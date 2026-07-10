import { Component, ReactNode } from 'react'

export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <main className="error-page">
          <section className="card empty-state">
            <p className="eyebrow">页面渲染失败</p>
            <h1>ProtoTree 遇到了前端显示错误</h1>
            <p>{this.state.error.message}</p>
            <button className="primary" type="button" onClick={() => window.location.reload()}>刷新页面</button>
          </section>
        </main>
      )
    }
    return this.props.children
  }
}

