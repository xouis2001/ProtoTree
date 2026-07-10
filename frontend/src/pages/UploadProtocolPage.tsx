import { useEffect, useState } from 'react'
import { ProtocolClassificationPicker } from '../components/ProtocolClassificationPicker'
import { RichTextEditor } from '../components/RichTextEditor'
import type { ProtocolCategory, ProtocolClassificationValue, ProtocolParseResponse, ProtocolTag, ProtocolTagGroup, StructuredProtocol } from '../types'

type UploadProtocolPageProps = {
  parseResult: ProtocolParseResponse | null
  structured: StructuredProtocol
  setStructured: (value: StructuredProtocol) => void
  isExtractingFile: boolean
  isFormattingUpload: boolean
  onExtractFile: (file: File) => Promise<void>
  onAssistFormat: (titleHint: string) => Promise<ProtocolParseResponse | null>
  onSave: (title: string, abstract: string) => void
  taxonomy: ProtocolCategory[]
  onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>
  onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null>
}

export function UploadProtocolPage({ parseResult, structured, setStructured, isExtractingFile, isFormattingUpload, onExtractFile, onAssistFormat, onSave, taxonomy, onCreateTagGroup, onCreateTag }: UploadProtocolPageProps) {
  const plainContent = typeof structured.content === 'string' ? structured.content : ''
  const classification: ProtocolClassificationValue = {
    experiment_category: structured.experiment_category ?? structured.experiment_type ?? '',
    tag_groups: Array.isArray(structured.tag_groups) ? structured.tag_groups : [],
    tags: Array.isArray(structured.tags) ? structured.tags : structured.experiment_subtype ? [structured.experiment_subtype] : [],
  }
  const [title, setTitle] = useState('')
  const [abstract, setAbstract] = useState('')

  useEffect(() => {
    setTitle(parseResult?.title ?? '')
    setAbstract(parseResult?.abstract ?? '')
  }, [parseResult])

  function updateClassification(value: ProtocolClassificationValue) {
    setStructured({ ...structured, experiment_type: value.experiment_category, experiment_subtype: value.tags[0] ?? '', experiment_category: value.experiment_category, tag_groups: value.tag_groups, tags: value.tags })
  }

  return (
    <section className="upload-protocol-page">
      <section className="card file-extract-panel upload-protocol-card">
        <p className="eyebrow">文件建立 Protocol</p>
        <h2>上传 Word / PDF 提取 Protocol</h2>
        <p className="muted">用于已有文档版 Protocol：系统只提取文字并保留为大段文本，不自动拆分 Step。</p>
        <input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" disabled={isExtractingFile} onChange={(event) => { const file = event.target.files?.[0]; if (file) { void onExtractFile(file); event.currentTarget.value = '' } }} />
        {isExtractingFile && <p className="muted">正在提取文件文字...</p>}
      </section>
      <section className="card result-panel upload-result-card">
        <p className="eyebrow">提取结果</p>
        <h2>{parseResult ? '确认 Protocol 信息' : '等待上传文件'}</h2>
        <p className="muted">上传 PDF 或 Word 后，可先修改标题和摘要，再选择分类标签、编辑正文并保存为 Protocol。</p>
        <div className="upload-meta-grid">
          <label>
            标题
            <input value={title} disabled={!parseResult} onChange={(event) => setTitle(event.target.value)} placeholder="Protocol 标题" />
          </label>
          <label>
            摘要
            <textarea value={abstract} disabled={!parseResult} onChange={(event) => setAbstract(event.target.value)} placeholder="Protocol 摘要" />
          </label>
        </div>
        <div className="upload-ai-actions">
          <button className="secondary" type="button" disabled={!parseResult || isFormattingUpload} onClick={() => { void onAssistFormat(title) }}>{isFormattingUpload ? 'AI 整理中...' : 'AI辅助整理标题/摘要/格式'}</button>
          <span className="muted">AI 只做格式整理和标题摘要提炼，不应修改实验内容；请保存前核对。</span>
        </div>
        <ProtocolClassificationPicker taxonomy={taxonomy} value={classification} disabled={!parseResult} onChange={updateClassification} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
        <label className="rich-editor-field">
          大段文本内容
          <RichTextEditor value={plainContent} disabled={!parseResult} onChange={(content) => setStructured({ ...structured, content, content_format: 'html' })} placeholder="上传文件后可继续编辑 Protocol 内容" minHeight={520} />
        </label>
        <button className="primary" type="button" disabled={!parseResult || !title.trim() || !classification.experiment_category || classification.tags.length < 2} onClick={() => onSave(title, abstract)}>保存为 Protocol</button>
      </section>
    </section>
  )
}
