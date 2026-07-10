import type { Protocol, ProtocolFolder, ProtocolListItem, ProtocolTreeNode, StructuredProtocol, StructuredStep } from './types'
import { avatarColors } from './appConstants'

export function formatLocalDateTime(value: string) {
  const normalized = /Z$|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(normalized))
}

export type FolderTreeItem = ProtocolFolder & { children: FolderTreeItem[] }

export function buildFolderTree(folders: ProtocolFolder[] = [], parentId: number | null = null): FolderTreeItem[] {
  return folders
    .filter((folder) => folder.parent_id === parentId)
    .sort((left, right) => left.name.localeCompare(right.name))
    .map((folder) => ({ ...folder, children: buildFolderTree(folders, folder.id) }))
}

export function flattenFolderOptions(folder: FolderTreeItem, depth = 0): { id: number; name: string; depth: number }[] {
  return [{ id: folder.id, name: folder.name, depth }, ...folder.children.flatMap((child) => flattenFolderOptions(child, depth + 1))]
}

export function parseAvatar(value: string) {
  const [color = '#2563eb', pattern = '1111100110011111'] = value.split('|')
  return { color, pattern: pattern.padEnd(16, '0').slice(0, 16) }
}

export function buildAvatarWithColor(color: string, avatar: string) {
  return `${color}|${parseAvatar(avatar).pattern}`
}

export function getFirstAvailableAvatarColor(usedColors: string[]) {
  const usedSet = new Set(usedColors.map((color) => color.toLowerCase()))
  return avatarColors.find((color) => !usedSet.has(color.toLowerCase())) ?? avatarColors[0]
}

export function normalizeSteps(structured: StructuredProtocol): StructuredStep[] {
  const steps = Array.isArray(structured.steps) ? structured.steps : []
  return steps.map((step, index) => ({ ...step, order: step.order ?? index + 1 }))
}

export function stripStepPrefix(value: string) {
  return value.replace(/^第?\s*\d+\s*[步.、:：-]?\s*/i, '').replace(/^step\s*\d+\s*[.、:：-]?\s*/i, '')
}

export function formatParameters(parameters: StructuredStep['parameters']) {
  if (!parameters) {
    return ''
  }
  if (typeof parameters === 'string') {
    return parameters
  }
  return Object.entries(parameters).map(([key, value]) => `${key}: ${value}`).join('；')
}

export function parseParametersText(value: string): Record<string, string> | string {
  if (!value.includes(':') && !value.includes('：')) {
    return value
  }
  return value.split(/[；;]/).reduce<Record<string, string>>((result, item) => {
    const [rawKey, ...rawValue] = item.split(/[:：]/)
    const key = rawKey?.trim()
    const nextValue = rawValue.join(':').trim()
    if (key && nextValue) {
      result[key] = nextValue
    }
    return result
  }, {})
}

export function getProtocolExperimentPrimary(protocol: ProtocolListItem | Protocol) {
  return protocol.structured?.experiment_type ?? ''
}

export function getProtocolExperimentSubtype(protocol: ProtocolListItem | Protocol) {
  return protocol.structured?.experiment_subtype ?? ''
}

export function getProtocolExperimentType(protocol: ProtocolListItem | Protocol) {
  const primary = getProtocolExperimentPrimary(protocol)
  const subtype = getProtocolExperimentSubtype(protocol)
  if (primary) {
    return `${primary}${subtype ? ` / ${subtype}` : ''}`
  }
  return protocol.parent_id ? 'Fork Protocol' : '原创 Protocol'
}

export function getProtocolForkCount(protocol: ProtocolListItem, protocols: ProtocolListItem[]) {
  return protocols.filter((item) => item.parent_id === protocol.id).length
}

export function getProtocolUsageCount(protocol: ProtocolListItem, protocols: ProtocolListItem[]) {
  const rootId = protocol.root_id ?? protocol.id
  return protocols.filter((item) => (item.root_id ?? item.id) === rootId).length
}

export function flattenTree(tree: ProtocolTreeNode): ProtocolTreeNode[] {
  return [tree, ...tree.children.flatMap((child) => flattenTree(child))]
}

export function getLineage(nodes: ProtocolTreeNode[], selected: ProtocolTreeNode) {
  const lineage: ProtocolTreeNode[] = []
  let current: ProtocolTreeNode | undefined = selected
  while (current) {
    lineage.unshift(current)
    current = current.parent_id ? nodes.find((node) => node.id === current?.parent_id) : undefined
  }
  return lineage
}

export function sanitizeRichTextHtml(value: string) {
  const template = document.createElement('template')
  template.innerHTML = value
  const allowedTags = new Set(['B', 'STRONG', 'I', 'EM', 'U', 'P', 'BR', 'DIV', 'SPAN', 'FONT', 'UL', 'OL', 'LI', 'TABLE', 'TBODY', 'THEAD', 'TR', 'TD', 'TH'])
  const allowedStyles = new Set(['color', 'text-align', 'font-weight', 'font-style', 'text-decoration'])
  template.content.querySelectorAll('*').forEach((element) => {
    if (!allowedTags.has(element.tagName)) {
      element.replaceWith(...Array.from(element.childNodes))
      return
    }
    Array.from(element.attributes).forEach((attribute) => {
      if (attribute.name === 'style') {
        const nextStyle = attribute.value.split(';').map((item) => item.trim()).filter((item) => {
          const [name] = item.split(':')
          return allowedStyles.has(name.trim().toLowerCase())
        }).join('; ')
        if (nextStyle) {
          element.setAttribute('style', nextStyle)
        } else {
          element.removeAttribute('style')
        }
      } else if (element.tagName === 'FONT' && attribute.name === 'color') {
        return
      } else {
        element.removeAttribute(attribute.name)
      }
    })
  })
  return template.innerHTML
}

export function isErrorMessage(value: string) {
  return /失败|错误|异常|无效|不能|不存在|请输入|请先|not found|error|failed/i.test(value)
}

