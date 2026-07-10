import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { API_BASE_URL, deleteCommercialProtocol, downloadFile, listCommercialProtocols, starCommercialProtocol, unstarCommercialProtocol } from '../api'
import { formatLocalDateTime } from '../appUtils'
import { Icon } from '../components/Icon'
import type { CommercialProtocol, User } from '../types'

export function CommercialProtocolsPage({ user }: { user: User }) {
  const navigate = useNavigate()
  const [items, setItems] = useState<CommercialProtocol[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [manufacturerFilter, setManufacturerFilter] = useState('')
  const manufacturers = useMemo(() => Array.from(new Set(items.map((item) => item.manufacturer).filter(Boolean))).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN')), [items])
  const filteredItems = useMemo(() => {
    const keyword = query.trim().toLowerCase()
    return items.filter((item) => {
      const matchesManufacturer = !manufacturerFilter || item.manufacturer === manufacturerFilter
      const text = [item.title, item.manufacturer, item.catalog_no, item.description, item.author_name].join(' ').toLowerCase()
      const matchesKeyword = !keyword || text.includes(keyword)
      return matchesManufacturer && matchesKeyword
    })
  }, [items, manufacturerFilter, query])
  const selected = useMemo(() => filteredItems.find((item) => item.id === selectedId) ?? filteredItems[0] ?? null, [filteredItems, selectedId])

  async function refresh() {
    setIsLoading(true)
    try {
      const nextItems = await listCommercialProtocols()
      setItems(nextItems)
      setSelectedId((current) => current && nextItems.some((item) => item.id === current) ? current : nextItems[0]?.id ?? null)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '加载商品化试剂 Protocol 失败')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('确认删除这个商品化试剂 Protocol？')) {
      return
    }
    setMessage('')
    try {
      await deleteCommercialProtocol(id)
      const nextItems = items.filter((item) => item.id !== id)
      setItems(nextItems)
      setSelectedId(nextItems[0]?.id ?? null)
      setMessage('已删除')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '删除失败')
    }
  }

  async function handleDownload(item: CommercialProtocol) {
    setMessage('')
    try {
      await downloadFile(item.download_url, item.filename)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '下载失败')
    }
  }

  async function handleToggleStar(item: CommercialProtocol) {
    setMessage('')
    try {
      const summary = item.starred_by_me ? await unstarCommercialProtocol(item.id) : await starCommercialProtocol(item.id)
      setItems((currentItems) => currentItems.map((current) => current.id === item.id ? { ...current, star_count: summary.star_count, starred_by_me: summary.starred_by_me } : current))
      setMessage(summary.starred_by_me ? '已送上小星星' : '已取消小星星')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '小星星操作失败')
    }
  }

  function handleOpenItem(item: CommercialProtocol) {
    setSelectedId(item.id)
    if (window.matchMedia('(max-width: 900px)').matches) {
      navigate(`/commercial-protocols/${item.id}`)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  return (
    <section className="commercial-page">
      <div className="commercial-header card">
        <div>
          <p className="eyebrow">商品化试剂 Protocol</p>
          <h2>试剂说明书 PDF Protocol 库</h2>
          <p className="muted">用于集中存放商品化试剂随附的 PDF 版 Protocol，可在线预览并下载原始 PDF。</p>
        </div>
        <div className="action-row">
          <button className="primary" type="button" onClick={() => navigate('/commercial-protocols/new')}>上传商品化 Protocol</button>
          <button className="secondary" type="button" onClick={() => { void refresh() }}>{isLoading ? '加载中...' : '刷新'}</button>
        </div>
      </div>
      {message && <div className="app-message success inline-message">{message}</div>}
      <section className="card commercial-filter-card">
        <div className="commercial-filter-grid">
          <label className="filter-field">
            <span>关键词检索</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索标题、厂家、货号或说明" />
          </label>
          <label className="filter-field commercial-manufacturer-select">
            <span>试剂厂家</span>
            <select value={manufacturerFilter} onChange={(event) => setManufacturerFilter(event.target.value)}>
              <option value="">全部厂家</option>
              {manufacturers.map((manufacturer) => <option value={manufacturer} key={manufacturer}>{manufacturer}</option>)}
            </select>
          </label>
        </div>
      </section>
      <section className="commercial-grid">
        <div className="card commercial-list-card">
          <h3>PDF Protocol 列表</h3>
          {items.length === 0 && <div className="resource-empty-state commercial-upload-empty"><strong>暂无商品化试剂 Protocol</strong><span>上传试剂说明书或试剂盒 PDF 后，可在这里预览和下载。</span><button className="primary compact-button" type="button" onClick={() => navigate('/commercial-protocols/new')}>上传 PDF</button></div>}
          {items.length > 0 && filteredItems.length === 0 && <p className="empty">没有匹配当前检索条件的商品化试剂 Protocol。</p>}
          <div className="commercial-list">
            {filteredItems.map((item) => (
              <button className={`commercial-item ${selected?.id === item.id ? 'active' : ''}`} type="button" key={item.id} onClick={() => handleOpenItem(item)}>
                <strong>{item.title}</strong>
                <span>{item.manufacturer || '未知厂家'}{item.catalog_no ? ` · ${item.catalog_no}` : ''}</span>
                <small><Icon name={item.starred_by_me ? 'star-filled' : 'star'} size={13} style={{ color: item.starred_by_me ? '#f59e0b' : undefined }} /> {item.star_count} · 上传者：{item.author_name || '未知上传者'} · {formatLocalDateTime(item.created_at)}</small>
              </button>
            ))}
          </div>
        </div>
        <div className="card commercial-preview-card">
          {!selected ? (
            <div className="resource-empty-state commercial-upload-empty"><strong>请选择一个 PDF Protocol</strong><span>也可以先上传新的商品化试剂 PDF。</span><button className="primary compact-button" type="button" onClick={() => navigate('/commercial-protocols/new')}>上传 PDF</button></div>
          ) : (
            <>
              <div className="commercial-preview-header">
                <div>
                  <p className="eyebrow">PDF 预览</p>
                  <h3>{selected.title}</h3>
                  <p className="muted">{selected.manufacturer || '未知厂家'}{selected.catalog_no ? ` · ${selected.catalog_no}` : ''} · 上传者：{selected.author_name || '未知上传者'}</p>
                  {selected.description && <p>{selected.description}</p>}
                  <div className="star-summary"><span><Icon name={selected.starred_by_me ? 'star-filled' : 'star'} size={16} style={{ color: selected.starred_by_me ? '#f59e0b' : undefined }} /> {selected.star_count} 颗小星星</span><button className={selected.starred_by_me ? 'star-button active' : 'star-button'} type="button" onClick={() => { void handleToggleStar(selected) }}><Icon name={selected.starred_by_me ? 'star-filled' : 'star'} size={16} /> {selected.starred_by_me ? '已送星星' : '送上小星星'}</button></div>
                </div>
                <div className="action-row">
                  <button className="primary" type="button" onClick={() => navigate(`/commercial-protocols/${selected.id}`)}>打开预览页</button>
                  <button className="secondary" type="button" onClick={() => { void handleDownload(selected) }}>下载 PDF</button>
                  {(user.is_admin || selected.author_id === user.id) && <button className="danger" type="button" onClick={() => { void handleDelete(selected.id) }}>删除</button>}
                </div>
              </div>
              <iframe className="commercial-pdf-frame" title={selected.title} src={`${API_BASE_URL}${selected.preview_url}`} />
            </>
          )}
        </div>
      </section>
    </section>
  )
}

export function CommercialProtocolDetailPage({ user }: { user: User }) {
  const navigate = useNavigate()
  const params = useParams()
  const protocolId = params.id ?? ''
  const [items, setItems] = useState<CommercialProtocol[]>([])
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const selected = useMemo(() => items.find((item) => item.id === protocolId) ?? null, [items, protocolId])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setIsLoading(true)
      try {
        const nextItems = await listCommercialProtocols()
        if (!cancelled) {
          setItems(nextItems)
        }
      } catch (error) {
        if (!cancelled) {
          setMessage(error instanceof Error ? error.message : '加载商品化试剂 Protocol 失败')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleDownload(item: CommercialProtocol) {
    setMessage('')
    try {
      await downloadFile(item.download_url, item.filename)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '下载失败')
    }
  }

  async function handleDelete(item: CommercialProtocol) {
    if (!window.confirm('确认删除这个商品化试剂 Protocol？')) {
      return
    }
    setMessage('')
    try {
      await deleteCommercialProtocol(item.id)
      setMessage('已删除')
      navigate('/commercial-protocols')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '删除失败')
    }
  }

  async function handleToggleStar(item: CommercialProtocol) {
    setMessage('')
    try {
      const summary = item.starred_by_me ? await unstarCommercialProtocol(item.id) : await starCommercialProtocol(item.id)
      setItems((currentItems) => currentItems.map((current) => current.id === item.id ? { ...current, star_count: summary.star_count, starred_by_me: summary.starred_by_me } : current))
      setMessage(summary.starred_by_me ? '已送上小星星' : '已取消小星星')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '小星星操作失败')
    }
  }

  return (
    <section className="commercial-detail-page">
      {message && <div className="app-message success inline-message">{message}</div>}
      <section className="card commercial-preview-card commercial-detail-preview">
        {isLoading && <div className="resource-empty-state commercial-upload-empty"><strong>正在加载 PDF 预览</strong><span>请稍候。</span></div>}
        {!isLoading && !selected && <div className="resource-empty-state commercial-upload-empty"><strong>未找到这个 PDF Protocol</strong><span>它可能已被删除，或当前链接不正确。</span><button className="primary compact-button" type="button" onClick={() => navigate('/commercial-protocols')}>返回列表</button></div>}
        {selected && (
          <>
            <div className="commercial-pdf-toolbar">
              <span>如果当前浏览器无法内嵌预览，可直接打开或下载 PDF。</span>
              <div className="action-row">
                <a className="button-link secondary" href={`${API_BASE_URL}${selected.preview_url}`} target="_blank" rel="noreferrer">打开 PDF</a>
                <button className="primary" type="button" onClick={() => { void handleDownload(selected) }}>下载 PDF</button>
              </div>
            </div>
            <iframe className="commercial-pdf-frame commercial-detail-pdf-frame" title={selected.title} src={`${API_BASE_URL}${selected.preview_url}`} />
          </>
        )}
      </section>
      <div className="commercial-preview-header card commercial-detail-header">
        <div>
          <p className="eyebrow">商品化试剂 Protocol</p>
          <h2>{selected?.title ?? (isLoading ? '正在加载 PDF Protocol' : '未找到这个 Protocol')}</h2>
          {selected && <p className="muted">{selected.manufacturer || '未知厂家'}{selected.catalog_no ? ` · ${selected.catalog_no}` : ''} · 上传者：{selected.author_name || '未知上传者'} · {formatLocalDateTime(selected.created_at)}</p>}
          {selected?.description && <p>{selected.description}</p>}
          {selected && <div className="star-summary"><span><Icon name={selected.starred_by_me ? 'star-filled' : 'star'} size={16} style={{ color: selected.starred_by_me ? '#f59e0b' : undefined }} /> {selected.star_count} 颗小星星</span><button className={selected.starred_by_me ? 'star-button active' : 'star-button'} type="button" onClick={() => { void handleToggleStar(selected) }}><Icon name={selected.starred_by_me ? 'star-filled' : 'star'} size={16} /> {selected.starred_by_me ? '已送星星' : '送上小星星'}</button></div>}
        </div>
        <div className="action-row">
          <button className="secondary" type="button" onClick={() => navigate('/commercial-protocols')}>返回列表</button>
          {selected && <button className="primary" type="button" onClick={() => { void handleDownload(selected) }}>下载 PDF</button>}
          {selected && (user.is_admin || selected.author_id === user.id) && <button className="danger" type="button" onClick={() => { void handleDelete(selected) }}>删除</button>}
        </div>
      </div>
    </section>
  )
}
