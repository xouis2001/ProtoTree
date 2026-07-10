import { FormEvent } from 'react'
import { getProtocol } from '../api'
import type { ForkForm, LibraryFilters } from '../appTypes'
import { FolderSelect } from '../components/FolderSelect'
import { ProtocolClassificationPicker } from '../components/ProtocolClassificationPicker'
import { RichTextEditor } from '../components/RichTextEditor'
import type { Protocol, ProtocolAuthorOption, ProtocolCategory, ProtocolClassificationValue, ProtocolFolder, ProtocolListItem, ProtocolTag, ProtocolTagGroup, StructuredProtocol } from '../types'
import { ProtocolFilterBar, ProtocolPagination, ProtocolSearchPanel } from './ProtocolLibrary'

export function ForkProtocolPage({ forkSource, forkForm, setForkForm, handleFork, protocols, handleSelect, startFork, resetForkSource, folders, protocolFilters, setProtocolFilters, total, page, pages, onProtocolPageChange, protocolAuthors, taxonomy, onCreateTagGroup, onCreateTag }: { forkSource: Protocol | null; forkForm: ForkForm; setForkForm: (value: ForkForm) => void; handleFork: (event: FormEvent<HTMLFormElement>) => void; protocols: ProtocolListItem[]; handleSelect: (id: number) => Promise<void>; startFork: (protocol: Protocol) => void; resetForkSource: () => void; folders: ProtocolFolder[]; protocolFilters: LibraryFilters; setProtocolFilters: (value: LibraryFilters) => void; total: number; page: number; pages: number; onProtocolPageChange: (page: number) => void; protocolAuthors: ProtocolAuthorOption[]; taxonomy: ProtocolCategory[]; onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>; onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null> }) {
  if (!forkSource) {
    return <ForkSourceSelection protocols={protocols} handleSelect={handleSelect} startFork={startFork} protocolFilters={protocolFilters} setProtocolFilters={setProtocolFilters} total={total} page={page} pages={pages} onProtocolPageChange={onProtocolPageChange} protocolAuthors={protocolAuthors} taxonomy={taxonomy} />
  }

  return (
    <section className="fork-edit-stage">
      <ForkEditPanel source={forkSource} form={forkForm} setForm={setForkForm} onFork={handleFork} onBack={resetForkSource} folders={folders} taxonomy={taxonomy} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
    </section>
  )
}

function ForkSourceSelection({ protocols, handleSelect, startFork, protocolFilters, setProtocolFilters, total, page, pages, onProtocolPageChange, protocolAuthors, taxonomy }: { protocols: ProtocolListItem[]; handleSelect: (id: number) => Promise<void>; startFork: (protocol: Protocol) => void; protocolFilters: LibraryFilters; setProtocolFilters: (value: LibraryFilters) => void; total: number; page: number; pages: number; onProtocolPageChange: (page: number) => void; protocolAuthors: ProtocolAuthorOption[]; taxonomy: ProtocolCategory[] }) {
  return (
    <section className="library-page fork-library-page">
      <div className="card fork-library-hero">
        <div>
          <p className="eyebrow">Fork Protocol</p>
          <h2>选择要 Fork 的 Protocol</h2>
          <p className="muted">这个页面的筛选和展示方式与实验室 Protocol 库保持一致；点击任意 Protocol 后会直接进入 Fork 编辑页面。</p>
        </div>
        <div className="fork-stage-steps"><span className="active">1 选择来源</span><span>2 编辑 Fork</span></div>
      </div>
      <ProtocolFilterBar filters={protocolFilters} setFilters={setProtocolFilters} authors={protocolAuthors} taxonomy={taxonomy} />
      <div className="library-stats"><span>共 {total} 条可选 Protocol</span><span>第 {page} / {Math.max(pages, 1)} 页</span></div>
      <ProtocolSearchPanel protocols={protocols} selectedId={null} onSelectProtocol={async (id) => { await handleSelect(id); const detail = await getProtocol(id); startFork(detail) }} title="可 Fork 的 Protocol" eyebrow="来源列表" />
      {pages > 1 && <ProtocolPagination page={page} pages={pages} onPageChange={onProtocolPageChange} />}
    </section>
  )
}

