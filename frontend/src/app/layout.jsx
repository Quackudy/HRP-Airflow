import "@/app/globals.css"

export const metadata = {
  title: "HRP - Portfolio Management",
  description: "Professional portfolio management and analytics platform",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
