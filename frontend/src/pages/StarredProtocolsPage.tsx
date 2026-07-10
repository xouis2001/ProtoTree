import { formatLocalDateTime } from '../appUtils'
import { Icon } from '../components/Icon'
import type { CommercialProtocol, ProtocolListItem } from '../types'

export function StarredProtocolsPage({ protocols, commercialProtocols, onSelectProtocol, onSelectCommercialProtocol }: { protocols: ProtocolListItem[]; commercialProtocols: CommercialProtocol[]; onSelectProtocol: (id: number) => void; onSelectCommercialProtocol: (id: string) => void }) {
  const safeProtocols = protocols ?? []
  const safeCommercialProtocols = commercialProtocols ?? []
  const total = safeProtocols.length + safeCommercialProtocols.length

  return (
    <section className="starred-page">
      <div className="card starred-protocols-card">
        <div className="starred-page-header">
          <div>
            <p className="eyebrow">快速回访</p>
            <h2>我的收藏 Protocol</h2>
            <p className="muted">汇总你曾经送过小星星的实验 Protocol 和商品化试剂 PDF，方便后续快速找回。</p>
          </div>
          <span>{total} 条收藏</span>
        </div>
        <div className="event-list starred-protocol-list">
          {total === 0 && <div className="starred-empty-state"><strong>暂无收藏 Protocol</strong><span>在 Protocol 或商品化试剂详情页送出小星星后，它会出现在这里。</span></div>}
          {safeProtocols.map((protocol) => {
            const category = protocol.structured?.experiment_category || protocol.structured?.experiment_type || '未分类'
            const tags = Array.isArray(protocol.structured?.tags) && protocol.structured.tags.length ? protocol.structured.tags : protocol.structured?.experiment_subtype ? [protocol.structured.experiment_subtype] : []
            return (
              <button className="event-item starred-protocol-item" type="button" key={protocol.id} onClick={() => onSelectProtocol(protocol.id)}>
                <strong>{protocol.title}</strong>
                <span>{category}{tags.length ? ` · ${tags.slice(0, 3).join(' / ')}` : ''}</span>
                <span><Icon name="star" size={14} /> {protocol.star_count} · {protocol.author.name} · {formatLocalDateTime(protocol.created_at)}</span>
              </button>
            )
          })}
          {safeCommercialProtocols.map((protocol) => (
            <button className="event-item starred-protocol-item" type="button" key={`commercial-${protocol.id}`} onClick={() => onSelectCommercialProtocol(protocol.id)}>
              <strong>{protocol.title}</strong>
              <span>商品化试剂 PDF · {protocol.manufacturer || '未知厂家'}{protocol.catalog_no ? ` · ${protocol.catalog_no}` : ''}</span>
              <span><Icon name={protocol.starred_by_me ? 'star-filled' : 'star'} size={14} /> {protocol.star_count} · {protocol.author_name || '未知上传者'} · {formatLocalDateTime(protocol.created_at)}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
