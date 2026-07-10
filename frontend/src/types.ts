export type AvatarConfig = {
  bg?: string
  sel?: Record<string, string>
  colors?: Record<string, string>
} | null

export type User = {
  id: number
  name: string
  email: string
  avatar: string
  avatar_config?: AvatarConfig
  is_admin: boolean
  contribution_score: number
  projects: string[]
  created_at: string
}

export type AuthResponse = {
  access_token: string
  token_type: string
  user: User
}

export type StructuredStep = {
  order?: number
  title?: string
  content?: string
  parameters?: Record<string, string> | string
}

export type StructuredProtocol = {
  experiment_name?: string
  experiment_type?: string
  experiment_subtype?: string
  experiment_category?: string
  tag_groups?: string[]
  tags?: string[]
  content?: string
  content_format?: 'plain' | 'html'
  steps?: StructuredStep[]
  [key: string]: unknown
}

export type ProtocolSource = 'user' | 'base'

export type TaxonomySource = 'official' | 'user' | 'community'

export type TaxonomyStatus = 'active' | 'merged' | 'disabled'

export type ProtocolTag = {
  id: number
  category_id: number
  tag_group_id: number
  name: string
  description: string
  source: TaxonomySource
  status: TaxonomyStatus
  usage_count: number
  sort_order: number
  created_at: string
}

export type ProtocolTagGroup = {
  id: number
  category_id: number
  name: string
  description: string
  source: TaxonomySource
  status: TaxonomyStatus
  usage_count: number
  sort_order: number
  created_at: string
  tags: ProtocolTag[]
}

export type ProtocolCategory = {
  id: number
  name: string
  description: string
  color: string
  source: TaxonomySource
  status: TaxonomyStatus
  usage_count: number
  sort_order: number
  created_at: string
  tag_groups: ProtocolTagGroup[]
}

export type TaxonomyResponse = {
  categories: ProtocolCategory[]
}

export type ProtocolClassificationValue = {
  experiment_category: string
  tag_groups: string[]
  tags: string[]
}

export type ProtocolListItem = {
  id: number
  root_id: number | null
  parent_id: number | null
  title: string
  abstract: string
  author_id: number
  folder_id: number | null
  source: ProtocolSource
  author: User
  version_label: string
  structured?: StructuredProtocol
  star_count: number
  starred_by_me: boolean
  created_at: string
}

