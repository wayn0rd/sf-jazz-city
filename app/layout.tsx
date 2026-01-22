import './globals.css'

export const metadata = {
  title: 'SF Jazz City',
  description: 'Where to go for live jazz in San Francisco',
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
