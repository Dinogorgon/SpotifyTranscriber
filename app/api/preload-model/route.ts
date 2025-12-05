import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { join } from 'path'

const PYTHON_DIR = join(process.cwd(), 'python')

export async function GET() {
  try {
    // Pre-load the model in the background
    const python = spawn('python', [join(PYTHON_DIR, 'preload_model.py')], {
      cwd: PYTHON_DIR,
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: true, // Don't wait for completion
    })

    // Don't wait for the process to finish
    python.unref()

    return NextResponse.json({ 
      message: 'Model pre-loading started',
      status: 'success'
    })
  } catch (error: any) {
    console.error('Pre-load error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to start model pre-loading' },
      { status: 500 }
    )
  }
}

