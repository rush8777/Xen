"use client"

import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import Image from "next/image"
import { Bell, ChevronRight } from "lucide-react"
import Link from "next/link"
import { ThemeToggle } from "@/components/theme-toggle"
import { usePathname } from "next/navigation"

interface BreadcrumbItem {
  label: string
  href?: string
}

export default function TopNav() {
  const pathname = usePathname()
  
  const getPageLabel = (path: string): string => {
    const pathSegments = path.split('/').filter(Boolean)
    const lastSegment = pathSegments[pathSegments.length - 1]
    
    const pageLabels: Record<string, string> = {
      'dashboard': 'dashboard',
      'chat': 'chat',
      'connections': 'connections',
      'calender': 'calendar',
      'feedsense': 'feedsense',
      'library': 'library',
      'project': 'project',
      'streamline': 'streamline'
    }
    
    return pageLabels[lastSegment] || lastSegment || 'dashboard'
  }

  const currentPageLabel = getPageLabel(pathname)
  
  const breadcrumbs: BreadcrumbItem[] = [
    { label: "xen", href: "#" },
    { label: currentPageLabel, href: "#" },
  ]

  return (
    <nav className="px-3 sm:px-4 flex items-center justify-between bg-white dark:bg-[#0F0F12] h-12 min-h-12 border-b border-gray-200 dark:border-[#1F1F23]">
      <div className="font-medium text-xs hidden sm:flex items-center space-x-0.5 truncate max-w-[300px]">
        {breadcrumbs.map((item, index) => (
          <div key={item.label} className="flex items-center">
            {index > 0 && <ChevronRight className="h-3.5 w-3.5 text-gray-500 dark:text-gray-400 mx-0.5" />}
            {item.href ? (
              <Link
                href={item.href}
                className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-gray-900 dark:text-gray-100">{item.label}</span>
            )}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2 ml-auto sm:ml-0">
        <button
          type="button"
          className="p-1 hover:bg-gray-100 dark:hover:bg-[#1F1F23] rounded-full transition-colors"
        >
          <Bell className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-gray-600 dark:text-gray-300" />
        </button>

        <ThemeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger className="focus:outline-none">
            <Image
              src="https://ferf1mheo22r9ira.public.blob.vercel-storage.com/avatar-01-n0x8HFv8EUetf9z6ht0wScJKoTHqf8.png"
              alt="User avatar"
              width={24}
              height={24}
              className="rounded-full ring-2 ring-gray-200 dark:ring-[#2B2B30] sm:w-7 sm:h-7 cursor-pointer"
            />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            sideOffset={8}
            className="w-[280px] sm:w-80 bg-background border-border rounded-lg shadow-lg"
          >
            <div className="p-4">
              <div className="flex items-center space-x-3">
                <Image
                  src="https://ferf1mheo22r9ira.public.blob.vercel-storage.com/avatar-01-n0x8HFv8EUetf9z6ht0wScJKoTHqf8.png"
                  alt="User avatar"
                  width={40}
                  height={40}
                  className="rounded-full"
                />
                <div>
                  <p className="text-sm font-medium">User</p>
                  <p className="text-xs text-gray-500">user@example.com</p>
                </div>
              </div>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </nav>
  )
}
