import { buildFolderTree, flattenFolderOptions } from '../appUtils'
import type { ProtocolFolder } from '../types'

export function FolderSelect({ folders, value, onChange, label }: { folders: ProtocolFolder[]; value: number | null; onChange: (value: number | null) => void; label?: string }) {
  const options = buildFolderTree(folders).flatMap((folder) => flattenFolderOptions(folder))
  const select = (
    <select className="folder-select" value={value ?? ''} onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}>
      <option value="">未分类</option>
      {options.map((option) => <option value={option.id} key={option.id}>{`${'　'.repeat(option.depth)}${option.name}`}</option>)}
    </select>
  )

  if (!label) {
    return select
  }

  return (
    <label>
      {label}
      {select}
    </label>
  )
}
