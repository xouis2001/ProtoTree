import type { FormEvent } from 'react'
import type { LibraryFilters } from '../appTypes'
import { Avatar } from '../components/Avatar'
import { Icon } from '../components/Icon'
import type { ProtocolAuthorOption, ProtocolCategory, ProtocolListItem, ProtocolListSort, ProtocolTag } from '../types'

export function getProtocolCategoryLabel(protocol: ProtocolListItem) {
  return protocol.structured?.experiment_category || protocol.structured?.experiment_type || '未分类'
}

export function getProtocolTagGroups(protocol: ProtocolListItem) {
  return Array.isArray(protocol.structured?.tag_groups) ? protocol.structured.tag_groups : []
}

export function getProtocolTags(protocol: ProtocolListItem) {
  if (Array.isArray(protocol.structured?.tags) && protocol.structured.tags.length) {
    return protocol.structured.tags
  }
  return protocol.structured?.experiment_subtype ? [protocol.structured.experiment_subtype] : []
}

function getProtocolSourceLabel(protocol: ProtocolListItem) {
  return protocol.source === 'base' ? '公共数据库' : '用户上传'
}

function dedupeProtocolTags(tags: ProtocolTag[]) {
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

export function ProtocolLibrary({ filters, setFilters, protocols, selectedId, handleSelect, total, page, pages, onPageChange, authors, taxonomy, isLoading = false }: { filters: LibraryFilters; setFilters: (value: LibraryFilters) => void; protocols: ProtocolListItem[]; selectedId: number | null; handleSelect: (id: number) => void; total: number; page: number; pages: number; onPageChange: (page: number) => void; authors: ProtocolAuthorOption[]; taxonomy: ProtocolCategory[]; isLoading?: boolean }) {
  return (
    <section className="library-page">
      <ProtocolFilterBar filters={filters} setFilters={setFilters} authors={authors} taxonomy={taxonomy} isLoading={isLoading} />
      <div className="library-stats">
        <span>共 {total} 条 Protocol</span>
        <span>第 {page} / {Math.max(pages, 1)} 页</span>
        {isLoading && <span className="library-loading-pill">正在筛选...</span>}
      </div>
      <ProtocolSearchPanel protocols={protocols} selectedId={selectedId} onSelectProtocol={handleSelect} title="实验室Protocol库" eyebrow="搜索结果" isLoading={isLoading} />
      {pages > 1 && <ProtocolPagination page={page} pages={pages} onPageChange={onPageChange} />}
    </section>
  )
}

export function ProtocolFilterBar({ filters, setFilters, compact = false, authors = [], taxonomy = [], isLoading = false }: { filters: LibraryFilters; setFilters: (value: LibraryFilters) => void; compact?: boolean; authors?: ProtocolAuthorOption[]; taxonomy?: ProtocolCategory[]; isLoading?: boolean }) {
  const selectedCategory = taxonomy.find((category) => category.name === filters.experiment_category) ?? null
  const tagGroups = selectedCategory?.tag_groups ?? []
  const activeGroupNames = filters.tag_groups.length ? new Set(filters.tag_groups) : null
  const allTags = tagGroups.flatMap((group) => group.tags)
  const selectedTagNames = new Set(filters.tags)
  const tags = activeGroupNames ? dedupeProtocolTags([...tagGroups.filter((group) => activeGroupNames.has(group.name)).flatMap((group) => group.tags), ...allTags.filter((tag) => selectedTagNames.has(tag.name))]) : allTags

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFilters({ ...filters, page: 1 })
  }

  function toggleGroup(name: string) {
    const nextGroups = filters.tag_groups.includes(name) ? filters.tag_groups.filter((item) => item !== name) : [...filters.tag_groups, name]
    setFilters({ ...filters, tag_groups: nextGroups, page: 1 })
  }

  function toggleTag(tag: ProtocolTag) {
    const group = tagGroups.find((item) => item.id === tag.tag_group_id)
    const nextGroups = group && !filters.tag_groups.includes(group.name) ? [...filters.tag_groups, group.name] : filters.tag_groups
    setFilters({ ...filters, tag_groups: nextGroups, tags: filters.tags.includes(tag.name) ? filters.tags.filter((item) => item !== tag.name) : [...filters.tags, tag.name], page: 1 })
  }

  return (
    <form className={`card filters taxonomy-filters ${compact ? 'compact' : ''}`} onSubmit={submit}>
      <div className="filter-row filter-search-row">
        <label>关键词<input value={filters.q} onChange={(event) => setFilters({ ...filters, q: event.target.value, page: 1 })} placeholder="搜索标题、摘要、原文" /></label>
        <label>作者<select value={filters.author_id ?? ''} onChange={(event) => setFilters({ ...filters, author_id: event.target.value ? Number(event.target.value) : '', page: 1 })}><option value="">全部</option>{authors.map((author) => <option value={author.id} key={author.id}>{author.name}</option>)}</select></label>
        <label>排序<select value={filters.sort} onChange={(event) => setFilters({ ...filters, sort: event.target.value as ProtocolListSort, page: 1 })}><option value="newest">最新</option><option value="oldest">最早</option><option value="title">标题</option></select></label>
        <button className="secondary" type="submit" disabled={isLoading}>{isLoading ? '筛选中...' : '筛选'}</button>
      </div>
      <div className="taxonomy-filter-block">
        <span>一级分类</span>
        <div className="taxonomy-chip-grid compact-chip-grid">
          <button className={!filters.experiment_category ? 'taxonomy-chip active' : 'taxonomy-chip'} type="button" onClick={() => setFilters({ ...filters, experiment_category: '', experiment_type: '', experiment_subtype: '', tag_groups: [], tags: [], page: 1 })}>全部</button>
          {taxonomy.map((category) => <button className={filters.experiment_category === category.name ? 'taxonomy-chip active' : 'taxonomy-chip'} type="button" key={category.id} onClick={() => setFilters({ ...filters, experiment_category: category.name, experiment_type: '', experiment_subtype: '', tag_groups: [], tags: [], page: 1 })}>{category.name}</button>)}
        </div>
      </div>
      {selectedCategory && <div className="taxonomy-filter-block"><span>标签组</span><div className="taxonomy-chip-grid compact-chip-grid">{tagGroups.map((group) => <button className={filters.tag_groups.includes(group.name) ? 'taxonomy-chip active' : 'taxonomy-chip'} type="button" key={group.id} onClick={() => toggleGroup(group.name)}>{group.name}</button>)}</div></div>}
      {selectedCategory && <div className="taxonomy-filter-block"><span>Tags</span><div className="taxonomy-chip-grid compact-chip-grid tag-grid">{tags.map((tag) => <button className={filters.tags.includes(tag.name) ? 'taxonomy-chip active' : 'taxonomy-chip'} type="button" key={`${tag.tag_group_id}-${tag.id}`} onClick={() => toggleTag(tag)}>{tag.name}</button>)}</div></div>}
    </form>
  )
}

