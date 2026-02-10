"use client"

import Layout from "@/components/xen/main/layout"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <Layout>{children}</Layout>
}
