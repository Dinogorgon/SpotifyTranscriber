import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { join, dirname } from 'path'
import { rm, mkdtemp, access, constants } from 'fs/promises'
import { tmpdir } from 'os'
import { TranscribeRequest } from '@/lib/types'

const PYTHON_DIR = join(process.cwd(), 'python')

export async function POST(request: NextRequest) {
  let tempDir: string | null = null

  try {
    const body: TranscribeRequest = await request.json()
    const { spotify_url, file_path, backend, model_size } = body

    if (!spotify_url && !file_path) {
      return NextResponse.json(
        { error: 'Either spotify_url or file_path is required' },
        { status: 400 }
      )
    }

    let audioPath: string

    if (file_path) {
      // Verify file exists
      try {
        await access(file_path, constants.F_OK)
      } catch {
        return NextResponse.json(
          { error: `Uploaded file not found: ${file_path}` },
          { status: 404 }
        )
      }

      // Use uploaded file directly
      audioPath = file_path
      // Extract temp directory from file path for cleanup
      // The file_path should be in a temp directory like: /tmp/spotify-transcriber-upload-xxx/filename.mp3
      // Extract the directory containing the file
      const pathParts = file_path.split(/[\\/]/)
      const tempDirIndex = pathParts.findIndex(part => part.startsWith('spotify-transcriber-upload-'))
      if (tempDirIndex !== -1) {
        // Reconstruct the temp directory path
        tempDir = join(...pathParts.slice(0, tempDirIndex + 1))
      } else {
        // Fallback: use directory name of the file
        tempDir = dirname(file_path)
      }
    } else if (spotify_url) {
      // Step 1: Get metadata
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

      // Step 2: Download audio
      tempDir = await mkdtemp(join(tmpdir(), 'spotify-transcriber-'))
      audioPath = join(tempDir, 'audio.mp3')

      await new Promise<void>((resolve, reject) => {
        const python = spawn(
          'python',
          [join(PYTHON_DIR, 'download_audio.py'), spotify_url, audioPath],
          { cwd: PYTHON_DIR, stdio: ['pipe', 'pipe', 'pipe'] }
        )

        let stderr = ''

        python.stderr.on('data', (data) => {
          stderr += data.toString()
        })

        python.on('close', (code) => {
          if (code === 0) {
            resolve()
          } else {
            reject(new Error(stderr || 'Failed to download audio'))
          }
        })

        python.on('error', reject)
      })
    } else {
      return NextResponse.json(
        { error: 'Either spotify_url or file_path is required' },
        { status: 400 }
      )
    }

    // Step 3: Transcribe
    const transcriptionResult = await new Promise<any>((resolve, reject) => {
      // Set working directory to project root so bin/ffmpeg.exe can be found
      const projectRoot = process.cwd()
      // Suppress pkg_resources deprecation warnings
      const env = { 
        ...process.env,
        PYTHONWARNINGS: 'ignore::DeprecationWarning:pkg_resources'
      }
      const python = spawn(
        'python',
        [join(PYTHON_DIR, 'transcribe_audio.py'), audioPath, backend, model_size],
        { cwd: projectRoot, stdio: ['pipe', 'pipe', 'pipe'], env }
      )

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
            // Filter out debug messages that might be in stdout
            const lines = stdout.trim().split('\n')
            const jsonLines = lines.filter(line => 
              line.trim().startsWith('{') || line.trim().startsWith('[')
            )
            const jsonOutput = jsonLines.length > 0 ? jsonLines.join('\n') : stdout.trim()
            resolve(JSON.parse(jsonOutput))
          } catch (parseError) {
            console.error('Failed to parse transcription JSON:', stdout)
            reject(new Error(`Failed to parse transcription: ${parseError instanceof Error ? parseError.message : 'Invalid JSON'}`))
          }
        } else {
          // Filter out debug messages from stderr
          const errorLines = stderr.trim().split('\n').filter(line => 
            !line.startsWith('DEBUG:') && !line.startsWith('Using cached model:') && !line.startsWith('Loading') && line.trim().length > 0
          )
          const errorMessage = errorLines.length > 0 
            ? errorLines.join('\n') 
            : stderr || `Process exited with code ${code}`
          reject(new Error(errorMessage))
        }
      })

      python.on('error', (error) => {
        reject(new Error(`Failed to start transcription process: ${error.message}`))
      })
    })

    // Step 4: Summarize
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

    return NextResponse.json({
      ...transcriptionResult,
      summary: summaryResult,
    })
  } catch (error: any) {
    console.error('Transcription error:', error)
    return NextResponse.json(
      { error: error.message || 'Transcription failed' },
      { status: 500 }
    )
  } finally {
    // Cleanup: Remove entire temporary directory
    if (tempDir) {
      try {
        await rm(tempDir, { recursive: true, force: true })
      } catch (error) {
        // Ignore cleanup errors but log them
        console.error('Failed to cleanup temp directory:', error)
      }
    }
  }
}