function ForkEditPanel({ source, form, setForm, onFork, onBack, folders, taxonomy, onCreateTagGroup, onCreateTag }: { source: Protocol; form: ForkForm; setForm: (value: ForkForm) => void; onFork: (event: FormEvent<HTMLFormElement>) => void; onBack: () => void; folders: ProtocolFolder[]; taxonomy: ProtocolCategory[]; onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>; onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null> }) {
  const content = getForkContent(form)
  const classification = getForkClassification(form.structured)
  const canFork = Boolean(form.title.trim() && getPlainText(content).trim() && classification.experiment_category && classification.tags.length >= 2)

  function updateStructured(next: StructuredProtocol) {
    setForm({ ...form, structured: next })
  }

  function updateClassification(next: ProtocolClassificationValue) {
    updateStructured({
      ...form.structured,
      experiment_type: next.experiment_category,
      experiment_subtype: next.tags[0] ?? '',
      experiment_category: next.experiment_category,
      tag_groups: next.tag_groups,
      tags: next.tags,
    })
  }

  function updateContent(nextContent: string) {
    setForm({
      ...form,
      raw_text: getPlainText(nextContent),
      structured: {
        ...form.structured,
        content: nextContent,
        content_format: 'html',
        steps: [],
      },
    })
  }

  return (
    <form className="card fork-edit-panel fork-form-panel fork-modern-form" onSubmit={onFork}>
      <div className="fork-editor-hero">
        <div>
          <p className="eyebrow">Fork Protocol</p>
          <h2>编辑 Fork 内容</h2>
          <p className="muted">当前来源为「{source.title}」。你可以整体修改正文、更新分类 tag，并保存为新的 Fork Protocol。</p>
        </div>
        <div className="fork-editor-actions">
          <div className="fork-stage-steps"><span>1 选择来源</span><span className="active">2 编辑 Fork</span></div>
          <button className="secondary" type="button" onClick={onBack}>重新选择来源</button>
        </div>
      </div>
      <div className="fork-source-strip">
        <span>来源 Protocol</span><strong>{source.title}</strong>
      </div>
      <div className="fork-form-section fork-basic-section">
        <label>
          标题
          <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="请输入 Fork 后的 Protocol 标题" />
        </label>
        <label>
          摘要
          <textarea value={form.abstract} onChange={(event) => setForm({ ...form, abstract: event.target.value })} placeholder="请输入 Fork 后的摘要" />
        </label>
      </div>
      <div className="edit-row two fork-meta-grid">
        <label>
          保存到文件夹
          <FolderSelect folders={folders} value={form.folder_id} onChange={(folderId) => setForm({ ...form, folder_id: folderId })} />
        </label>
      </div>
      <ProtocolClassificationPicker taxonomy={taxonomy} value={classification} onChange={updateClassification} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
      <label className="rich-editor-field fork-rich-editor-field">
        Protocol 内容
        <RichTextEditor value={content} onChange={updateContent} placeholder="像新建 Protocol 一样，在这里整体编辑 Fork 后的内容" minHeight={520} />
      </label>
      <div className="fork-submit-row">
        <span>{classification.tags.length >= 2 ? '分类和 tag 已满足保存要求' : '请至少选择两个 tag 后再创建 Fork'}</span>
        <button className="primary" type="submit" disabled={!canFork}>创建 Fork</button>
      </div>
    </form>
  )
}

function getForkClassification(structured: StructuredProtocol): ProtocolClassificationValue {
  const category = structured.experiment_category || structured.experiment_type || ''
  const tagGroups = Array.isArray(structured.tag_groups) ? structured.tag_groups : []
  const tags = Array.isArray(structured.tags) && structured.tags.length ? structured.tags : structured.experiment_subtype ? [structured.experiment_subtype] : []
  return { experiment_category: category, tag_groups: tagGroups, tags }
}

function getForkContent(form: ForkForm) {
  if (typeof form.structured.content === 'string' && form.structured.content.trim()) {
    return form.structured.content
  }
  if (form.structured.steps?.length) {
    return form.structured.steps.map((step) => `<h3>${escapeHtml(step.title || `Step ${step.order}`)}</h3><p>${escapeHtml(step.content || '')}</p>`).join('')
  }
  if (form.raw_text.trim()) {
    return form.raw_text.split(/\n{2,}/).map((paragraph) => `<p>${escapeHtml(paragraph.trim())}</p>`).join('')
  }
  return ''
}

function getPlainText(html: string) {
  return html.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim()
}

function escapeHtml(value: string) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}
