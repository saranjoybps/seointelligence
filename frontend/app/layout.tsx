import type { Metadata } from 'next'
import { Inter, Space_Grotesk, Space_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const syne = Space_Grotesk({ subsets: ['latin'], variable: '--font-syne' })
const mono = Space_Mono({ subsets: ['latin'], weight: ['400', '700'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'SEO Intelligence Platform',
  description: 'AI-powered SEO and digital marketing analysis'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <body className={`${inter.variable} ${syne.variable} ${mono.variable} bg-bg text-text antialiased`}>
        {children}
      </body>
    </html>
  )
}
