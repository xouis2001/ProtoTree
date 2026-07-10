import { formatLocalDateTime } from '../appUtils'
import { Avatar } from '../components/Avatar'
import type { CommentWithProtocol, ContributionProfile, User } from '../types'

export function ProfileCenter({ user, contributionProfile, receivedComments, onSelectProtocol }: { user: User; contributionProfile: ContributionProfile | null; receivedComments: CommentWithProtocol[]; onSelectProtocol: (id: number) => void }) {
  const safeReceivedComments = receivedComments ?? []
  const protocolCount = contributionProfile?.protocol_publishing.value ?? 0
  const maintainedCount = contributionProfile?.protocol_maintenance.value ?? 0
  const commentCount = contributionProfile?.discussion.value ?? 0
  const impactCount = contributionProfile ? contributionProfile.impact.reduce((total, item) => total + item.value, 0) : 0
  const summaryItems = contributionProfile ? [
    contributionProfile.protocol_publishing,
    contributionProfile.protocol_maintenance,
    contributionProfile.discussion,
    ...contributionProfile.impact,
    ...contributionProfile.special_contributions,
  ] : []

  return (
    <section className="profile-grid contribution-profile-grid">
      <div className="card profile-hero-card">
        <div className="profile-hero-identity">
          <Avatar value={user.avatar} config={user.avatar_config} size="large" label={user.name} />
          <div>
            <p className="eyebrow">Contribution Profile</p>
            <h2>{user.name}</h2>
            <p className="muted">{user.email}</p>
          </div>
        </div>
        <div className="profile-hero-stats">
          <span><strong>{protocolCount}</strong>发布</span>
          <span><strong>{maintainedCount}</strong>维护</span>
          <span><strong>{commentCount}</strong>讨论</span>
          <span><strong>{impactCount}</strong>影响</span>
        </div>
      </div>
      <div className="card profile-summary contribution-profile-summary">
        <div>
          <p className="eyebrow">数据总览</p>
          <h2>贡献指标</h2>
          <p className="muted">按事实行为拆分，不合并成单一分数。</p>
        </div>
        <div className="profile-metric-grid">
          {summaryItems.length === 0 && <p className="empty">暂无 Contribution Profile 数据。</p>}
          {summaryItems.map((item) => <article className="profile-metric" key={item.label}><strong>{item.value}</strong><span>{item.label}</span></article>)}
        </div>
      </div>
      <div className="card contribution-profile-card">
        <div>
          <p className="eyebrow">协作反馈</p>
          <h2>最近收到的评论</h2>
          <p className="muted">成员对你发布或维护的 Protocol 留下的反馈会集中显示在这里。</p>
        </div>
        <div className="event-list">
          {safeReceivedComments.length === 0 && <p className="empty">暂无收到的评论。</p>}
          {safeReceivedComments.map((comment) => (
            <button className="event-item profile-comment-item" type="button" key={comment.id} onClick={() => onSelectProtocol(comment.protocol_id)}>
              <strong>{comment.author.name} 评论了「{comment.protocol.title}」{comment.step_order ? `第 ${comment.step_order} 步` : ''}</strong>
              <span>{comment.content}</span>
              <span>{formatLocalDateTime(comment.created_at)}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
