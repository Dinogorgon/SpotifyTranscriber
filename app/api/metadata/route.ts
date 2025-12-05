import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { join } from 'path'

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
    const result = await new Promise<any>((resolve, reject) => {
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
            const data = JSON.parse(stdout.trim())
            resolve(data)
          } catch (error) {
            reject(new Error(`Failed to parse metadata: ${stdout}`))
          }
        } else {
          reject(new Error(stderr || `Process exited with code ${code}`))
        }
      })

      python.on('error', (error) => {
        reject(error)
      })
    })

    return NextResponse.json(result)
  } catch (error: any) {
    console.error('Metadata error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to fetch metadata' },
      { status: 500 }
    )
  }
}

