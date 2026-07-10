import { CSSProperties, FormEvent, useState } from 'react'
import type { FolderForm } from '../appTypes'
import { buildFolderTree, formatLocalDateTime, type FolderTreeItem } from '../appUtils'
import { FolderSelect } from '../components/FolderSelect'
import { Icon } from '../components/Icon'
import type { ProtocolFolder, ProtocolListItem } from '../types'

export function MyProtocolLibrary({ protocols, folders, selectedId, onSelectProtocol, onCreateFolder, onRenameFolder, onDeleteFolder, onMoveProtocol }: { protocols: ProtocolListItem[]; folders: ProtocolFolder[]; selectedId: number | null; onSelectProtocol: (id: number) => void; onCreateFolder: (payload: FolderForm) => Promise<boolean>; onRenameFolder: (folder: ProtocolFolder, name: string) => void; onDeleteFolder: (folder: ProtocolFolder) => void; onMoveProtocol: (protocolId: number, folderId: number | null) => void }) {
  const [selectedFolderId, setSelectedFolderId] = useState<number | null | 'all'>('all')
  const [folderForm, setFolderForm] = useState<FolderForm>({ name: '', parent_id: null })
  const [query, setQuery] = useState('')
  const safeProtocols = protocols ?? []
  const safeFolders = folders ?? []
  const visibleProtocols = safeProtocols.filter((protocol) => selectedFolderId === 'all' ? true : protocol.folder_id === selectedFolderId).filter((protocol) => `${protocol.title} ${protocol.abstract}`.toLowerCase().includes(query.toLowerCase()))
  const currentFolder = typeof selectedFolderId === 'number' ? safeFolders.find((folder) => folder.id === selectedFolderId) ?? null : null
  const uncategorizedCount = safeProtocols.filter((protocol) => protocol.folder_id === null).length

  async function submitFolder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!folderForm.name.trim()) {
      return
    }
    const created = await onCreateFolder(folderForm)
    if (created) {
      setFolderForm({ name: '', parent_id: typeof selectedFolderId === 'number' ? selectedFolderId : null })
    }
  }

  return (
    <section className="my-library-layout">
      <aside className="card folder-panel">
        <div className="folder-panel-header">
          <div>
            <p className="eyebrow">我的 Protocol 库</p>
            <h2>分级文件夹</h2>
          </div>
          <span>{safeFolders.length} 个文件夹</span>
        </div>
        <form className="folder-form" onSubmit={submitFolder}>
          <input value={folderForm.name} onChange={(event) => setFolderForm({ ...folderForm, name: event.target.value })} placeholder="新文件夹名称" />
          <FolderSelect folders={folders} value={folderForm.parent_id} onChange={(folderId) => setFolderForm({ ...folderForm, parent_id: folderId })} label="父级文件夹" />
          <button className="primary" type="submit">新建文件夹</button>
        </form>
        <div className="folder-tree">
          <button className={`folder-tree-item folder-shortcut ${selectedFolderId === 'all' ? 'active' : ''}`} type="button" onClick={() => { setSelectedFolderId('all'); setFolderForm({ ...folderForm, parent_id: null }) }}><span className="folder-icon has-children" /><span className="folder-name">全部 Protocol</span><span className="folder-child-count">{safeProtocols.length}</span></button>
          <button className={`folder-tree-item folder-shortcut ${selectedFolderId === null ? 'active' : ''}`} type="button" onClick={() => { setSelectedFolderId(null); setFolderForm({ ...folderForm, parent_id: null }) }}><span className="folder-icon" /><span className="folder-name">未分类</span><span className="folder-child-count">{uncategorizedCount}</span></button>
          {buildFolderTree(folders).map((folder) => <FolderTreeNode key={folder.id} node={folder} selectedFolderId={selectedFolderId} setSelectedFolderId={(id) => { setSelectedFolderId(id); setFolderForm({ ...folderForm, parent_id: id }) }} depth={0} />)}
        </div>
      </aside>
      <section className="card my-library-main">
        <div className="section-heading">
          <div><p className="eyebrow">当前文件夹</p><h2>{selectedFolderId === 'all' ? '全部 Protocol' : currentFolder?.name ?? '未分类'}</h2></div>
          {currentFolder && <div className="action-row"><button className="secondary" type="button" onClick={() => onRenameFolder(currentFolder, window.prompt('新的文件夹名称', currentFolder.name) ?? currentFolder.name)}>重命名</button><button className="danger" type="button" onClick={() => onDeleteFolder(currentFolder)}>删除文件夹</button></div>}
        </div>
        <div className="my-library-toolbar">
          <label>
            搜索
            <input className="library-search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索我的 Protocol" />
          </label>
          <div className="my-library-counts">
            <span>{visibleProtocols.length} 条当前结果</span>
            <span>{safeProtocols.length} 条个人 Protocol</span>
          </div>
        </div>
        <div className="my-protocol-list">
          {visibleProtocols.length === 0 && <div className="my-library-empty"><strong>当前文件夹没有 Protocol</strong><span>换一个文件夹，或新建 / Fork 一个 Protocol 后再归档。</span></div>}
          {visibleProtocols.map((protocol) => {
            const category = protocol.structured?.experiment_category || protocol.structured?.experiment_type || '未分类'
            return (
              <article className={`my-protocol-item ${protocol.id === selectedId ? 'active' : ''}`} key={protocol.id}>
                <button type="button" onClick={() => onSelectProtocol(protocol.id)}>
                  <strong>{protocol.title}</strong>
                  <p>{protocol.abstract || '暂无摘要'}</p>
                  <span><Icon name="star" size={12} /> {protocol.star_count} · {category} · {formatLocalDateTime(protocol.created_at)}</span>
                </button>
                <label className="my-protocol-move">
                  移动到
                  <FolderSelect folders={safeFolders} value={protocol.folder_id} onChange={(folderId) => onMoveProtocol(protocol.id, folderId)} />
                </label>
              </article>
            )
          })}
        </div>
      </section>
    </section>
  )
}

function FolderTreeNode({ node, selectedFolderId, setSelectedFolderId, depth }: { node: FolderTreeItem; selectedFolderId: number | null | 'all'; setSelectedFolderId: (id: number) => void; depth: number }) {
  const treeStyle = { '--folder-depth': depth } as CSSProperties
  return (
    <div className="folder-tree-node" style={treeStyle}>
      <div className="folder-tree-row">
        {depth > 0 && <span className="folder-branch" />}
        <button className={`folder-tree-item ${selectedFolderId === node.id ? 'active' : ''}`} type="button" onClick={() => setSelectedFolderId(node.id)}><span className={node.children.length > 0 ? 'folder-icon has-children' : 'folder-icon'} /><span className="folder-name">{node.name}</span>{node.children.length > 0 && <span className="folder-child-count">{node.children.length}</span>}</button>
      </div>
      {node.children.length > 0 && <div className="folder-tree-children">{node.children.map((child) => <FolderTreeNode key={child.id} node={child} selectedFolderId={selectedFolderId} setSelectedFolderId={setSelectedFolderId} depth={depth + 1} />)}</div>}
    </div>
  )
}
