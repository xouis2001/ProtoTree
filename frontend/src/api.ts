import type { AgentSkillResource, AnalysisToolResource, AuthResponse, Comment, CommentCreate, CommentWithProtocol, CommercialProtocol, ContributionProfile, ContributionProfileLeaderboards, ContributionSummary, ImageMacroResource,
  Pitfall, PitfallCreate, ProjectStats, Protocol, ProtocolAuthorOption, ProtocolCreate, ProtocolDiffResponse, ProtocolFolder, ProtocolFolderCreate, ProtocolFolderUpdate, ProtocolForkPayload, ProtocolListFilters, ProtocolListResponse, ProtocolParseResponse, ProtocolStarSummary, ProtocolTag, ProtocolTagGroup, ProtocolTreeNode, ProtocolUpdate, TaxonomyResponse, User } from './types'
import { getToken } from './authSession'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    const detail = Array.isArray(error.detail) ? error.detail.map((item: { msg?: string }) => item.msg ?? '请求参数错误').join('；') : error.detail
    throw new Error(detail ?? '请求失败')
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function register(payload: { name: string; email: string; password: string; avatar: string }) {
  return request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function login(payload: { email: string; password: string }) {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getUsedAvatarColors() {
  return request<string[]>('/auth/avatar-colors')
}

function getFilenameFromDisposition(disposition: string | null) {
  if (!disposition) {
    return ''
  }
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1])
  }
  const plainMatch = disposition.match(/filename="?([^";]+)"?/i)
  return plainMatch?.[1] ?? ''
}

export async function downloadFile(path: string, fallbackFilename: string) {
  const token = getToken()
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '文件下载失败' }))
    throw new Error(error.detail ?? '文件下载失败')
  }
  const blob = await response.blob()
  const filename = getFilenameFromDisposition(response.headers.get('Content-Disposition')) || fallbackFilename || 'download'
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function listProtocolAuthors() {
  return request<ProtocolAuthorOption[]>('/protocols/authors')
}

export async function listProtocols(filters: ProtocolListFilters = {}) {
  const params = new URLSearchParams()
  if (filters.q) {
    params.set('q', filters.q)
  }
  if (filters.author_id) {
    params.set('author_id', String(filters.author_id))
  }
  if (filters.source) {
    params.set('source', filters.source)
  }
  if (filters.experiment_category) {
    params.set('experiment_category', filters.experiment_category)
  } else if (filters.experiment_type) {
    params.set('experiment_type', filters.experiment_type)
  }
  if (filters.experiment_subtype) {
    params.set('experiment_subtype', filters.experiment_subtype)
  }
  if (filters.tag_groups?.length) {
    params.set('tag_groups', filters.tag_groups.join(','))
  }
  if (filters.tags?.length) {
    params.set('tags', filters.tags.join(','))
  }
  if (filters.sort) {
    params.set('sort', filters.sort)
  }
  if (filters.page) {
    params.set('page', String(filters.page))
  }
  if (filters.page_size) {
    params.set('page_size', String(filters.page_size))
  }
  const query = params.toString()
  const response = await request<ProtocolListResponse | ProtocolListResponse['items']>(`/protocols${query ? `?${query}` : ''}`)
  if (Array.isArray(response)) {
    return {
      items: response,
      total: response.length,
      page: filters.page ?? 1,
      page_size: filters.page_size ?? response.length,
      pages: 1,
    }
  }
  return response
}

export function getProtocol(id: number) {
  return request<Protocol>(`/protocols/${id}`)
}

