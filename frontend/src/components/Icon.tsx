import type { CSSProperties } from 'react'

/* ====================================================================
   Icon — Lightweight inline SVG icon set for navigation and UI
   Replaces emoji icons with consistent, crisp SVG icons
   ==================================================================== */

type IconName =
  | 'home' | 'library' | 'flask' | 'reagent' | 'edit' | 'upload' | 'fork'
  | 'dna' | 'chart' | 'robot' | 'sparkles' | 'user' | 'folder'
  | 'star' | 'star-filled' | 'logout' | 'arrow-left' | 'trash' | 'menu' | 'close'

interface IconProps {
  name: IconName
  size?: number
  className?: string
  style?: CSSProperties
}

const icons: Record<IconName, string> = {
  home: '<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  library: '<path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  flask: '<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 2h8l-1 7v3.5a2.5 2.5 0 01-6 0V9L8 2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  reagent: '<path d="M9 2h6M10 2v4.2l-3.4 4.9A5.4 5.4 0 0011 20h2a5.4 5.4 0 004.4-8.9L14 6.2V2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.3 14h7.4M9 17h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M10.4 10.5h3.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  edit: '<path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  upload: '<path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  fork: '<path d="M7 4v5a3 3 0 003 3h4a3 3 0 013 3v5M17 4v3a5 5 0 01-5 5M7 20v-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="7" cy="4" r="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17" cy="4" r="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="7" cy="20" r="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17" cy="20" r="2" fill="none" stroke="currentColor" stroke-width="1.8"/>',
  dna: '<path d="M9 3v0m6 0v0M9 3c0 3.314 2.686 6 6 6M9 3c0 3.314-2.686 6-6 6m12 0v0M3 9v0m18 0v0M3 9c0 3.314 2.686 6 6 6m12-6c0 3.314-2.686 6-6 6M9 15c0 3.314 2.686 6 6 6M9 15c0 3.314-2.686 6-6 6m12-6c0 3.314 2.686 6 6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  chart: '<path d="M4 19V5m0 14h16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M7 15l3.2-3.2 2.5 2.5L18 8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 8h2v2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  robot: '<path d="M12 18v-6m0 0V6a2 2 0 112 0v6m-2 0a2 2 0 10-2 0m7-3h1a2 2 0 012 2v2a2 2 0 01-2 2h-1m-7-6H5a2 2 0 00-2 2v2a2 2 0 002 2h1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="10" r="1" fill="currentColor"/><circle cx="15" cy="10" r="1" fill="currentColor"/>',
  sparkles: '<path d="M12 3l1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3zM5 15l.8 2.2L8 18l-2.2.8L5 21l-.8-2.2L2 18l2.2-.8L5 15zM18 13l1 2.8 3 1.2-3 1.2-1 2.8-1-2.8-3-1.2 3-1.2 1-2.8z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
  user: '<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  folder: '<path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  star: '<path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  'star-filled': '<path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" fill="currentColor" stroke="currentColor" stroke-width="1.2"/>',
  logout: '<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  'arrow-left': '<path d="M19 12H5m0 0l7 7m-7-7l7-7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  trash: '<path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
  close: '<path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
}

export function Icon({ name, size = 18, className, style }: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style }}
      dangerouslySetInnerHTML={{ __html: icons[name] }}
    />
  )
}
