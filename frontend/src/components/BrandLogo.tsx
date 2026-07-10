type BrandLogoVariant = 'mark' | 'lockup'

const assetBase = import.meta.env.BASE_URL ?? '/'

const brandLogoSources: Record<BrandLogoVariant, string> = {
  mark: `${assetBase}brand/prototree-logo-256x256.png`,
  lockup: `${assetBase}brand/prototree-text-horiz-800x450.png`,
}

export function BrandLogo({ variant = 'lockup', className }: { variant?: BrandLogoVariant; className?: string }) {
  return <img className={className} src={brandLogoSources[variant]} alt="ProtoTree" onError={(event) => { event.currentTarget.replaceWith(document.createTextNode('ProtoTree')) }} />
}
