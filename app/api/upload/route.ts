import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdtemp } from 'fs/promises'
import { join } from 'path'
import { tmpdir } from 'os'

export const maxDuration = 300 // 5 minutes for large file uploads
export const runtime = 'nodejs'

const MAX_FILE_SIZE = 1610612736 // 1.5 GB in bytes
const ALLOWED_TYPES = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'video/mp4', 'audio/x-m4a', 'audio/m4a']
const ALLOWED_EXTENSIONS = ['.mp3', '.mp4', '.m4a']

export async function POST(request: NextRequest) {
  let tempDir: string | null = null

  try {
    const formData = await request.formData()
    const file = formData.get('file') as File | null

    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      )
    }

    // Validate file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    const isValidType = ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTENSIONS.includes(fileExtension)
    
    if (!isValidType) {
      return NextResponse.json(
        { error: 'Invalid file type. Please upload an MP3, MP4, or M4A file.' },
        { status: 400 }
      )
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: `File size exceeds maximum of 1.5 GB. File size: ${(file.size / 1024 / 1024).toFixed(2)} MB` },
        { status: 400 }
      )
    }

    // Create temporary directory
    tempDir = await mkdtemp(join(tmpdir(), 'spotify-transcriber-upload-'))
    const filePath = join(tempDir, file.name)

    // Write file to disk
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filePath, buffer)

    return NextResponse.json({
      file_path: filePath,
      file_name: file.name,
      file_size: file.size,
    })
  } catch (error: any) {
    console.error('Upload error:', error)
    
    // Cleanup on error
    if (tempDir) {
      try {
        const { rm } = await import('fs/promises')
        await rm(tempDir, { recursive: true, force: true })
      } catch {
        // Ignore cleanup errors
      }
    }

    return NextResponse.json(
      { error: error.message || 'File upload failed' },
      { status: 500 }
    )
  }
}

