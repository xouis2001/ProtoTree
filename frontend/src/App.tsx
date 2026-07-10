import { FormEvent, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { createComment, createFolder, createProtocol, createTag, createTagGroup, deleteFolder, deleteProtocol, extractProtocolFile, formatUploadedProtocol, forkProtocol, getContributionProfile, getContributionProfileLeaderboards, getCurrentUser, getProjectStats, getProtocol, getProtocolTree, getReceivedComments, getTaxonomy, listComments, listFolders, listProtocolAuthors, listProtocols, listStarredCommercialProtocols, listStarredProtocols, starProtocol, unstarProtocol, updateFolder, updateProtocol } from './api'
import { defaultStructured } from './appConstants'
import type { FolderForm, ForkForm, LibraryFilters, ProtocolEditForm } from './appTypes'

import { clearToken, getToken } from './authSession'
import { ErrorBoundary } from './ErrorBoundary'
import { AppLayout } from './layout/AppLayout'
import { AgentSkillsPage } from './pages/AgentSkillsPage'
import { CommercialProtocolDetailPage, CommercialProtocolsPage } from './pages/CommercialProtocolsPage'
import { CreateCommercialProtocolPage } from './pages/CreateCommercialProtocolPage'
import { buildDirectProtocolStructured, CreateProtocolPage, type CreateProtocolDraft } from './pages/CreateProtocolPage'
import { HomePage } from './pages/HomePage'
import { DataProcessingResourcesPage } from './pages/DataProcessingResourcesPage'
import { MyProtocolLibrary } from './pages/MyProtocolLibrary'
import { ForkProtocolPage } from './pages/ForkProtocolPage'
import { ProfileCenter } from './pages/ProfileCenter'
import { ProtocolDetailPage } from './pages/ProtocolDetailPage'
import { ProtocolLibrary } from './pages/ProtocolLibrary'
import { StarredProtocolsPage } from './pages/StarredProtocolsPage'
import { UploadProtocolPage } from './pages/UploadProtocolPage'
import type { Comment, CommentWithProtocol, CommercialProtocol, ContributionProfile, ContributionProfileLeaderboards, ProjectStats, Protocol, ProtocolAuthorOption, ProtocolCategory, ProtocolCreate, ProtocolFolder, ProtocolListItem, ProtocolParseResponse, ProtocolTag, ProtocolTagGroup, ProtocolTreeNode, StructuredProtocol, User } from './types'

function AppContent() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  const [protocols, setProtocols] = useState<ProtocolListItem[]>([])
  const [protocolTotal, setProtocolTotal] = useState(0)
  const [protocolPages, setProtocolPages] = useState(1)
  const [folders, setFolders] = useState<ProtocolFolder[]>([])
  const [selected, setSelected] = useState<Protocol | null>(null)
  const [editingProtocol, setEditingProtocol] = useState(false)
  const [editForm, setEditForm] = useState<ProtocolEditForm>({ title: '', abstract: '', raw_text: '', version_label: '', folder_id: null, structured: defaultStructured })
  const [protocolTree, setProtocolTree] = useState<ProtocolTreeNode | null>(null)
  const [contributionProfile, setContributionProfile] = useState<ContributionProfile | null>(null)
  const [contributionProfileLeaderboards, setContributionProfileLeaderboards] = useState<ContributionProfileLeaderboards | null>(null)
  const [projectStats, setProjectStats] = useState<ProjectStats | null>(null)
  const [receivedComments, setReceivedComments] = useState<CommentWithProtocol[]>([])
  const [starredProtocols, setStarredProtocols] = useState<ProtocolListItem[]>([])
  const [comments, setComments] = useState<Comment[]>([])
  const [protocolComment, setProtocolComment] = useState('')
  const [starredCommercialProtocols, setStarredCommercialProtocols] = useState<CommercialProtocol[]>([])
  const [message, setMessage] = useState('')
  const [busyAction, setBusyAction] = useState('')
  const [isProtocolLoading, setIsProtocolLoading] = useState(false)
  const [isExtractingFile, setIsExtractingFile] = useState(false)
  const [isFormattingUpload, setIsFormattingUpload] = useState(false)
  const [forkSource, setForkSource] = useState<Protocol | null>(null)
  const [forkForm, setForkForm] = useState<ForkForm>({ title: '', abstract: '', raw_text: '', version_label: 'fork', folder_id: null, structured: defaultStructured })
  const [parseResult, setParseResult] = useState<ProtocolParseResponse | null>(null)
  const [editableStructured, setEditableStructured] = useState<StructuredProtocol>(defaultStructured)
  const [protocolAuthors, setProtocolAuthors] = useState<ProtocolAuthorOption[]>([])
  const [taxonomy, setTaxonomy] = useState<ProtocolCategory[]>([])
  const [libraryFilters, setLibraryFilters] = useState<LibraryFilters>({ q: '', author_id: '', experiment_type: '', experiment_subtype: '', experiment_category: '', tag_groups: [], tags: [], sort: 'newest', page: 1, page_size: 20 })
  const myProtocols = useMemo(() => protocols.filter((protocol) => protocol.author_id === user?.id), [protocols, user?.id])

  async function refreshContributionData() {
    const nextUser = await getCurrentUser()
    setUser(nextUser)
    const [nextContributionProfile, nextContributionProfileLeaderboards, nextProjectStats, nextReceivedComments, nextTaxonomy, nextStarredProtocols, nextStarredCommercialProtocols] = await Promise.all([getContributionProfile().catch(() => null), getContributionProfileLeaderboards().catch(() => null), getProjectStats().catch(() => null), getReceivedComments().catch(() => []), getTaxonomy().catch(() => ({ categories: [] })), listStarredProtocols({ page_size: 20 }).catch(() => ({ items: [] })), listStarredCommercialProtocols().catch(() => [])])
    setContributionProfile(nextContributionProfile)
    setContributionProfileLeaderboards(nextContributionProfileLeaderboards)
    setProjectStats(nextProjectStats)
    setReceivedComments(nextReceivedComments)
    setTaxonomy(nextTaxonomy.categories)
    setStarredProtocols(nextStarredProtocols.items)
    setStarredCommercialProtocols(nextStarredCommercialProtocols)
  }


  function redirectToUnifiedLogin() {
    const next = `${window.location.pathname}${window.location.search}${window.location.hash}` || '/protocol/'
    window.location.href = `/login.html?next=${encodeURIComponent(next)}`
  }

  async function loadProtocol(id: number) {
    const detail = await getProtocol(id)
    setSelected(detail)
    try {
      setProtocolTree(await getProtocolTree(id))
    } catch {
      setProtocolTree(null)
    }
    try {
      setComments(await listComments(id))
    } catch {
      setComments([])
    }
    setProtocolComment('')
    setEditingProtocol(false)
  }

  async function refreshProtocols(preferredId?: number, filters = libraryFilters) {
    setIsProtocolLoading(true)
    try {
      const [response, nextFolders, nextAuthors] = await Promise.all([listProtocols(filters).catch(() => ({ items: [], total: 0, page: filters.page, page_size: filters.page_size, pages: 1 })), listFolders().catch(() => []), listProtocolAuthors().catch(() => [])])
      const items = Array.isArray(response.items) ? response.items : []
      setProtocols(items)
      setProtocolTotal(response.total ?? items.length)
      setProtocolPages(response.pages ?? 1)
      setFolders(Array.isArray(nextFolders) ? nextFolders : [])
      setProtocolAuthors(Array.isArray(nextAuthors) ? nextAuthors : [])
      const targetId = preferredId ?? selected?.id
      if (targetId && items.some((item) => item.id === targetId)) {
        await loadProtocol(targetId)
      } else if (!targetId) {
        setSelected(null)
        setProtocolTree(null)
        setComments([])
      }
    } finally {
      setIsProtocolLoading(false)
    }
  }

  async function handleExtractProtocolFile(file: File) {
    setMessage('')
    setIsExtractingFile(true)
    try {
      const result = await extractProtocolFile(file)
      const content = typeof result.structured.content === 'string' ? result.structured.content : ''
      const htmlContent = content.split(/\r?\n/).map((line) => `<p>${line || '<br>'}</p>`).join('')
      setParseResult(result)
      setEditableStructured({ ...result.structured, content: htmlContent, content_format: 'html' })
      setMessage('文件内容已提取为大段文本 Protocol')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '文件提取失败')
    } finally {
      setIsExtractingFile(false)
    }
  }

  async function handleSaveDirectProtocol(draft: CreateProtocolDraft) {
    const title = draft.title.trim()
    const content = draft.content.trim()
    if (!title || !content) {
      setMessage('请填写标题和 Protocol 内容')
      return
    }
    if (!draft.classification.experiment_category || draft.classification.tags.length < 2) {
      setMessage('请选择一级分类，并至少选择两个 tag')
      return
    }
    await saveProtocol({ title, abstract: draft.abstract, raw_text: content, structured: buildDirectProtocolStructured({ ...draft, title, content }), version_label: 'v1.0', folder_id: null })
  }

  async function handleAssistFormatUploadedProtocol(titleHint: string) {
    setMessage('')
    const rawText = typeof parseResult?.structured.content === 'string' ? parseResult.structured.content : typeof editableStructured.content === 'string' ? editableStructured.content : ''
    if (!rawText.trim()) {
      setMessage('请先上传 Word 或 PDF 并提取内容')
      return null
    }
    setIsFormattingUpload(true)
    try {
      const result = await formatUploadedProtocol({ raw_text: rawText, title_hint: titleHint })
      setParseResult(result)
      setEditableStructured({ ...editableStructured, ...result.structured, content_format: 'html' })
      setMessage(result.warnings[0] ?? 'AI 辅助整理完成，请核对后保存')
      return result
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'AI辅助整理失败')
      return null
    } finally {
      setIsFormattingUpload(false)
    }
  }

  async function handleSaveUploadedProtocol(title: string, abstract: string) {
    if (!parseResult) {
      setMessage('请先上传并提取文件')
      return
    }
    const content = typeof editableStructured.content === 'string' ? editableStructured.content : ''
    const uploadTags = Array.isArray(editableStructured.tags) ? editableStructured.tags : []
    if (!editableStructured.experiment_category || uploadTags.length < 2) {
      setMessage('请选择一级分类，并至少选择两个 tag')
      return
    }
    await saveProtocol({ title: title.trim(), abstract, raw_text: content, structured: { ...editableStructured, experiment_type: editableStructured.experiment_category, experiment_subtype: uploadTags[0] ?? '', content, content_format: 'html' }, version_label: 'v1.0', folder_id: null })
  }

  async function handleCreateTagGroup(categoryId: number, name: string): Promise<ProtocolTagGroup | null> {
    setMessage('')
    try {
      const group = await createTagGroup({ category_id: categoryId, name })
      const nextTaxonomy = await getTaxonomy()
      setTaxonomy(nextTaxonomy.categories)
      setMessage(`标签组「${group.name}」已加入标签库`)
      return group
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '新增标签组失败')
      return null
    }
  }

  async function handleCreateTag(categoryId: number, tagGroupId: number, name: string): Promise<ProtocolTag | null> {
    setMessage('')
    try {
      const tag = await createTag({ category_id: categoryId, tag_group_id: tagGroupId, name })
      const nextTaxonomy = await getTaxonomy()
      setTaxonomy(nextTaxonomy.categories)
      setMessage(`Tag「${tag.name}」已加入标签库`)
      return tag
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '新增 tag 失败')
      return null
    }
  }

  async function saveProtocol(payload: ProtocolCreate) {
    setMessage('')
    try {
      const created = await createProtocol(payload)
      setMessage(`Protocol「${created.title}」已新建成功`)
      await refreshContributionData()
      await refreshProtocols(created.id)
      navigate(`/protocols/${created.id}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '保存失败')
    } finally {
      setBusyAction('')
    }
  }

  function startFork(protocol: Protocol) {
    const forkContent = buildForkContent(protocol)
    setForkSource(protocol)
    setForkForm({ title: `${protocol.title} fork`, abstract: protocol.abstract, raw_text: stripHtmlText(forkContent), structured: { ...protocol.structured, content: forkContent, content_format: 'html', steps: [] }, version_label: 'fork', folder_id: null })
    setMessage('')
  }

  async function handleFork(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!forkSource) {
      return
    }
    setMessage('')
    try {
      const forked = await forkProtocol(forkSource.id, { title: forkForm.title, abstract: forkForm.abstract, raw_text: forkForm.raw_text, structured: forkForm.structured, version_label: forkForm.version_label, folder_id: forkForm.folder_id })
      setForkSource(null)
      setMessage('Fork 已创建')
      await refreshContributionData()
      await refreshProtocols(forked.id)
      navigate(`/protocols/${forked.id}`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Fork 失败，请检查结构化 JSON 是否正确')
    }
  }

  async function handleAddProtocolComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) {
      return
    }
    setMessage('')
    try {
      await createComment(selected.id, { content: protocolComment, step_order: null })
      setComments(await listComments(selected.id))
      await refreshContributionData()
      setProtocolComment('')
      setMessage('评论已添加')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '添加评论失败')
    }
  }

  async function handleToggleStar() {
    if (!selected) {
      return
    }
    setMessage('')
    setBusyAction('star')
    try {
      const summary = selected.starred_by_me ? await unstarProtocol(selected.id) : await starProtocol(selected.id)
      setSelected({ ...selected, star_count: summary.star_count, starred_by_me: summary.starred_by_me })
      setProtocols((items) => items.map((item) => item.id === selected.id ? { ...item, star_count: summary.star_count, starred_by_me: summary.starred_by_me } : item))
      const nextStarredProtocols = await listStarredProtocols({ page_size: 20 }).catch(() => ({ items: [] }))
      setStarredProtocols(nextStarredProtocols.items)
      await refreshContributionData()
      setMessage(summary.starred_by_me ? '已送上小星星' : '已取消小星星')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '小星星操作失败')
    } finally {
      setBusyAction('')
    }
  }

  async function handleSelect(id: number) {
    setMessage('')
    await loadProtocol(id)
  }

  async function openProtocol(id: number) {
    await handleSelect(id)
    navigate(`/protocols/${id}`)
  }

  function startEditSelectedProtocol() {
    if (!selected) {
      return
    }
    setEditForm({ title: selected.title, abstract: selected.abstract, raw_text: selected.raw_text, version_label: selected.version_label, folder_id: selected.folder_id, structured: selected.structured })
    setMessage('')
    setEditingProtocol(true)
  }

  async function handleUpdateSelectedProtocol(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) {
      return
    }
    setMessage('')
    setBusyAction('update')
    try {
      const updated = await updateProtocol(selected.id, { title: editForm.title, abstract: editForm.abstract, raw_text: editForm.raw_text, version_label: editForm.version_label, folder_id: editForm.folder_id, structured: editForm.structured })
      setSelected(updated)
      setEditingProtocol(false)
      setMessage(`Protocol「${updated.title}」已更新成功`)
      await refreshProtocols(updated.id)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '更新失败')
    } finally {
      setBusyAction('')
    }
  }

  async function handleDeleteSelectedProtocol() {
    if (!selected) {
      return
    }
    if (!window.confirm(`确认删除 Protocol「${selected.title}」？删除后相关贡献分也会扣除。`)) {
      return
    }
    setMessage('')
    setBusyAction('delete')
    try {
      await deleteProtocol(selected.id)
      setMessage('Protocol 已删除，对应贡献分已扣除')
      await refreshContributionData()
      await refreshProtocols()
      navigate('/library')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '删除失败')
    } finally {
      setBusyAction('')
    }
  }

  async function handleCreateFolder(payload: FolderForm) {
    if (!payload.name.trim()) {
      setMessage('请输入文件夹名称')
      return false
    }
    setMessage('')
    try {
      await createFolder({ name: payload.name.trim(), parent_id: payload.parent_id })
      setFolders(await listFolders())
      setMessage('文件夹已创建')
      return true
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '创建文件夹失败')
      return false
    }
  }

  async function handleRenameFolder(folder: ProtocolFolder, name: string) {
    const nextName = name.trim()
    if (!nextName) {
      setMessage('请输入文件夹名称')
      return
    }
    setMessage('')
    try {
      await updateFolder(folder.id, { name: nextName, parent_id: folder.parent_id })
      setFolders(await listFolders())
      setMessage('文件夹已重命名')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '重命名失败')
    }
  }

  async function handleDeleteFolder(folder: ProtocolFolder) {
    if (!window.confirm(`确认删除文件夹「${folder.name}」？其中的 Protocol 会移动到未分类。`)) {
      return
    }
    setMessage('')
    try {
      await deleteFolder(folder.id)
      await refreshProtocols(selected?.id)
      setMessage('文件夹已删除')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '删除文件夹失败')
    }
  }

  async function handleMoveProtocol(protocolId: number, folderId: number | null) {
    setMessage('')
    try {
      const updated = await updateProtocol(protocolId, { folder_id: folderId })
      setProtocols((items) => items.map((item) => item.id === protocolId ? { ...item, folder_id: updated.folder_id } : item))
      if (selected?.id === protocolId) {
        setSelected(updated)
      }
      setMessage('Protocol 已移动')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '移动失败')
    }
  }

  function updateLibraryFilters(next: LibraryFilters) {
    setLibraryFilters(next)
  }

  useEffect(() => {
    document.title = 'ProtoTree'
  }, [])

  useEffect(() => {
    if (!getToken()) {
      redirectToUnifiedLogin()
      return
    }
    let cancelled = false
    async function restoreSession() {
      try {
        await refreshContributionData()
        if (!cancelled) {
          await refreshProtocols()
        }
      } catch {
        clearToken()
        if (!cancelled) {
          setUser(null)
          redirectToUnifiedLogin()
        }
      }
    }
    void restoreSession()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!message) {
      return
    }
    const timer = window.setTimeout(() => setMessage(''), 2600)
    return () => window.clearTimeout(timer)
  }, [message])

  useEffect(() => {
    if (user) {
      void refreshProtocols(undefined, libraryFilters)
    }
  }, [libraryFilters, user?.id])

  useEffect(() => {
    if (user && location.pathname === '/starred-protocols') {
      void refreshContributionData()
    }
  }, [location.pathname, user?.id])

  if (!user) {
    return <main className="auth-redirect-screen"><p>正在跳转到 LuLab 统一登录…</p></main>
  }

  return (
    <Routes>
      <Route element={<AppLayout user={user} message={message} />}>
        <Route index element={<HomePage leaderboards={contributionProfileLeaderboards} projectStats={projectStats} />} />
        <Route path="library" element={<ProtocolLibrary filters={libraryFilters} setFilters={updateLibraryFilters} protocols={protocols} selectedId={selected?.id ?? null} handleSelect={(id) => { void openProtocol(id) }} total={protocolTotal} page={libraryFilters.page} pages={protocolPages} onPageChange={(page) => updateLibraryFilters({ ...libraryFilters, page })} authors={protocolAuthors} taxonomy={taxonomy} isLoading={isProtocolLoading} />} />
        <Route path="commercial-protocols" element={<CommercialProtocolsPage user={user} />} />
        <Route path="commercial-protocols/new" element={<CreateCommercialProtocolPage />} />
        <Route path="commercial-protocols/:id" element={<CommercialProtocolDetailPage user={user} />} />
        <Route path="create" element={<CreateProtocolPage onSaveDirectProtocol={handleSaveDirectProtocol} taxonomy={taxonomy} onCreateTagGroup={handleCreateTagGroup} onCreateTag={handleCreateTag} />} />
        <Route path="fork-protocol" element={<ForkProtocolPage forkSource={forkSource} forkForm={forkForm} setForkForm={setForkForm} handleFork={handleFork} protocols={protocols} handleSelect={handleSelect} startFork={startFork} resetForkSource={() => setForkSource(null)} folders={folders} protocolFilters={libraryFilters} setProtocolFilters={updateLibraryFilters} total={protocolTotal} page={libraryFilters.page} pages={protocolPages} onProtocolPageChange={(page) => updateLibraryFilters({ ...libraryFilters, page })} protocolAuthors={protocolAuthors} taxonomy={taxonomy} onCreateTagGroup={handleCreateTagGroup} onCreateTag={handleCreateTag} />} />
        <Route path="upload-protocol" element={<UploadProtocolPage parseResult={parseResult} structured={editableStructured} setStructured={setEditableStructured} isExtractingFile={isExtractingFile} isFormattingUpload={isFormattingUpload} onExtractFile={handleExtractProtocolFile} onAssistFormat={handleAssistFormatUploadedProtocol} onSave={handleSaveUploadedProtocol} taxonomy={taxonomy} onCreateTagGroup={handleCreateTagGroup} onCreateTag={handleCreateTag} />} />
        <Route path="resources/data-processing" element={<DataProcessingResourcesPage user={user} setMessage={setMessage} />} />
        <Route path="resources/agent-skills" element={<AgentSkillsPage user={user} setMessage={setMessage} />} />
        <Route path="profile" element={<ProfileCenter user={user} contributionProfile={contributionProfile} receivedComments={receivedComments} onSelectProtocol={(id) => { void openProtocol(id) }} />} />
        <Route path="my-library" element={<MyProtocolLibrary protocols={myProtocols} folders={folders} selectedId={selected?.id ?? null} onSelectProtocol={(id) => { void openProtocol(id) }} onCreateFolder={handleCreateFolder} onRenameFolder={handleRenameFolder} onDeleteFolder={handleDeleteFolder} onMoveProtocol={handleMoveProtocol} />} />
        <Route path="starred-protocols" element={<StarredProtocolsPage protocols={starredProtocols} commercialProtocols={starredCommercialProtocols} onSelectProtocol={(id) => { void openProtocol(id) }} onSelectCommercialProtocol={(id) => navigate(`/commercial-protocols/${id}`)} />} />
        <Route path="protocols/:id" element={<ProtocolDetailRoute currentUser={user} selected={selected} protocolTree={protocolTree} folders={folders} comments={comments} protocolComment={protocolComment} setProtocolComment={setProtocolComment} editingProtocol={editingProtocol} editForm={editForm} setEditForm={setEditForm} busyAction={busyAction} handleAddProtocolComment={handleAddProtocolComment} handleToggleStar={handleToggleStar} handleUpdateProtocol={handleUpdateSelectedProtocol} handleSelect={handleSelect} openProtocol={openProtocol} startEdit={startEditSelectedProtocol} cancelEdit={() => setEditingProtocol(false)} startFork={(protocol) => { startFork(protocol); navigate('/fork-protocol') }} onDelete={handleDeleteSelectedProtocol} onBack={() => navigate('/library')} taxonomy={taxonomy} onCreateTagGroup={handleCreateTagGroup} onCreateTag={handleCreateTag} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

function buildForkContent(protocol: Protocol) {
  if (typeof protocol.structured.content === 'string' && protocol.structured.content.trim()) {
    return protocol.structured.content
  }
  if (protocol.structured.steps?.length) {
    return protocol.structured.steps.map((step) => `<h3>${escapeHtmlText(step.title || `Step ${step.order}`)}</h3><p>${escapeHtmlText(step.content || '')}</p>`).join('')
  }
  if (protocol.raw_text.trim()) {
    return protocol.raw_text.split(/\n{2,}/).map((paragraph) => `<p>${escapeHtmlText(paragraph.trim())}</p>`).join('')
  }
  return ''
}

function stripHtmlText(html: string) {
  return html.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim()
}

function escapeHtmlText(value: string) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

function ProtocolDetailRoute({ currentUser, selected, protocolTree, folders, comments, protocolComment, setProtocolComment, editingProtocol, editForm, setEditForm, busyAction, handleAddProtocolComment, handleToggleStar, handleUpdateProtocol, handleSelect, openProtocol, startEdit, cancelEdit, startFork, onDelete, onBack, taxonomy, onCreateTagGroup, onCreateTag }: { currentUser: User; selected: Protocol | null; protocolTree: ProtocolTreeNode | null; folders: ProtocolFolder[]; comments: Comment[]; protocolComment: string; setProtocolComment: (value: string) => void; editingProtocol: boolean; editForm: ProtocolEditForm; setEditForm: (value: ProtocolEditForm) => void; busyAction: string; handleAddProtocolComment: (event: FormEvent<HTMLFormElement>) => void; handleToggleStar: () => void; handleUpdateProtocol: (event: FormEvent<HTMLFormElement>) => void; handleSelect: (id: number) => Promise<void>; openProtocol: (id: number) => Promise<void>; startEdit: () => void; cancelEdit: () => void; startFork: (protocol: Protocol) => void; onDelete: () => void; onBack: () => void; taxonomy: ProtocolCategory[]; onCreateTagGroup: (categoryId: number, name: string) => Promise<ProtocolTagGroup | null>; onCreateTag: (categoryId: number, tagGroupId: number, name: string) => Promise<ProtocolTag | null> }) {
  const params = useParams()
  const routeId = params.id ? Number(params.id) : null

  useEffect(() => {
    if (routeId && selected?.id !== routeId) {
      void handleSelect(routeId)
    }
  }, [routeId, selected?.id])

  return <ProtocolDetailPage currentUser={currentUser} selected={selected} protocolTree={protocolTree} folders={folders} comments={comments} protocolComment={protocolComment} setProtocolComment={setProtocolComment} editingProtocol={editingProtocol} editForm={editForm} setEditForm={setEditForm} busyAction={busyAction} handleAddProtocolComment={handleAddProtocolComment} handleToggleStar={handleToggleStar} handleUpdateProtocol={handleUpdateProtocol} handleSelect={(id) => { void openProtocol(id) }} startEdit={startEdit} cancelEdit={cancelEdit} startFork={startFork} onDelete={onDelete} onBack={onBack} taxonomy={taxonomy} onCreateTagGroup={onCreateTagGroup} onCreateTag={onCreateTag} />
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter basename="/protocol">
        <AppContent />
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
