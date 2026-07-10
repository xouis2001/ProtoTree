import { FormEvent } from 'react'
import type { ProtocolEditForm } from '../appTypes'
import { flattenTree, formatLocalDateTime, formatParameters, getLineage, normalizeSteps, sanitizeRichTextHtml, stripStepPrefix } from '../appUtils'
import { Avatar } from '../components/Avatar'
import { FolderSelect } from '../components/FolderSelect'
import { Icon } from '../components/Icon'
import { ProtocolClassificationPicker } from '../components/ProtocolClassificationPicker'
import { RichTextEditor } from '../components/RichTextEditor'
import type { Comment, Protocol, ProtocolCategory, ProtocolClassificationValue, ProtocolFolder, ProtocolTag, ProtocolTagGroup, ProtocolTreeNode, User } from '../types'

export function ProtocolDetailPage({ currentUser, selected, protocolTree, folders, comments, protocolComment, setProtocolComment, editingProtocol, editForm, setEditForm, busyAction, handleAddProtocolComment, handleToggleStar, handleUpdateProtocol, handleSelect, startEdit, cancelEdit, startFork, onDelete, onBack, taxonomy, onCreateTagGroup, onCreateTag }: { currentUser: User; selected: Protocol | null; protocolTree: ProtocolTreeNode | null; folders: ProtocolFolder[]; comments: Comment[]; protocolComment: string; setProtocolComment: (value: string) => void; editingProtocol: boolean; editForm: ProtocolEditForm; setEditForm: (value: ProtocolEditForm) => void; busyAction: string; handleAddProtocolComment: (event: FormEvent<HTMLFormElement>) => void; handleToggleStar: () => void; handleUpdateProtocol: (event: FormEvent<HTMLFormElement>) => void; handleSelect: (id: number) => void; startEdit: () => void; cancelEdit: () => void; startFork: (protocol: Protocol) => void; onDelete: () => void; onBack: () => void; taxonomy: ProtocolCategory[]; onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>; onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null> }) {
  if (!selected) {
    return <section className="card empty-state"><p className="eyebrow">Protocol 详情</p><h2>请选择一个 Protocol</h2></section>
  }
  return (
    <section className="detail-page">
      <div className="action-row"><button className="secondary" type="button" onClick={onBack}>返回实验室Protocol库</button></div>
      {protocolTree && <VersionLineage tree={protocolTree} selectedId={selected.id} onSelect={handleSelect} />}
      <ProtocolCard currentUser={currentUser} protocol={selected} folders={folders} comments={comments} protocolComment={protocolComment} setProtocolComment={setProtocolComment} editingProtocol={editingProtocol} editForm={editForm} setEditForm={setEditForm} busyAction={busyAction} onAddProtocolComment={handleAddProtocolComment} onToggleStar={handleToggleStar} onUpdateProtocol={handleUpdateProtocol} onEdit={startEdit} onCancelEdit={cancelEdit} onFork={() => startFork(selected)} onDelete={onDelete} taxonomy={taxonomy} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
    </section>
  )
}

