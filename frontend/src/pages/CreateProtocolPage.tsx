import { useState } from 'react'
import { ProtocolClassificationPicker } from '../components/ProtocolClassificationPicker'
import { RichTextEditor } from '../components/RichTextEditor'
import type { ProtocolCategory, ProtocolClassificationValue, ProtocolTag, ProtocolTagGroup, StructuredProtocol } from '../types'

type CreateProtocolDraft = {
  title: string
  abstract: string
  content: string
  classification: ProtocolClassificationValue
}

const emptyClassification: ProtocolClassificationValue = { experiment_category: '', tag_groups: [], tags: [] }

export function CreateProtocolPage({ onSaveDirectProtocol, taxonomy, onCreateTagGroup, onCreateTag }: { onSaveDirectProtocol: (draft: CreateProtocolDraft) => void; taxonomy: ProtocolCategory[]; onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>; onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null> }) {
  const [draft, setDraft] = useState<CreateProtocolDraft>({ title: '', abstract: '', content: '', classification: emptyClassification })
  const canSave = draft.title.trim() && draft.content.replace(/<[^>]*>/g, '').trim() && draft.classification.experiment_category && draft.classification.tags.length >= 2

  function updateDraft(next: Partial<CreateProtocolDraft>) {
    setDraft({ ...draft, ...next })
  }

  return (
    <section className="create-layout direct-protocol-page">
      <form className="card direct-protocol-form" onSubmit={(event) => { event.preventDefault(); onSaveDirectProtocol(draft) }}>
        <p className="eyebrow">新建 Protocol</p>
        <h2>直接输入和编辑 Protocol</h2>
        <p className="muted">在下方大文本编辑框中直接编写 Protocol 内容，并通过一级分类、标签组和至少两个 tag 描述实验。</p>
        <div className="direct-protocol-meta-grid">
          <label>
            标题
            <input value={draft.title} onChange={(event) => updateDraft({ title: event.target.value })} placeholder="请输入 Protocol 标题" />
          </label>
          <label>
            摘要
            <textarea value={draft.abstract} onChange={(event) => updateDraft({ abstract: event.target.value })} placeholder="请输入摘要" />
          </label>
        </div>
        <ProtocolClassificationPicker taxonomy={taxonomy} value={draft.classification} onChange={(classification) => updateDraft({ classification })} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
        <label className="rich-editor-field">
          Protocol 内容
          <RichTextEditor value={draft.content} onChange={(content) => updateDraft({ content })} placeholder="在这里直接输入 Protocol 内容" minHeight={520} />
        </label>
        <div className="action-row">
          <button className="primary" type="submit" disabled={!canSave}>保存为 Protocol</button>
        </div>
      </form>
    </section>
  )
}

export type { CreateProtocolDraft }

export function buildDirectProtocolStructured(draft: CreateProtocolDraft): StructuredProtocol {
  return {
    experiment_name: draft.title.trim(),
    experiment_type: draft.classification.experiment_category,
    experiment_subtype: draft.classification.tags[0] ?? '',
    experiment_category: draft.classification.experiment_category,
    tag_groups: draft.classification.tag_groups,
    tags: draft.classification.tags,
    content: draft.content,
    content_format: 'html',
    steps: [],
  }
}
