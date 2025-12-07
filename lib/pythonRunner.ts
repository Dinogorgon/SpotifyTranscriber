import { spawn } from 'child_process'
import { join } from 'path'

const PYTHON_DIR = join(process.cwd(), 'python')

export interface PythonResult {
  success: boolean
  data?: any
  error?: string
  stdout?: string
  stderr?: string
}

/**
 * Execute a Python script and return the result
 */
export async function runPythonScript(
  scriptName: string,
  args: string[] = [],
  inputData?: any
): Promise<PythonResult> {
  return new Promise((resolve) => {
    const scriptPath = join(PYTHON_DIR, scriptName)
    const pythonArgs = [scriptPath, ...args]
    
    // If inputData is provided, serialize it as JSON and pass via stdin
    const inputJson = inputData ? JSON.stringify(inputData) : undefined
    
    const python = spawn('python', pythonArgs, {
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
          // Try to parse JSON output
          const data = stdout.trim()
          let parsed: any = data
          
          // Check if output looks like JSON
          if (data.startsWith('{') || data.startsWith('[')) {
            parsed = JSON.parse(data)
          }
          
          resolve({
            success: true,
            data: parsed,
            stdout,
          })
        } catch (error) {
          // If not JSON, return as string
          resolve({
            success: true,
            data: stdout.trim(),
            stdout,
          })
        }
      } else {
        resolve({
          success: false,
          error: stderr || `Process exited with code ${code}`,
          stderr,
          stdout,
        })
      }
    })
    
    python.on('error', (error) => {
      resolve({
        success: false,
        error: error.message,
        stderr,
        stdout,
      })
    })
    
    // Write input data if provided
    if (inputJson && python.stdin) {
      python.stdin.write(inputJson)
      python.stdin.end()
    }
  })
}

/**
 * Execute Python module method (e.g., python -m module.method)
 */
export async function runPythonModule(
  moduleName: string,
  methodName: string,
  args: any[] = []
): Promise<PythonResult> {
  return new Promise((resolve) => {
    const pythonArgs = [
      '-c',
      `import sys; sys.path.insert(0, '${PYTHON_DIR.replace(/\\/g, '/')}'); from ${moduleName} import *; import json; result = ${methodName}(${args.map(a => JSON.stringify(a)).join(', ')}); print(json.dumps(result) if isinstance(result, (dict, list)) else result)`
    ]
    
    const python = spawn('python', pythonArgs, {
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
          const data = stdout.trim()
          let parsed: any = data
          
          if (data.startsWith('{') || data.startsWith('[')) {
            parsed = JSON.parse(data)
          }
          
          resolve({
            success: true,
            data: parsed,
            stdout,
          })
        } catch (error) {
          resolve({
            success: true,
            data: stdout.trim(),
            stdout,
          })
        }
      } else {
        resolve({
          success: false,
          error: stderr || `Process exited with code ${code}`,
          stderr,
          stdout,
        })
      }
    })
    
    python.on('error', (error) => {
      resolve({
        success: false,
        error: error.message,
        stderr,
        stdout,
      })
    })
  })
}

/**
 * Call Python class method via a wrapper script
 */
export async function callPythonClass(
  className: string,
  methodName: string,
  args: any[] = []
): Promise<PythonResult> {
  const wrapperScript = `
import sys
import json
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ${className.split('.')[0]} import ${className.split('.').pop() || className}

args = json.loads(sys.stdin.read())
instance = ${className.split('.').pop() || className}()
result = getattr(instance, '${methodName}')(*args)
print(json.dumps(result) if isinstance(result, (dict, list)) else result)
`
  
  return new Promise((resolve) => {
    const python = spawn('python', ['-c', wrapperScript], {
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
          const data = stdout.trim()
          let parsed: any = data
          
          if (data.startsWith('{') || data.startsWith('[')) {
            parsed = JSON.parse(data)
          }
          
          resolve({
            success: true,
            data: parsed,
            stdout,
          })
        } catch (error) {
          resolve({
            success: true,
            data: stdout.trim(),
            stdout,
          })
        }
      } else {
        resolve({
          success: false,
          error: stderr || `Process exited with code ${code}`,
          stderr,
          stdout,
        })
      }
    })
    
    python.on('error', (error) => {
      resolve({
        success: false,
        error: error.message,
        stderr,
        stdout,
      })
    })
    
    if (python.stdin) {
      python.stdin.write(JSON.stringify(args))
      python.stdin.end()
    }
  })
}

