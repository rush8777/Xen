import React from "react"

interface IconProps {
  className?: string
}

const InstagramIcon: React.FC<IconProps> = ({ className }) => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <linearGradient id="igGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#F58529" />
        <stop offset="30%" stopColor="#FEDA77" />
        <stop offset="60%" stopColor="#DD2A7B" />
        <stop offset="100%" stopColor="#8134AF" />
      </linearGradient>
    </defs>
    <rect x="3" y="3" width="18" height="18" rx="5" fill="url(#igGradient)" />
    <circle cx="12" cy="12" r="4.2" fill="none" stroke="white" strokeWidth="1.8" />
    <circle cx="16.4" cy="7.6" r="0.9" fill="white" />
  </svg>
)

export default InstagramIcon


