import React from "react"

interface IconProps {
  className?: string
}

const TiktokIcon: React.FC<IconProps> = ({ className }) => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect x="3" y="3" width="18" height="18" rx="4" fill="#000000" />
    <path
      d="M15.5 8.2c.55.6 1.25 1.02 2.05 1.17v2.02c-.94-.06-1.82-.38-2.6-.9v3.85c0 2.3-1.77 3.68-3.7 3.68-1.98 0-3.7-1.45-3.7-3.6 0-2.16 1.75-3.6 3.7-3.6.23 0 .45.02.66.06v2.02a1.68 1.68 0 0 0-.66-.12c-.9 0-1.64.6-1.64 1.64 0 .96.76 1.62 1.64 1.62.88 0 1.6-.64 1.6-1.66V6.5h2.15c.08.66.35 1.3.8 1.7Z"
      fill="#ffffff"
    />
    <path
      d="M10.25 9.75c-1.95 0-3.7 1.44-3.7 3.6 0 2.15 1.72 3.6 3.7 3.6 1.93 0 3.7-1.38 3.7-3.68v-.27c-.17 1.5-1.5 2.5-3.04 2.5-1.6 0-2.94-1.1-2.94-2.87 0-1.72 1.3-2.82 2.94-2.82.23 0 .45.02.66.06v-2.02a4.3 4.3 0 0 0-.66-.06Z"
      fill="#FF0050"
      opacity="0.8"
    />
  </svg>
)

export default TiktokIcon


