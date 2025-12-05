import { NextRequest } from 'next/server'
import { spawn } from 'child_process'
import { join, dirname } from 'path'
import { rm, mkdtemp, access, constants } from 'fs/promises'
import { tmpdir } from 'os'
import { TranscribeRequest } from '@/lib/types'

const PYTHON_DIR = join(process.cwd(), 'python')

export async function POST(request: NextRequest) {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      let tempDir: string | null = null

      const sendProgress = (message: string, percent: number) => {
        const data = JSON.stringify({ type: 'progress', message, percent }) + '\n'
        const sseData = `data: ${data}\n\n`
        controller.enqueue(encoder.encode(sseData))
      }

      const sendError = (error: string) => {
        const data = JSON.stringify({ type: 'error', error }) + '\n'
        controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        controller.close()
      }

      try {
        const body: TranscribeRequest = await request.json()
        const { spotify_url, file_path, backend, model_size } = body

        if (!spotify_url && !file_path) {
          sendError('Either spotify_url or file_path is required')
          return
        }

        let audioPath: string

        if (file_path) {
          // Verify file exists
          try {
            await access(file_path, constants.F_OK)
          } catch {
            sendError(`Uploaded file not found: ${file_path}`)
            return
          }

          audioPath = file_path
          const pathParts = file_path.split(/[\\/]/)
          const tempDirIndex = pathParts.findIndex(part => part.startsWith('spotify-transcriber-upload-'))
          if (tempDirIndex !== -1) {
            tempDir = join(...pathParts.slice(0, tempDirIndex + 1))
          } else {
            tempDir = dirname(file_path)
          }
        } else if (spotify_url) {
          // Step 1: Get metadata
          sendProgress('Fetching Spotify metadata...', 10)
          const metadataResult = await new Promise<any>((resolve, reject) => {
            const python = spawn('python', [join(PYTHON_DIR, 'get_metadata.py'), spotify_url], {
              cwd: PYTHON_DIR,
              stdio: ['pipe', 'pipe', 'pipe'],
            })

            let stdout = ''
            let stderr = ''

            python.stdout.on('data', (data) => {
              stdout += data.toString()
            })

            python.stderr.on('data', (data) => {
              stderr += data.toString()
            })

            python.on('close', (code) => {
              if (code === 0) {
                try {
                  resolve(JSON.parse(stdout.trim()))
                } catch {
                  reject(new Error('Failed to parse metadata'))
                }
              } else {
                reject(new Error(stderr || 'Failed to get metadata'))
              }
            })

            python.on('error', reject)
          })

          // Step 2: Download audio with progress and timeout
          sendProgress('Downloading audio...', 20)
          tempDir = await mkdtemp(join(tmpdir(), 'spotify-transcriber-'))
          audioPath = join(tempDir, 'audio.mp3')

          await new Promise<void>((resolve, reject) => {
            const python = spawn(
              'python',
              ['-u', join(PYTHON_DIR, 'download_audio.py'), spotify_url, audioPath], // -u flag for unbuffered output
              { cwd: PYTHON_DIR, stdio: ['pipe', 'pipe', 'pipe'] }
            )

            let stderr = ''
            let downloadTimeout: NodeJS.Timeout | null = null
            let lastProgressUpdate = 0

            // Set timeout (5 minutes for download - should be fast with RSS)
            downloadTimeout = setTimeout(() => {
              python.kill() // Use kill() instead of kill('SIGTERM') for Windows compatibility
              reject(new Error('Download timeout: The download took too long (5 minutes). The RSS feed may be slow or the audio file is very large.'))
            }, 5 * 60 * 1000)
            
            // Also set a progress watchdog - if no progress for 2 minutes, timeout
            let lastProgressTime = Date.now()
            const progressWatchdog = setInterval(() => {
              const timeSinceLastProgress = Date.now() - lastProgressTime
              if (timeSinceLastProgress > 2 * 60 * 1000) { // 2 minutes without progress
                if (downloadTimeout) clearTimeout(downloadTimeout)
                clearInterval(progressWatchdog)
                python.kill()
                reject(new Error('Download stalled: No progress detected for 2 minutes. The download may have hung.'))
              }
            }, 10000) // Check every 10 seconds

            python.stderr.on('data', (data) => {
              const text = data.toString()
              const lines = text.split('\n')
              
              for (const line of lines) {
                const trimmed = line.trim()
                if (!trimmed) continue
                
                try {
                  const parsed = JSON.parse(trimmed)
                  
                  if (parsed.progress !== undefined && parsed.stage === 'download') {
                    lastProgressTime = Date.now() // Update progress watchdog
                    
                    // Progress is 0-1, map to 20-30% (download step)
                    const downloadPercent = 20 + (parsed.progress * 10)
                    const progressPercent = Math.round(parsed.progress * 100)
                    
                    // Always update progress (don't check for duplicates - let UI handle it)
                    const message = parsed.message 
                      ? `${parsed.message} ${progressPercent}%`
                      : `Downloading audio... ${progressPercent}%`
                    
                    sendProgress(message, downloadPercent)
                    lastProgressUpdate = progressPercent
                  } else if (parsed.error) {
                    if (downloadTimeout) clearTimeout(downloadTimeout)
                    reject(new Error(parsed.error))
                  }
                } catch (e) {
                  // Not JSON, might be debug output - ignore FFmpeg download messages and other noise
                  if (!trimmed.includes('Downloading FFmpeg') && 
                      !trimmed.includes('Extracting FFmpeg') &&
                      !trimmed.includes('Added') &&
                      !trimmed.includes('pkg_resources') &&
                      !trimmed.includes('Using cached model')) {
                    // Only add to stderr if it's not a known debug message
                    if (trimmed.length > 0 && !trimmed.startsWith('DEBUG:')) {
                      stderr += trimmed + '\n'
                    }
                  }
                }
              }
            })

            python.on('close', (code) => {
              if (downloadTimeout) clearTimeout(downloadTimeout)
              if (progressWatchdog) clearInterval(progressWatchdog)
              if (code === 0) {
                // Send final download progress
                sendProgress('Download complete', 30)
                resolve()
              } else {
                // Try to parse error from stderr
                try {
                  const errorLines = stderr.trim().split('\n')
                  const errorJson = errorLines.find(line => {
                    try {
                      const parsed = JSON.parse(line.trim())
                      return parsed.error
                    } catch {
                      return false
                    }
                  })
                  if (errorJson) {
                    const parsed = JSON.parse(errorJson.trim())
                    reject(new Error(parsed.error || 'Failed to download audio'))
                  } else {
                    reject(new Error(stderr || 'Failed to download audio'))
                  }
                } catch {
                  reject(new Error(stderr || 'Failed to download audio'))
                }
              }
            })

            python.on('error', (error) => {
              if (downloadTimeout) clearTimeout(downloadTimeout)
              if (progressWatchdog) clearInterval(progressWatchdog)
              reject(new Error(`Failed to start download process: ${error.message}`))
            })
          })
        }

        // Step 3: Transcribe with real-time progress and timeout
        sendProgress('Starting transcription...', 30)
        const projectRoot = process.cwd()
        const env = { 
          ...process.env,
          PYTHONWARNINGS: 'ignore::DeprecationWarning:pkg_resources'
        }
        
        const transcriptionResult = await new Promise<any>((resolve, reject) => {
          const python = spawn(
            'python',
            ['-u', join(PYTHON_DIR, 'transcribe_audio.py'), audioPath, backend, model_size], // -u flag for unbuffered output
            { cwd: projectRoot, stdio: ['pipe', 'pipe', 'pipe'], env }
          )

          let stdout = ''
          let stderr = ''
          let lastProgressTime = Date.now()
          let transcriptionTimeout: NodeJS.Timeout | null = null
          let progressCheckInterval: NodeJS.Timeout | null = null

          // Set timeout (30 minutes for transcription)
          transcriptionTimeout = setTimeout(() => {
            python.kill('SIGTERM')
            reject(new Error('Transcription timeout: The transcription took too long (30 minutes). The audio file may be very long or there was an issue with the model.'))
          }, 30 * 60 * 1000)

          // Check for progress every 30 seconds - if no progress for 2 minutes, timeout
          progressCheckInterval = setInterval(() => {
            const timeSinceLastProgress = Date.now() - lastProgressTime
            if (timeSinceLastProgress > 2 * 60 * 1000) { // 2 minutes without progress
              if (transcriptionTimeout) clearTimeout(transcriptionTimeout)
              clearInterval(progressCheckInterval!)
              python.kill('SIGTERM')
              reject(new Error('Transcription stalled: No progress detected for 2 minutes. The process may have hung.'))
            }
          }, 30000) // Check every 30 seconds

          // Parse stderr line by line for progress updates
          python.stderr.on('data', (data) => {
            const lines = data.toString().split('\n')
            for (const line of lines) {
              if (!line.trim()) continue
              
              try {
                const parsed = JSON.parse(line.trim())
                if (parsed.progress !== undefined) {
                  lastProgressTime = Date.now() // Update last progress time
                  // Progress is 0-1, map to 30-95% (transcription step)
                  const transcriptionPercent = 30 + (parsed.progress * 65)
                  sendProgress(
                    `Transcribing with ${backend} Whisper (${model_size})... ${Math.round(parsed.progress * 100)}%`,
                    transcriptionPercent
                  )
                } else if (parsed.error) {
                  if (transcriptionTimeout) clearTimeout(transcriptionTimeout)
                  if (progressCheckInterval) clearInterval(progressCheckInterval)
                  reject(new Error(parsed.error))
                }
              } catch {
                // Not JSON, ignore (might be debug output)
                stderr += line
              }
            }
          })

          python.stdout.on('data', (data) => {
            stdout += data.toString()
          })

          python.on('close', (code) => {
            if (transcriptionTimeout) clearTimeout(transcriptionTimeout)
            if (progressCheckInterval) clearInterval(progressCheckInterval)
            
            if (code === 0) {
              try {
                const lines = stdout.trim().split('\n')
                const jsonLines = lines.filter(line => 
                  line.trim().startsWith('{') || line.trim().startsWith('[')
                )
                const jsonOutput = jsonLines.length > 0 ? jsonLines.join('\n') : stdout.trim()
                resolve(JSON.parse(jsonOutput))
              } catch (parseError) {
                reject(new Error(`Failed to parse transcription: ${parseError instanceof Error ? parseError.message : 'Invalid JSON'}`))
              }
            } else {
              const errorLines = stderr.trim().split('\n').filter(line => {
                const trimmed = line.trim()
                return !trimmed.startsWith('DEBUG:') && 
                       !trimmed.startsWith('Using cached model:') && 
                       !trimmed.startsWith('Loading') && 
                       trimmed.length > 0 &&
                       !trimmed.includes('pkg_resources') // Filter out deprecation warnings
              })
              const errorMessage = errorLines.length > 0 
                ? errorLines.join('\n') 
                : stderr || `Process exited with code ${code}`
              reject(new Error(errorMessage))
            }
          })

          python.on('error', (error) => {
            if (transcriptionTimeout) clearTimeout(transcriptionTimeout)
            if (progressCheckInterval) clearInterval(progressCheckInterval)
            reject(new Error(`Failed to start transcription process: ${error.message}`))
          })
        })

        // Step 4: Summarize
        sendProgress('Generating AI summary...', 95)
        const summaryResult = await new Promise<string>((resolve, reject) => {
          const python = spawn('python', [join(PYTHON_DIR, 'summarize_transcript.py')], {
            cwd: PYTHON_DIR,
            stdio: ['pipe', 'pipe', 'pipe'],
          })

          let stdout = ''
          let stderr = ''

          python.stdout.on('data', (data) => {
            stdout += data.toString()
          })

          python.stderr.on('data', (data) => {
            stderr += data.toString()
          })

          python.on('close', (code) => {
            if (code === 0) {
              resolve(stdout.trim())
            } else {
              reject(new Error(stderr || 'Failed to summarize'))
            }
          })

          python.on('error', reject)

          if (python.stdin) {
            python.stdin.write(JSON.stringify(transcriptionResult))
            python.stdin.end()
          }
        })

        // Send final result
        const finalResult = {
          ...transcriptionResult,
          summary: summaryResult,
        }
        sendProgress('Complete!', 100)
        const data = JSON.stringify({ type: 'result', data: finalResult }) + '\n'
        controller.enqueue(encoder.encode(`data: ${data}\n\n`))
        controller.close()

      } catch (error: any) {
        console.error('Transcription error:', error)
        sendError(error.message || 'Transcription failed')
      } finally {
        // Cleanup: Remove entire temporary directory
        if (tempDir) {
          try {
            await rm(tempDir, { recursive: true, force: true })
          } catch (error) {
            console.error('Failed to cleanup temp directory:', error)
          }
        }
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}

export const maxDuration = 600

