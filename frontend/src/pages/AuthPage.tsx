import { FormEvent } from 'react'
import type { AuthMode, RegisterStep } from '../appTypes'
import { isErrorMessage } from '../appUtils'
import { AvatarBuilder } from '../components/Avatar'
import { BrandLogo } from '../components/BrandLogo'

export function AuthPage({ mode, setMode, registerStep, setRegisterStep, authForm, setAuthForm, usedAvatarColors, message, handleAuth }: { mode: AuthMode; setMode: (mode: AuthMode) => void; registerStep: RegisterStep; setRegisterStep: (step: RegisterStep) => void; authForm: { name: string; email: string; password: string; avatar: string }; setAuthForm: (value: { name: string; email: string; password: string; avatar: string }) => void; usedAvatarColors: string[]; message: string; handleAuth: (event: FormEvent<HTMLFormElement>) => void }) {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand-block">
          <BrandLogo variant="lockup" />
          <div><p className="eyebrow">ProtoTree Demo · M8</p><h1>实验室 Protocol 协作知识库</h1><p className="muted">已支持富文本编辑、Fork 关系、Contribution Profile、评论或踩坑经验协作和搜索筛选。</p></div>
        </div>
        <div className="tabs">
          <button className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setRegisterStep('info') }}>注册</button>
          <button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setRegisterStep('info') }}>登录</button>
        </div>
        <form className="form" onSubmit={handleAuth}>
          {mode === 'register' && registerStep === 'avatar' ? (
            <>
              <AvatarBuilder value={authForm.avatar} usedColors={usedAvatarColors} onChange={(avatar) => setAuthForm({ ...authForm, avatar })} />
              <button className="primary" type="submit">完成注册</button>
              <button className="secondary" type="button" onClick={() => setRegisterStep('info')}>返回填写信息</button>
            </>
          ) : (
            <>
              {mode === 'register' && <input value={authForm.name} onChange={(event) => setAuthForm({ ...authForm, name: event.target.value })} placeholder="姓名" />}
              <input value={authForm.email} onChange={(event) => setAuthForm({ ...authForm, email: event.target.value })} placeholder="邮箱" />
              <input type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} placeholder="密码" />
              <button className="primary" type="submit">{mode === 'register' ? '下一步：选择头像' : '登录'}</button>
            </>
          )}
        </form>
        {message && <p className={`message ${isErrorMessage(message) ? 'error' : 'success'}`}>{message}</p>}
      </section>
    </main>
  )
}
