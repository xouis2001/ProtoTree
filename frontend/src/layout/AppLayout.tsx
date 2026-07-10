import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { isErrorMessage } from '../appUtils'
import { Avatar } from '../components/Avatar'
import { BrandLogo } from '../components/BrandLogo'
import { Icon } from '../components/Icon'
import type { User } from '../types'

export function AppLayout({ user, message }: { user: User; message: string }) {
  const location = useLocation()
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false)

  useEffect(() => {
    setIsMobileNavOpen(false)
  }, [location.pathname])

  const rootNavItems = [
    { href: '/index.html', label: '首页' },
    { href: '/reservation.html', label: '仪器预约' },
    { href: '/reagent.html', label: '试剂订购' },
    { href: '/schedule.html', label: '排班查询' },
    { href: '/cashbook.html', label: '现金账' },
    { href: '/protocol/', label: 'Protocol 共享', active: true },
  ]


  return (
    <>
      <nav className="lulab-site-nav prototree-root-nav">
        <div className="nav-links">
          {rootNavItems.map((item) => (
            <a key={item.href} href={item.href} className={item.active ? 'active' : undefined}>{item.label}</a>
          ))}
        </div>
        <div className="lulab-auth-area">
          <span className="lulab-user-chip">
            <a className="lulab-profile-link" href="/profile.html" aria-label="个人资料">
              <span className="lulab-avatar" aria-hidden="true">
                <Avatar value={user.avatar} config={user.avatar_config} size="small" label={user.name} />
              </span>
              <span className="lulab-user-name">{user.name}</span>
            </a>
          </span>
        </div>
      </nav>
      <main className="app-shell">
      <aside className={`sidebar ${isMobileNavOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-topbar">
          <div className="sidebar-brand">
            <div className="sidebar-logo-wrap">
              <BrandLogo className="sidebar-logo" variant="mark" />
            </div>
            <div className="sidebar-brand-text">
              <h1>ProtoTree</h1>
              <span>实验室 Protocol 协作知识库</span>
            </div>
          </div>
          <button
            className="mobile-nav-toggle"
            type="button"
            aria-label={isMobileNavOpen ? '关闭导航' : '打开导航'}
            aria-expanded={isMobileNavOpen}
            onClick={() => setIsMobileNavOpen((open) => !open)}
          >
            <Icon name={isMobileNavOpen ? 'close' : 'menu'} size={20} />
          </button>
        </div>
        <div className="sidebar-user">
          <Avatar value={user.avatar} config={user.avatar_config} size="medium" label={user.name} />
          <div className="sidebar-user-info">
            <strong>{user.name}</strong>
            <span>Contribution Profile</span>
          </div>
        </div>
        <div className="sidebar-section">
          <p className="sidebar-section-title">浏览</p>
          <nav className="side-nav">
            <NavLink to="/" end><Icon name="home" size={16} /> 主页</NavLink>
            <NavLink to="/library"><Icon name="library" size={16} /> 实验室Protocol库</NavLink>
            <NavLink to="/commercial-protocols"><Icon name="reagent" size={16} /> 商品化试剂 Protocol</NavLink>
          </nav>
        </div>
        <div className="sidebar-section">
          <p className="sidebar-section-title">创作</p>
          <nav className="side-nav">
            <NavLink to="/create"><Icon name="edit" size={16} /> 新建 Protocol</NavLink>
            <NavLink to="/upload-protocol"><Icon name="upload" size={16} /> 上传 Word/PDF</NavLink>
            <NavLink to="/commercial-protocols/new"><Icon name="reagent" size={16} /> 上传商品化试剂</NavLink>
            <NavLink to="/fork-protocol"><Icon name="fork" size={16} /> Fork Protocol</NavLink>
          </nav>
        </div>
        <div className="sidebar-section">
          <p className="sidebar-section-title">其他公共资源</p>
          <nav className="side-nav">
            <NavLink to="/resources/data-processing"><Icon name="chart" size={16} /> 数据处理</NavLink>
            <NavLink to="/resources/agent-skills"><Icon name="sparkles" size={16} /> Agent Skill</NavLink>
          </nav>
        </div>
        <div className="sidebar-section">
          <p className="sidebar-section-title">个人</p>
          <nav className="side-nav">
            <NavLink to="/profile"><Icon name="user" size={16} /> 个人中心</NavLink>
            <NavLink to="/my-library"><Icon name="folder" size={16} /> 我的 Protocol</NavLink>
            <NavLink to="/starred-protocols"><Icon name="star" size={16} /> 我的收藏</NavLink>
          </nav>
        </div>
      </aside>
      <section className="content">
        {message && <div className={`app-message ${isErrorMessage(message) ? 'error' : 'success'}`}>{message}</div>}
        <Outlet />
      </section>
      </main>
    </>
  )
}
