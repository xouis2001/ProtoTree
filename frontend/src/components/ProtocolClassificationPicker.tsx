import { useMemo, useState } from 'react'
import type { ProtocolCategory, ProtocolClassificationValue, ProtocolTag, ProtocolTagGroup } from '../types'

type ProtocolClassificationPickerProps = {
  taxonomy: ProtocolCategory[]
  value: ProtocolClassificationValue
  onChange: (value: ProtocolClassificationValue) => void
  onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>
  onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null>
  disabled?: boolean
}

function dedupeTags(tags: ProtocolTag[]) {
  const seen = new Set<string>()
  return tags.filter((tag) => {
    const key = `${tag.tag_group_id}-${tag.id}`
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

export function ProtocolClassificationPicker({ taxonomy, value, onChange, onCreateTagGroup, onCreateTag, disabled = false }: ProtocolClassificationPickerProps) {
  const [newGroupName, setNewGroupName] = useState('')
  const [newTagName, setNewTagName] = useState('')
  const [targetGroupId, setTargetGroupId] = useState<number | ''>('')
  const selectedCategory = taxonomy.find((category) => category.name === value.experiment_category) ?? null
  const selectedGroups = useMemo(() => selectedCategory?.tag_groups.filter((group) => value.tag_groups.includes(group.name)) ?? [], [selectedCategory, value.tag_groups])
  const visibleGroups = selectedCategory?.tag_groups ?? []
  const allTags = visibleGroups.flatMap((group) => group.tags)
  const selectedTagNames = new Set(value.tags)
  const visibleTags = selectedGroups.length ? dedupeTags([...selectedGroups.flatMap((group) => group.tags), ...allTags.filter((tag) => selectedTagNames.has(tag.name))]) : allTags

  function setCategory(category: ProtocolCategory) {
    onChange({ experiment_category: category.name, tag_groups: [], tags: [] })
    setTargetGroupId('')
  }

  function toggleGroup(group: ProtocolTagGroup) {
    const nextGroups = value.tag_groups.includes(group.name) ? value.tag_groups.filter((item) => item !== group.name) : [...value.tag_groups, group.name]
    onChange({ ...value, tag_groups: nextGroups })
  }

  function toggleTag(tag: ProtocolTag) {
    const nextTags = value.tags.includes(tag.name) ? value.tags.filter((item) => item !== tag.name) : [...value.tags, tag.name]
    const group = visibleGroups.find((item) => item.id === tag.tag_group_id)
    const nextGroups = group && !value.tag_groups.includes(group.name) ? [...value.tag_groups, group.name] : value.tag_groups
    onChange({ ...value, tag_groups: nextGroups, tags: nextTags })
  }

  async function submitGroup() {
    if (!selectedCategory || !newGroupName.trim()) {
      return
    }
    const group = await onCreateTagGroup(selectedCategory.id, newGroupName.trim())
    if (group) {
      onChange({ ...value, tag_groups: [...new Set([...value.tag_groups, group.name])] })
      setTargetGroupId(group.id)
      setNewGroupName('')
    }
  }

  async function submitTag() {
    if (!selectedCategory || !newTagName.trim()) {
      return
    }
    const groupId = typeof targetGroupId === 'number' ? targetGroupId : selectedGroups[0]?.id ?? visibleGroups[0]?.id
    if (!groupId) {
      return
    }
    const tag = await onCreateTag(selectedCategory.id, groupId, newTagName.trim())
    if (tag) {
      const group = visibleGroups.find((item) => item.id === tag.tag_group_id)
      onChange({ ...value, tag_groups: group ? [...new Set([...value.tag_groups, group.name])] : value.tag_groups, tags: [...new Set([...value.tags, tag.name])] })
      setNewTagName('')
    }
  }

  return (
    <section className="classification-picker">
      <div className="classification-section">
        <div><p className="eyebrow">实验分类</p><h3>选择一级实验分类</h3></div>
        <div className="category-card-grid">
          {taxonomy.map((category) => <button className={value.experiment_category === category.name ? 'category-card active' : 'category-card'} type="button" disabled={disabled} key={category.id} onClick={() => setCategory(category)} style={{ borderColor: value.experiment_category === category.name ? category.color : undefined }}><strong>{category.name}</strong><span>{category.description}</span></button>)}
        </div>
      </div>
      {selectedCategory && (
        <>
          <div className="classification-section">
            <div className="classification-heading"><div><p className="eyebrow">标签组</p><h3>选择实验方向或标签组</h3></div><span className="muted">可多选，也可以新增标签组</span></div>
            <div className="taxonomy-chip-grid">
              {visibleGroups.map((group) => <button className={value.tag_groups.includes(group.name) ? 'taxonomy-chip active' : 'taxonomy-chip'} type="button" disabled={disabled} key={group.id} onClick={() => toggleGroup(group)}>{group.name}</button>)}
            </div>
            <div className="taxonomy-create-row">
              <input value={newGroupName} disabled={disabled} onChange={(event) => setNewGroupName(event.target.value)} placeholder="新增标签组，例如：细胞应激处理" />
              <button className="secondary" type="button" disabled={disabled || !newGroupName.trim()} onClick={() => { void submitGroup() }}>新增标签组</button>
            </div>
          </div>
          <div className="classification-section">
            <div className="classification-heading"><div><p className="eyebrow">具体标签</p><h3>至少选择两个 tag</h3></div><span className={value.tags.length >= 2 ? 'tag-count ok' : 'tag-count'}>已选 {value.tags.length} 个</span></div>
            <div className="taxonomy-chip-grid tag-grid">
              {visibleTags.map((tag) => <button className={value.tags.includes(tag.name) ? 'taxonomy-chip active' : 'taxonomy-chip'} type="button" disabled={disabled} key={`${tag.tag_group_id}-${tag.id}`} onClick={() => toggleTag(tag)}>{tag.name}</button>)}
            </div>
            <div className="taxonomy-create-row">
              <select value={targetGroupId} disabled={disabled} onChange={(event) => setTargetGroupId(event.target.value ? Number(event.target.value) : '')}>
                <option value="">选择新增 tag 所属标签组</option>
                {visibleGroups.map((group) => <option value={group.id} key={group.id}>{group.name}</option>)}
              </select>
              <input value={newTagName} disabled={disabled} onChange={(event) => setNewTagName(event.target.value)} placeholder="新增 tag，例如：CUT&Tag" />
              <button className="secondary" type="button" disabled={disabled || !newTagName.trim() || !visibleGroups.length} onClick={() => { void submitTag() }}>新增 tag</button>
            </div>
          </div>
        </>
      )}
    </section>
  )
}
