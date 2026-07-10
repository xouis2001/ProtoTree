import type { ProtocolListSort, StructuredProtocol } from './types'

export type ProtocolEditForm = {
  title: string
  abstract: string
  raw_text: string
  version_label: string
  folder_id: number | null
  structured: StructuredProtocol
}

export type ForkForm = ProtocolEditForm

export type FolderForm = {
  name: string
  parent_id: number | null
}

export type LibraryFilters = {
  q: string
  author_id: number | ''
  experiment_type: string
  experiment_subtype: string
  experiment_category: string
  tag_groups: string[]
  tags: string[]
  sort: ProtocolListSort
  page: number
  page_size: number
}

export type AuthMode = 'login' | 'register'

export type RegisterStep = 'info' | 'avatar'