function ProtocolCard({ currentUser, protocol, folders, comments, protocolComment, setProtocolComment, editingProtocol, editForm, setEditForm, busyAction, onAddProtocolComment, onToggleStar, onUpdateProtocol, onEdit, onCancelEdit, onFork, onDelete, taxonomy, onCreateTagGroup, onCreateTag }: { currentUser: User; protocol: Protocol; folders: ProtocolFolder[]; comments: Comment[]; protocolComment: string; setProtocolComment: (value: string) => void; editingProtocol: boolean; editForm: ProtocolEditForm; setEditForm: (value: ProtocolEditForm) => void; busyAction: string; onAddProtocolComment: (event: FormEvent<HTMLFormElement>) => void; onToggleStar: () => void; onUpdateProtocol: (event: FormEvent<HTMLFormElement>) => void; onEdit: () => void; onCancelEdit: () => void; onFork: () => void; onDelete: () => void; taxonomy: ProtocolCategory[]; onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>; onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null> }) {
  const steps = normalizeSteps(protocol.structured)
  const plainContent = typeof protocol.structured.content === 'string' ? protocol.structured.content : ''
  const isRichContent = protocol.structured.content_format === 'html'
  const safeContent = isRichContent ? sanitizeRichTextHtml(plainContent) : ''
  const categoryLabel = protocol.structured.experiment_category || protocol.structured.experiment_type || '其他'
  const tagGroups = Array.isArray(protocol.structured.tag_groups) ? protocol.structured.tag_groups : []
  const tags = Array.isArray(protocol.structured.tags) && protocol.structured.tags.length ? protocol.structured.tags : protocol.structured.experiment_subtype ? [protocol.structured.experiment_subtype] : []
  const editClassification: ProtocolClassificationValue = {
    experiment_category: editForm.structured.experiment_category || editForm.structured.experiment_type || '',
    tag_groups: Array.isArray(editForm.structured.tag_groups) ? editForm.structured.tag_groups : [],
    tags: Array.isArray(editForm.structured.tags) ? editForm.structured.tags : editForm.structured.experiment_subtype ? [editForm.structured.experiment_subtype] : [],
  }
  const canEdit = currentUser.id === protocol.author_id || currentUser.is_admin

  return (
    <section className="card protocol-detail-card">
      {!editingProtocol ? (
        <>
          <p className="eyebrow">{categoryLabel}</p>
          <h2>{protocol.title}</h2>
          <p className="muted">作者：{protocol.author.name} · 创建时间：{formatLocalDateTime(protocol.created_at)}</p>
          <div className="star-summary"><span><Icon name={protocol.starred_by_me ? 'star-filled' : 'star'} size={16} style={{ color: protocol.starred_by_me ? '#f59e0b' : undefined }} /> {protocol.star_count} 颗小星星</span><button className={protocol.starred_by_me ? 'star-button active' : 'star-button'} type="button" disabled={busyAction === 'star'} onClick={onToggleStar}><Icon name={protocol.starred_by_me ? 'star-filled' : 'star'} size={16} /> {protocol.starred_by_me ? '已送星星' : '送上小星星'}</button></div>
          <p>{protocol.abstract || '暂无摘要'}</p>
          <div className="protocol-taxonomy-summary"><span>{categoryLabel}</span>{tagGroups.map((group) => <span key={group}>{group}</span>)}{tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
          <div className="action-row"><button className="secondary" type="button" onClick={onFork}>Fork</button>{canEdit && <button className="secondary" type="button" onClick={onEdit}>编辑</button>}{canEdit && <button className="danger" type="button" disabled={busyAction === 'delete'} onClick={onDelete}>{busyAction === 'delete' ? '删除中...' : '删除'}</button>}</div>
        </>
      ) : (
        <form className="edit-form protocol-edit-form" onSubmit={onUpdateProtocol}>
          <div className="protocol-edit-header">
            <div>
              <p className="eyebrow">编辑 Protocol</p>
              <h3>基础信息</h3>
            </div>
            <div className="action-row"><button className="primary" type="submit" disabled={busyAction === 'update'}>{busyAction === 'update' ? '保存中...' : '保存修改'}</button><button className="secondary" type="button" onClick={onCancelEdit}>取消</button></div>
          </div>
          <div className="protocol-edit-grid single">
            <label>
              标题
              <input value={editForm.title} onChange={(event) => setEditForm({ ...editForm, title: event.target.value })} />
            </label>
          </div>
          <label>
            摘要
            <textarea value={editForm.abstract} onChange={(event) => setEditForm({ ...editForm, abstract: event.target.value })} />
          </label>
          <div className="protocol-edit-grid single">
            <label>
              保存到文件夹
              <FolderSelect folders={folders} value={editForm.folder_id} onChange={(folderId) => setEditForm({ ...editForm, folder_id: folderId })} />
            </label>
          </div>
          <ProtocolClassificationPicker taxonomy={taxonomy} value={editClassification} onChange={(classification) => setEditForm({ ...editForm, structured: { ...editForm.structured, experiment_type: classification.experiment_category, experiment_subtype: classification.tags[0] ?? '', experiment_category: classification.experiment_category, tag_groups: classification.tag_groups, tags: classification.tags } })} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
          {typeof editForm.structured.content === 'string' ? (
            <label className="rich-editor-field">
              Protocol 正文
              <RichTextEditor value={editForm.structured.content} onChange={(content) => setEditForm({ ...editForm, raw_text: content, structured: { ...editForm.structured, content, content_format: 'html' } })} minHeight={420} />
            </label>
          ) : (
            <label>
              原始文本
              <textarea className="protocol-edit-main-text" value={editForm.raw_text} onChange={(event) => setEditForm({ ...editForm, raw_text: event.target.value })} />
            </label>
          )}
        </form>
      )}
      {plainContent ? (
        <section className="steps-section">
          <h3>Protocol 正文</h3>
          {isRichContent ? <div className="rich-protocol-content" dangerouslySetInnerHTML={{ __html: safeContent }} /> : <div className="plain-protocol-content">{plainContent}</div>}
        </section>
      ) : (
        <section className="steps-section">
          <h3>步骤</h3>
          <div className="step-list">
            {steps.map((step, index) => <article className="step-card" key={`${step.order}-${index}`}><strong>Step {step.order ?? index + 1}：{stripStepPrefix(step.title ?? '') || `第${index + 1}步`}</strong><p>{step.content || '暂无步骤内容'}</p>{formatParameters(step.parameters) && <span>{formatParameters(step.parameters)}</span>}</article>)}
          </div>
        </section>
      )}
      <section className="protocol-comments-card">
        <div className="comment-panel-header">
          <div><p className="eyebrow">讨论与反馈</p><h3>Protocol 评论</h3><span>记录复现实验中的问题、优化建议和注意事项。</span></div>
          <strong>{comments.filter((comment) => comment.step_order === null).length} 条评论</strong>
        </div>
        <form className="comment-form" onSubmit={onAddProtocolComment}>
          <textarea value={protocolComment} onChange={(event) => setProtocolComment(event.target.value)} placeholder="分享你对这个 Protocol 的复现经验、疑问或改进建议" />
          <div className="comment-form-footer"><span>评论会展示给实验室成员，建议描述具体条件和现象。</span><button className="primary" type="submit" disabled={!protocolComment.trim()}>发布评论</button></div>
        </form>
        <CommentList comments={comments} />
      </section>
    </section>
  )
}

function CommentList({ comments }: { comments: Comment[] }) {
  const items = (comments ?? []).filter((comment) => comment.step_order === null).sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())
  return (
    <section className="comment-list">
      {items.length === 0 && <div className="comment-empty-state"><strong>暂无评论</strong><span>成为第一个分享复现实验经验的人。</span></div>}
      {items.map((item) => (
        <article className="comment-item" key={item.id}>
          <Avatar value={item.author.avatar} config={item.author.avatar_config} size="small" label={item.author.name} />
          <div className="comment-item-body">
            <div className="comment-item-meta"><strong>{item.author.name}</strong><span>{formatLocalDateTime(item.created_at)}</span></div>
            <p>{item.content}</p>
          </div>
        </article>
      ))}
    </section>
  )
}

function VersionLineage({ tree, selectedId, onSelect }: { tree: ProtocolTreeNode; selectedId: number; onSelect: (id: number) => void }) {
  const nodes = flattenTree(tree)
  const selected = nodes.find((node) => node.id === selectedId)
  const lineage = selected ? getLineage(nodes, selected) : nodes.slice(0, 1)

  return (
    <section className="card lineage-card">
      <p className="eyebrow">Fork 追踪</p>
      <h2>Fork 关系</h2>
      <div className="lineage-flow">
        {lineage.map((node, index) => <div className="lineage-segment" key={node.id}>{index > 0 && <span className="lineage-arrow">→</span>}<button className={`lineage-node ${node.id === selectedId ? 'active' : ''}`} type="button" onClick={() => onSelect(node.id)}><strong>{index === 0 ? '源头' : `Fork ${index}`}</strong><span>{node.title}</span><small>{node.author.name}</small></button></div>)}
      </div>
    </section>
  )
}
