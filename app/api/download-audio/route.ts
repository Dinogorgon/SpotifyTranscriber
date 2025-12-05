import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { join } from 'path'
import { readFile, unlink, mkdtemp } from 'fs/promises'
import { tmpdir } from 'os'

const PYTHON_DIR = join(process.cwd(), 'python')

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const spotifyUrl = searchParams.get('spotify_url')

  if (!spotifyUrl) {
    return NextResponse.json(
      { error: 'spotify_url parameter is required' },
      { status: 400 }
    )
  }

  try {
    // Get metadata first to get title for filename
    const metadataResult = await new Promise<any>((resolve, reject) => {
      const python = spawn('python', [join(PYTHON_DIR, 'get_metadata.py'), spotifyUrl], {
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

    // Download audio
    const tempDir = await mkdtemp(join(tmpdir(), 'spotify-transcriber-'))
    const audioPath = join(tempDir, 'audio.mp3')

    await new Promise<void>((resolve, reject) => {
      const python = spawn(
        'python',
        [join(PYTHON_DIR, 'download_audio.py'), spotifyUrl, audioPath],
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

    // Read file and return
    const audioBuffer = await readFile(audioPath)
    const title = metadataResult.title || 'episode'
    const filename = `${title.replace(/[^a-z0-9]/gi, '_')}.mp3`

    // Cleanup
    try {
      await unlink(audioPath)
    } catch {
      // Ignore cleanup errors
    }

    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    })
  } catch (error: any) {
    console.error('Download error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to download audio' },
      { status: 500 }
    )
  }
}

