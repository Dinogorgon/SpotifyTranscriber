import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Spotify Transcriber',
  description: 'Transcribe Spotify podcast episodes using Whisper AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

