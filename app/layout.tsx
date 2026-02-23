import { Inter } from "next/font/google"
import "./globals.css"
import "@/components/teach-canvas-kit-component/styles.css"
import { ThemeProvider } from "@/components/theme-provider"
import { ScrollbarVisibilityManager } from "@/components/scrollbar-visibility-manager"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "xen Dashboard",
  description: "A modern dashboard with theme switching",
    generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ScrollbarVisibilityManager />
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
