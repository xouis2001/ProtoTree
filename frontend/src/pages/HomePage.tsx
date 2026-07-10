import { useMemo, useState } from 'react'
import { contributionProfileLeaderboardMetrics } from '../appConstants'
import { Avatar } from '../components/Avatar'
import { BrandLogo } from '../components/BrandLogo'
import type { ContributionProfileLeaderboardMetric, ContributionProfileLeaderboards, ProjectStats } from '../types'

type LeaderboardRow = {
  user_id: number
  name: string
  avatar: string
  avatar_config?: import('../types').AvatarConfig
} & Record<ContributionProfileLeaderboardMetric, number>

export function HomePage({ leaderboards, projectStats }: { leaderboards: ContributionProfileLeaderboards | null; projectStats: ProjectStats | null }) {
  const laboratoryProtocols = projectStats?.laboratory_protocols ?? 0
  const baseProtocols = projectStats?.base_protocols ?? 0
  const userProtocols = projectStats?.user_protocols ?? Math.max(laboratoryProtocols - baseProtocols, 0)
  const commercialProtocols = projectStats?.commercial_protocols ?? 0
  const publicResources = (projectStats?.image_macros ?? 0) + (projectStats?.analysis_tools ?? 0) + (projectStats?.agent_skills ?? 0)
  const totalProtocols = laboratoryProtocols + commercialProtocols
  const baseShare = formatPercent(baseProtocols, laboratoryProtocols)

  return (
    <>
      <section className="hero home-intro">
        <div className="hero-copy">
          <BrandLogo className="hero-accent-logo" variant="mark" />
          <p className="eyebrow">实验室 Protocol 协作知识库</p>
          <h1>实验室 Protocol 的协作知识库</h1>
          <p>ProtoTree 用 AI 将零散实验文本整理成步骤化 Protocol，并通过 Fork 关系、评论或踩坑经验和 Contribution Profile，帮助实验室持续沉淀可复用的实验经验。</p>
          <div className="hero-badges">
            <span>步骤化 Protocol</span>
            <span>Fork 关系追踪</span>
            <span>实验经验沉淀</span>
            <span>Contribution Profile</span>
          </div>
        </div>
      </section>
      <section className="home-grid">
        <div className="card home-feature-card">
          <h2>项目目标</h2>
          <p>把散落在个人文档、聊天记录和口头经验里的实验方案统一沉淀到一个可检索、可追踪、可讨论的实验室 Protocol 库中。</p>
        </div>
        <div className="card home-feature-card">
          <h2>核心流程</h2>
          <p>上传或粘贴原始 SOP，AI 按步骤规范表达；成员可以 Fork 形成新分支，并围绕每一步添加评论或踩坑经验。</p>
        </div>
      </section>
      <section className="card project-stats-card project-stats-card-detailed">
        <div className="project-stats-copy">
          <p className="eyebrow">项目集成</p>
          <h2>当前知识库规模</h2>
          <p className="muted">实时汇总公共基础库、成员贡献、商品化试剂和数据处理资源，让库的增长结构更清楚。</p>
          <div className="project-stats-summary">
            <strong>{totalProtocols}</strong>
            <span>条 Protocol 已纳入知识库</span>
          </div>
          <div className="project-stats-breakdown">
            <span>公共基础库占实验室 Protocol {baseShare}</span>
            <span>{projectStats?.taxonomy_categories ?? 0} 个一级分类</span>
          </div>
        </div>
        <div className="project-stats-grid">
          <article><strong>{laboratoryProtocols}</strong><span>实验室 Protocol</span><em>可搜索、可 Fork、可评论</em></article>
          <article><strong>{baseProtocols}</strong><span>公共基础库</span><em>Protocol Book 导入内容</em></article>
          <article><strong>{userProtocols}</strong><span>成员贡献 Protocol</span><em>由成员新建或 Fork 沉淀</em></article>
          <article><strong>{commercialProtocols}</strong><span>商品化试剂 Protocol</span><em>集中保存厂家 PDF</em></article>
          <article><strong>{publicResources}</strong><span>数据处理资源</span><em>Macro、分析工具、Agent Skill</em></article>
          <article><strong>{totalProtocols}</strong><span>Protocol 总量</span><em>实验室库 + 商品化试剂</em></article>
        </div>
      </section>
      <WideLeaderboard title="多指标榜" description="每行展示全部 Contribution Profile 指标，默认按发布 Protocol 总数排序，也可以切换为其他指标排序。" data={leaderboards} emptyText="暂无 Contribution Profile 榜单数据。" />
    </>
  )
}

function formatPercent(value: number, total: number) {
  if (!total) {
    return '0%'
  }
  return `${Math.round((value / total) * 100)}%`
}

function WideLeaderboard({ title, description, data, emptyText }: { title: string; description: string; data: ContributionProfileLeaderboards | null; emptyText: string }) {
  const [metric, setMetric] = useState<ContributionProfileLeaderboardMetric>('protocol_count')
  const rows = useMemo(() => buildWideRows(data, metric), [data, metric])

  return (
    <section className="card leaderboard-card leaderboard-card-wide contribution-wide-card">
      <div className="wide-leaderboard-header">
        <div>
          <p className="eyebrow">Contribution Profile</p>
          <h2>{title}</h2>
          <p className="muted">{description}</p>
        </div>
        <label className="leaderboard-sort-select">排序指标<select value={metric} onChange={(event) => setMetric(event.target.value as ContributionProfileLeaderboardMetric)}>{contributionProfileLeaderboardMetrics.map((item) => <option value={item.key} key={item.key}>{item.label}</option>)}</select></label>
      </div>
      <div className="wide-leaderboard-table-wrap">
        <table className="wide-leaderboard-table">
          <thead>
            <tr>
              <th>排名</th>
              <th>成员</th>
              {contributionProfileLeaderboardMetrics.map((item) => <th className={metric === item.key ? 'active' : ''} key={item.key}>{item.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={contributionProfileLeaderboardMetrics.length + 2}>{emptyText}</td></tr>}
            {rows.map((row, index) => (
              <tr key={row.user_id}>
                <td>#{index + 1}</td>
                <td><span className="wide-leaderboard-user"><Avatar value={row.avatar} config={row.avatar_config} size="medium" label={row.name} /><strong>{row.name}</strong></span></td>
                {contributionProfileLeaderboardMetrics.map((item) => <td className={metric === item.key ? 'active' : ''} key={item.key}>{row[item.key]} {item.unit}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function buildWideRows(data: ContributionProfileLeaderboards | null, metric: ContributionProfileLeaderboardMetric): LeaderboardRow[] {
  if (!data) {
    return []
  }
  const rows = new Map<number, LeaderboardRow>()
  for (const metricItem of contributionProfileLeaderboardMetrics) {
    for (const item of data[metricItem.key] ?? []) {
      const existing = rows.get(item.user_id) ?? {
        user_id: item.user_id,
        name: item.name,
        avatar: item.avatar,
        avatar_config: item.avatar_config,
        protocol_count: 0,
        update_count: 0,
        comment_count: 0,
        star_received_count: 0,
        forked_count: 0,
        commercial_protocol_count: 0,
        image_macro_count: 0,
        analysis_tool_count: 0,
        agent_skill_count: 0,
      }
      existing[metricItem.key] = item.value
      rows.set(item.user_id, existing)
    }
  }
  return [...rows.values()].sort((left, right) => right[metric] - left[metric] || left.name.localeCompare(right.name) || left.user_id - right.user_id)
}
