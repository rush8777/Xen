import React from "react"

interface IconProps {
  className?: string
}

const FacebookIcon: React.FC<IconProps> = ({ className }) => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="11" fill="#1877F2" />
    <path
      d="M13.5 8.25H15V6h-1.5C10.91 6 9.75 7.77 9.75 10.2V11.5H8v2.25h1.75V18h2.25v-4.25h1.75L14.5 11.5h-2.5v-1.3c0-.9.3-1.95 1.5-1.95Z"
      fill="white"
    />
  </svg>
)

export default FacebookIcon