export function ProtocolPagination({ page, pages, onPageChange }: { page: number; pages: number; onPageChange: (page: number) => void }) {
  return (
    <div className="pagination">
      <button className="secondary" type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>上一页</button>
      <span>{page} / {pages}</span>
      <button className="secondary" type="button" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>下一页</button>
    </div>
  )
}

export function ProtocolSearchPanel({ protocols, selectedId, onSelectProtocol, title, eyebrow, compact = false, isLoading = false }: { protocols: ProtocolListItem[]; selectedId: number | null; onSelectProtocol: (id: number) => void | Promise<void>; title: string; eyebrow: string; compact?: boolean; isLoading?: boolean }) {
  const items = protocols ?? []
  return (
    <section className={`card protocol-list-panel ${compact ? 'compact' : ''}`} aria-busy={isLoading}>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {isLoading && <div className="protocol-loading-state"><span className="loading-dot" />正在筛选 Protocol...</div>}
      <div className="protocol-list">
        {items.length === 0 && <p className="empty">暂无 Protocol。</p>}
        {items.map((protocol) => {
          const tagGroups = getProtocolTagGroups(protocol)
          const tags = getProtocolTags(protocol)
          return (
            <button className={`${selectedId === protocol.id ? 'protocol-card selected' : 'protocol-card'} protocol-source-${protocol.source ?? 'user'}`} type="button" key={protocol.id} onClick={() => onSelectProtocol(protocol.id)}>
              <div className="protocol-card-title"><strong>{protocol.title}</strong></div>
              <p>{protocol.abstract}</p>
              <div className="protocol-card-meta">
                <span className="avatar-line"><Avatar value={protocol.author.avatar} config={protocol.author.avatar_config} size="tiny" label={protocol.author.name} /> {protocol.author.name}</span>
                <span className="protocol-source-pill">{getProtocolSourceLabel(protocol)}</span>
                <span>{getProtocolCategoryLabel(protocol)}</span>
                {tagGroups.slice(0, 1).map((group) => <span key={group}>{group}</span>)}
                {tags.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}
                <span><Icon name="star" size={12} /> {protocol.star_count}</span>
                <span>{new Date(protocol.created_at).toLocaleDateString()}</span>
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}
