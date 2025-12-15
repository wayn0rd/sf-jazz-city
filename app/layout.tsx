import './globals.css'

export const metadata = {
  title: 'SF Jazz City',
  description: 'Your guide to live jazz in San Francisco',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}