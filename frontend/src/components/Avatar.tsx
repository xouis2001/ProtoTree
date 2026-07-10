import { useEffect, useMemo, useState } from 'react'
import '../styles/avatar.css'

type AvatarSize = 'tiny' | 'small' | 'medium' | 'large'

export type AvatarConfig = {
  bg?: string
  sel?: Record<string, string>
  colors?: Record<string, string>
} | null

type AvatarProps = {
  value?: string | null
  config?: AvatarConfig
  size?: AvatarSize
  label?: string
}

const ORDER = ['face', 'beard', 'mouth', 'nose', 'eyes', 'eyebrows', 'glasses', 'hair', 'accessories', 'details']
const OPTIONAL = new Set(['glasses', 'accessories', 'details', 'beard'])
const HAIR_COLORS = ['#000000', '#5b4636', '#a86b38', '#d89a56', '#2c3e50']
const BGS = ['#ffffff', '#f5f0e8', '#e8f0f5', '#f5e8ee']
const COUNTS: Record<string, number> = { face: 13, beard: 13, mouth: 13, nose: 13, eyes: 13, eyebrows: 13, glasses: 13, hair: 22, accessories: 13, details: 13 }

function normaliseConfig(config?: AvatarConfig, value?: string | null): AvatarConfig {
  if (config && typeof config === 'object' && 'sel' in config) return config
  if (!value) return null
  try {
    const parsed = JSON.parse(value)
    if (parsed && typeof parsed === 'object' && ('sel' in parsed || 'colors' in parsed || 'bg' in parsed)) return parsed as AvatarConfig
  } catch {
    // Legacy avatar string; renderer will create a deterministic random face from seed.
  }
  return null
}

function hashSeed(seed: string) {
  let h = 2166136261
  for (let i = 0; i < seed.length; i += 1) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function makeRng(seed: string) {
  let s = hashSeed(seed) || 1
  return () => {
    s ^= s << 13
    s ^= s >>> 17
    s ^= s << 5
    return ((s >>> 0) / 4294967296)
  }
}

function randomConfig(seed: string): NonNullable<AvatarConfig> {
  const rnd = makeRng(seed || 'ProtoTree user')
  const sel: Record<string, string> = {}
  const colors: Record<string, string> = {}
  for (const cat of ORDER) {
    const count = COUNTS[cat] || 13
    if (OPTIONAL.has(cat) && rnd() < 0.4) sel[cat] = `${cat}-0`
    else sel[cat] = `${cat}-${1 + Math.floor(rnd() * (count - 1))}`
    colors[cat] = '#000000'
  }
  colors.hair = HAIR_COLORS[Math.floor(rnd() * HAIR_COLORS.length)] || '#000000'
  return { bg: BGS[Math.floor(rnd() * BGS.length)] || '#ffffff', sel, colors }
}

function avatarItemIndex(name?: string) {
  const m = /(\d+)$/.exec(name || '')
  return m ? parseInt(m[1], 10) : -1
}

function avatarInnerSvg(svgText: string) {
  const m = /<svg[^>]*>([\s\S]*?)<\/svg>/i.exec(svgText || '')
  return m ? m[1] : (svgText || '')
}

function avatarColorize(svgText: string, color: string) {
  let s = (svgText || '').replace(/(fill|stroke)="(#[0-9a-fA-F]{3,8}|black|white|currentColor)"/g,
    (_match, attr) => `${attr}="${color}"`)
  if (!/(fill|stroke)="#/.test(s)) s = s.replace(/<path /g, `<path fill="${color}" `)
  return s
}

async function buildAvatarSvg(cfg: NonNullable<AvatarConfig>) {
  let inner = ''
  for (const cat of ORDER) {
    const name = cfg.sel?.[cat]
    const idx = avatarItemIndex(name)
    if (!name || idx <= 0) continue
    const res = await fetch(`/avatar-assets/preview/${cat}/${idx}.svg`, { cache: 'force-cache' })
    if (!res.ok) continue
    const raw = await res.text()
    const body = avatarInnerSvg(raw)
    // Accessories/items are imported as finished multicolor assets; keep their original fill/stroke colors.
    // Other facial parts still follow the user's configured color.
    const rendered = cat === 'accessories' ? body : avatarColorize(body, cfg.colors?.[cat] || '#000000')
    const faceFill = cat === 'face' ? ' fill="#ffffff"' : ''
    inner += `<g${faceFill}>${rendered}</g>`
  }
  if (!inner) return ''
  const bg = cfg.bg || '#ffffff'
  return `<svg viewBox="0 0 1080 1080" xmlns="http://www.w3.org/2000/svg" aria-label="用户头像" style="width:100%;height:100%;display:block;border-radius:50%;overflow:hidden;background:${bg}"><defs><clipPath id="avatarCircleClip"><circle cx="540" cy="540" r="540"></circle></clipPath></defs><rect width="1080" height="1080" rx="540" ry="540" fill="${bg}"></rect><g clip-path="url(#avatarCircleClip)">${inner}</g></svg>`
}

function fallbackInitial(label?: string, value?: string | null) {
  const s = (label || value || '?').trim()
  return s.charAt(0).toUpperCase()
}

export function Avatar({ value, config, size = 'medium', label }: AvatarProps) {
  const faceConfig = useMemo(() => normaliseConfig(config, value) || randomConfig(label || value || 'ProtoTree user'), [config, value, label])
  const [svg, setSvg] = useState('')

  useEffect(() => {
    let alive = true
    setSvg('')
    buildAvatarSvg(faceConfig).then((html) => {
      if (alive) setSvg(html)
    }).catch(() => {
      if (alive) setSvg('')
    })
    return () => { alive = false }
  }, [faceConfig])

  return (
    <span className={`avatar avatar-${size} avatar-face`} aria-label={label} style={{ ['--avatar-bg' as string]: faceConfig.bg || '#ffffff' }}>
      {svg ? <span className="avatar-inline-svg" dangerouslySetInnerHTML={{ __html: svg }} /> : fallbackInitial(label, value)}
    </span>
  )
}

export function AvatarBuilder(props: { value?: string; usedColors?: string[]; onChange?: (avatar: string) => void }) {
  void props
  return <div className="avatar-builder-disabled">头像请在 lulab.top/avatar-builder.html 中统一设置。</div>
}