export function createProtocol(payload: ProtocolCreate) {
  return request<Protocol>('/protocols', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProtocol(id: number, payload: ProtocolUpdate) {
  return request<Protocol>(`/protocols/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function parseProtocol(rawText: string) {
  return request<ProtocolParseResponse>('/protocols/parse', {
    method: 'POST',
    body: JSON.stringify({ raw_text: rawText }),
  })
}

export function extractProtocolFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<ProtocolParseResponse>('/protocols/extract-file/upload', {
    method: 'POST',
    body: formData,
  })
}

export function formatUploadedProtocol(payload: { raw_text: string; title_hint?: string }) {
  return request<ProtocolParseResponse>('/protocols/format-upload', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function forkProtocol(id: number, payload: ProtocolForkPayload) {
  return request<Protocol>(`/protocols/${id}/fork`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteProtocol(id: number) {
  return request<void>(`/protocols/${id}`, {
    method: 'DELETE',
  })
}

export function starProtocol(id: number) {
  return request<ProtocolStarSummary>(`/protocols/${id}/star`, {
    method: 'POST',
  })
}

export function unstarProtocol(id: number) {
  return request<ProtocolStarSummary>(`/protocols/${id}/star`, {
    method: 'DELETE',
  })
}

export function listStarredProtocols(filters: { q?: string; sort?: ProtocolListFilters['sort']; page?: number; page_size?: number } = {}) {
  const params = new URLSearchParams()
  if (filters.q) {
    params.set('q', filters.q)
  }
  if (filters.sort) {
    params.set('sort', filters.sort)
  }
  if (filters.page) {
    params.set('page', String(filters.page))
  }
  if (filters.page_size) {
    params.set('page_size', String(filters.page_size))
  }
  const query = params.toString()
  return request<ProtocolListResponse>(`/protocols/starred${query ? `?${query}` : ''}`)
}

export function getProtocolTree(id: number) {
  return request<ProtocolTreeNode>(`/protocols/${id}/tree`)
}

export function getProtocolDiff(sourceId: number, targetId: number) {
  return request<ProtocolDiffResponse>(`/protocols/${sourceId}/diff/${targetId}`)
}

export function getCurrentUser() {
  return request<User>('/auth/me')
}

export function updateMyProjects(projects: string[]) {
  return request<User>('/auth/me/projects', {
    method: 'PUT',
    body: JSON.stringify({ projects }),
  })
}

export function getMyContributions() {
  return request<ContributionSummary>('/me/contributions')
}

export function getReceivedComments() {
  return request<CommentWithProtocol[]>('/me/comments/received')
}

export function listFolders() {
  return request<ProtocolFolder[]>('/folders')
}

export function createFolder(payload: ProtocolFolderCreate) {
  return request<ProtocolFolder>('/folders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateFolder(id: number, payload: ProtocolFolderUpdate) {
  return request<ProtocolFolder>(`/folders/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteFolder(id: number) {
  return request<void>(`/folders/${id}`, {
    method: 'DELETE',
  })
}

export function getContributionProfile() {
  return request<ContributionProfile>('/me/contribution-profile')
}

export function getContributionProfileLeaderboards() {
  return request<ContributionProfileLeaderboards>('/contribution-profile/leaderboards')
}

export function listCommercialProtocols() {
  return request<CommercialProtocol[]>('/commercial-protocols')
}

export function listStarredCommercialProtocols() {
  return request<CommercialProtocol[]>('/commercial-protocols/starred')
}

export function starCommercialProtocol(id: string) {
  return request<ProtocolStarSummary>(`/commercial-protocols/${id}/star`, {
    method: 'POST',
  })
}

export function unstarCommercialProtocol(id: string) {
  return request<ProtocolStarSummary>(`/commercial-protocols/${id}/star`, {
    method: 'DELETE',
  })
}

export function listImageMacros() {
  return request<ImageMacroResource[]>('/public-resources/image-macros')
}

export function createImageMacro(payload: { title: string; description: string; code: string }) {
  return request<ImageMacroResource>('/public-resources/image-macros', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateImageMacro(id: string, payload: { title: string; description: string; code: string }) {
  return request<ImageMacroResource>(`/public-resources/image-macros/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteImageMacro(id: string) {
  return request<void>(`/public-resources/image-macros/${id}`, {
    method: 'DELETE',
  })
}

export function listAnalysisTools() {
  return request<AnalysisToolResource[]>('/public-resources/analysis-tools')
}

export function uploadAnalysisTool(payload: { title: string; description: string; file: File }) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('description', payload.description)
  formData.append('file', payload.file)
  return request<AnalysisToolResource>('/public-resources/analysis-tools', {
    method: 'POST',
    body: formData,
  })
}

export function updateAnalysisTool(id: string, payload: { title: string; description: string; file?: File | null }) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('description', payload.description)
  if (payload.file) {
    formData.append('file', payload.file)
  }
  return request<AnalysisToolResource>(`/public-resources/analysis-tools/${id}`, {
    method: 'PUT',
    body: formData,
  })
}

export function deleteAnalysisTool(id: string) {
  return request<void>(`/public-resources/analysis-tools/${id}`, {
    method: 'DELETE',
  })
}

export function listAgentSkills() {
  return request<AgentSkillResource[]>('/public-resources/agent-skills')
}

export function createAgentSkill(payload: { title: string; description: string; source_model: string; source_agent: string; file: File }) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('description', payload.description)
  formData.append('source_model', payload.source_model)
  formData.append('source_agent', payload.source_agent)
  formData.append('file', payload.file)
  return request<AgentSkillResource>('/public-resources/agent-skills', {
    method: 'POST',
    body: formData,
  })
}

export function updateAgentSkill(id: string, payload: { title: string; description: string; source_model: string; source_agent: string; file?: File | null }) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('description', payload.description)
  formData.append('source_model', payload.source_model)
  formData.append('source_agent', payload.source_agent)
  if (payload.file) {
    formData.append('file', payload.file)
  }
  return request<AgentSkillResource>(`/public-resources/agent-skills/${id}`, {
    method: 'PUT',
    body: formData,
  })
}

export function deleteAgentSkill(id: string) {
  return request<void>(`/public-resources/agent-skills/${id}`, {
    method: 'DELETE',
  })
}

export function getTaxonomy() {
  return request<TaxonomyResponse>('/taxonomy')
}

export function createTagGroup(payload: { category_id: number; name: string; description?: string }) {
  return request<ProtocolTagGroup>('/taxonomy/tag-groups', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function createTag(payload: { category_id: number; tag_group_id: number; name: string; description?: string }) {
  return request<ProtocolTag>('/taxonomy/tags', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getProjectStats(): Promise<ProjectStats> {
  const [laboratoryResponse, baseResponse, userResponse, commercialProtocols, imageMacros, analysisTools, agentSkills, taxonomy] = await Promise.all([
    listProtocols({ page: 1, page_size: 1 }).catch(() => ({ items: [], total: 0, page: 1, page_size: 1, pages: 1 })),
    listProtocols({ source: 'base', page: 1, page_size: 1 }).catch(() => ({ items: [], total: 0, page: 1, page_size: 1, pages: 1 })),
    listProtocols({ source: 'user', page: 1, page_size: 1 }).catch(() => ({ items: [], total: 0, page: 1, page_size: 1, pages: 1 })),
    listCommercialProtocols().catch(() => []),
    listImageMacros().catch(() => []),
    listAnalysisTools().catch(() => []),
    listAgentSkills().catch(() => []),
    getTaxonomy().catch(() => ({ categories: [] })),
  ])
  return {
    laboratory_protocols: laboratoryResponse.total ?? laboratoryResponse.items.length,
    base_protocols: baseResponse.total ?? baseResponse.items.length,
    user_protocols: userResponse.total ?? userResponse.items.length,
    commercial_protocols: commercialProtocols.length,
    image_macros: imageMacros.length,
    analysis_tools: analysisTools.length,
    agent_skills: agentSkills.length,
    taxonomy_categories: taxonomy.categories.length,
  }
}

export function uploadCommercialProtocol(payload: { title: string; manufacturer: string; catalog_no: string; description: string; file: File }) {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('manufacturer', payload.manufacturer)
  formData.append('catalog_no', payload.catalog_no)
  formData.append('description', payload.description)
  formData.append('file', payload.file)
  return request<CommercialProtocol>('/commercial-protocols/upload', {
    method: 'POST',
    body: formData,
  })
}

export function deleteCommercialProtocol(id: string) {
  return request<void>(`/commercial-protocols/${id}`, {
    method: 'DELETE',
  })
}

export function listPitfalls(protocolId: number) {
  return request<Pitfall[]>(`/protocols/${protocolId}/pitfalls`)
}

export function createPitfall(protocolId: number, payload: PitfallCreate) {
  return request<Pitfall>(`/protocols/${protocolId}/pitfalls`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listComments(protocolId: number) {
  return request<Comment[]>(`/protocols/${protocolId}/comments`)
}

export function createComment(protocolId: number, payload: CommentCreate) {
  return request<Comment>(`/protocols/${protocolId}/comments`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
