import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { join } from 'path'
import { rm, mkdtemp } from 'fs/promises'
import { tmpdir } from 'os'
import { TranscribeRequest } from '@/lib/types'

const PYTHON_DIR = join(process.cwd(), 'python')

export async function POST(request: NextRequest) {
  let tempDir: string | null = null

  try {
    const body: TranscribeRequest = await request.json()
    const { spotify_url, backend, model_size } = body

    if (!spotify_url) {
      return NextResponse.json(
        { error: 'spotify_url is required' },
        { status: 400 }
      )
    }

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
    const audioPath = join(tempDir, 'audio.mp3')

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

    // Step 3: Transcribe
    const transcriptionResult = await new Promise<any>((resolve, reject) => {
      const python = spawn(
        'python',
        [join(PYTHON_DIR, 'transcribe_audio.py'), audioPath, backend, model_size],
        { cwd: PYTHON_DIR, stdio: ['pipe', 'pipe', 'pipe'] }
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
            resolve(JSON.parse(stdout.trim()))
          } catch {
            reject(new Error('Failed to parse transcription'))
          }
        } else {
          reject(new Error(stderr || 'Failed to transcribe'))
        }
      })

      python.on('error', reject)
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

