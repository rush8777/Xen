import React from "react"

interface IconProps {
  className?: string
}

const YoutubeIcon: React.FC<IconProps> = ({ className }) => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect x="2" y="6" width="20" height="12" rx="4" fill="#FF0000" />
    <path d="M11 15.25V8.75L16 12L11 15.25Z" fill="white" />
  </svg>
)

export default YoutubeIcon


