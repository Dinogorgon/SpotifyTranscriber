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
            // Filter out debug messages that might be in stdout
            const lines = stdout.trim().split('\n')
            const jsonLines = lines.filter(line => 
              line.trim().startsWith('{') || line.trim().startsWith('[')
            )
            const jsonOutput = jsonLines.length > 0 ? jsonLines.join('\n') : stdout.trim()
            const data = JSON.parse(jsonOutput)
            resolve(data)
          } catch (error) {
            console.error('Failed to parse metadata JSON:', stdout)
            reject(new Error(`Failed to parse metadata: ${error instanceof Error ? error.message : 'Invalid JSON'}`))
          }
        } else {
          // Filter out debug messages from stderr
          const errorLines = stderr.trim().split('\n').filter(line => 
            !line.startsWith('DEBUG:') && line.trim().length > 0
          )
          const errorMessage = errorLines.length > 0 
            ? errorLines.join('\n') 
            : stderr || `Process exited with code ${code}`
          reject(new Error(errorMessage))
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