export type ProtocolListResponse = {
  items: ProtocolListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type ProtocolListSort = 'newest' | 'oldest' | 'title'

export type ProtocolAuthorOption = {
  id: number
  name: string
  avatar: string
}

export type ProtocolListFilters = {
  q?: string
  author_id?: number | ''
  source?: ProtocolSource
  experiment_type?: string
  experiment_subtype?: string
  experiment_category?: string
  tag_groups?: string[]
  tags?: string[]
  sort?: ProtocolListSort
  page?: number
  page_size?: number
}

export type ImageMacroResource = {
  id: string
  title: string
  description: string
  code: string
  author_id: number | null
  author_name: string
  created_at: string
}

export type AnalysisToolResource = {
  id: string
  title: string
  description: string
  filename: string
  file_size: number
  author_id: number | null
  author_name: string
  download_url: string
  created_at: string
}

export type AgentSkillResource = {
  id: string
  title: string
  description: string
  source_model: string
  source_agent: string
  content: string
  filename: string
  file_size: number
  author_id: number | null
  author_name: string
  download_url: string
  created_at: string
}

export type Protocol = ProtocolListItem & {
  author: User
  raw_text: string
  structured: StructuredProtocol
}

export type ProtocolCreate = {
  title: string
  abstract: string
  raw_text: string
  structured: StructuredProtocol
  version_label: string
  folder_id?: number | null
  source?: ProtocolSource
}

export type ProtocolUpdate = Partial<ProtocolCreate>

export type ProtocolForkPayload = {
  title?: string
  abstract?: string
  raw_text?: string
  structured?: StructuredProtocol
  version_label: string
  folder_id?: number | null
}

export type ProtocolTreeNode = ProtocolListItem & {
  author: User
  children: ProtocolTreeNode[]
}

export type ProtocolDiffEntry = {
  section: string
  path: string
  change_type: 'added' | 'removed' | 'modified'
  before: unknown
  after: unknown
}

export type ProtocolDiffResponse = {
  source_id: number
  target_id: number
  source_title: string
  target_title: string
  summary: Record<string, number>
  changes: ProtocolDiffEntry[]
}

export type Comment = {
  id: number
  protocol_id: number
  step_order: number | null
  author_id: number
  author: User
  content: string
  created_at: string
}

export type CommentCreate = {
  step_order?: number | null
  content: string
}

export type CommentWithProtocol = Comment & {
  protocol: ProtocolListItem
}

export type Pitfall = {
  id: number
  protocol_id: number
  step_order: number
  author_id: number
  author: User
  content: string
  created_at: string
}

export type PitfallCreate = {
  step_order: number
  content: string
}

export type ContributionEvent = {
  id: number
  user_id: number
  event_type: 'create_protocol' | 'fork_protocol' | 'protocol_forked_by_other' | 'update_protocol' | 'add_pitfall' | 'add_comment' | 'receive_star'
  score_delta: number
  protocol_id: number | null
  related_protocol_id: number | null
  description: string
  created_at: string
}

export type ContributionSummary = {
  user_id: number
  score: number
  events: ContributionEvent[]
}


export type ContributionProfileModule = {
  label: string
  value: number
}

export type ContributionProfile = {
  user_id: number
  name: string
  avatar: string
  avatar_config?: AvatarConfig
  protocol_publishing: ContributionProfileModule
  protocol_maintenance: ContributionProfileModule
  discussion: ContributionProfileModule
  impact: ContributionProfileModule[]
  special_contributions: ContributionProfileModule[]
}

export type ContributionProfileLeaderboardItem = {
  user_id: number
  name: string
  avatar: string
  avatar_config?: AvatarConfig
  value: number
}

export type ContributionProfileLeaderboards = {
  protocol_count: ContributionProfileLeaderboardItem[]
  update_count: ContributionProfileLeaderboardItem[]
  comment_count: ContributionProfileLeaderboardItem[]
  star_received_count: ContributionProfileLeaderboardItem[]
  forked_count: ContributionProfileLeaderboardItem[]
  commercial_protocol_count: ContributionProfileLeaderboardItem[]
  image_macro_count: ContributionProfileLeaderboardItem[]
  analysis_tool_count: ContributionProfileLeaderboardItem[]
  agent_skill_count: ContributionProfileLeaderboardItem[]
}

export type ContributionProfileLeaderboardMetric = keyof ContributionProfileLeaderboards

export type ProtocolStarSummary = {
  protocol_id: number
  star_count: number
  starred_by_me: boolean
}

export type ProtocolParseResponse = {
  title: string
  abstract: string
  structured: StructuredProtocol
  parser: string
  warnings: string[]
}

export type ProtocolFolder = {
  id: number
  owner_id: number
  parent_id: number | null
  name: string
  created_at: string
}

export type ProtocolFolderCreate = {
  name: string
  parent_id?: number | null
}

export type ProtocolFolderUpdate = {
  name?: string
  parent_id?: number | null
}

export type ProjectStats = {
  laboratory_protocols: number
  base_protocols: number
  user_protocols: number
  commercial_protocols: number
  image_macros: number
  analysis_tools: number
  agent_skills: number
  taxonomy_categories: number
}

export type CommercialProtocol = {
  id: string
  title: string
  manufacturer: string
  catalog_no: string
  description: string
  filename: string
  file_size: number
  author_id: number | null
  author_name: string
  preview_url: string
  download_url: string
  star_count: number
  starred_by_me: boolean
  created_at: string
}

