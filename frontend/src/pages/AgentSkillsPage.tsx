import { FormEvent, useEffect, useState } from 'react'
import { createAgentSkill, deleteAgentSkill, downloadFile, listAgentSkills, updateAgentSkill } from '../api'
import type { AgentSkillResource, User } from '../types'

const initialSkillForm = { title: '', description: '', source_model: '', source_agent: '', file: null as File | null }

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

export function AgentSkillsPage({ user, setMessage }: { user: User; setMessage: (message: string) => void }) {
  const [skills, setSkills] = useState<AgentSkillResource[]>([])
  const [skillForm, setSkillForm] = useState(initialSkillForm)
  const [savingSkill, setSavingSkill] = useState(false)
  const [showSkillForm, setShowSkillForm] = useState(false)
  const [editingSkillId, setEditingSkillId] = useState<string | null>(null)

  async function refreshSkills() {
    setSkills(await listAgentSkills())
  }

  useEffect(() => {
    void refreshSkills().catch((error) => setMessage(error instanceof Error ? error.message : 'Agent skill 加载失败'))
  }, [])

  async function submitSkill(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingSkillId && !skillForm.file) {
      setMessage('请上传 skill 文件，推荐使用 zip 压缩包')
      return
    }
    setSavingSkill(true)
    try {
      if (editingSkillId) {
        await updateAgentSkill(editingSkillId, skillForm)
      } else {
        await createAgentSkill({ ...skillForm, file: skillForm.file as File })
      }
      setSkillForm(initialSkillForm)
      setEditingSkillId(null)
      setShowSkillForm(false)
      await refreshSkills()
      setMessage(editingSkillId ? 'Agent skill 已更新' : 'Agent skill 已分享')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Agent skill 分享失败')
    } finally {
      setSavingSkill(false)
    }
  }

  function startEditSkill(skill: AgentSkillResource) {
    setEditingSkillId(skill.id)
    setSkillForm({ title: skill.title, description: skill.description, source_model: skill.source_model, source_agent: skill.source_agent, file: null })
    setShowSkillForm(true)
  }

  function cancelSkillForm() {
    setEditingSkillId(null)
    setSkillForm(initialSkillForm)
    setShowSkillForm(false)
  }

  async function handleDeleteSkill(skill: AgentSkillResource) {
    if (!window.confirm(`确认删除 Agent Skill「${skill.title}」？`)) {
      return
    }
    try {
      await deleteAgentSkill(skill.id)
      await refreshSkills()
      setMessage('Agent skill 已删除')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Agent skill 删除失败')
    }
  }

  async function handleDownloadSkill(skill: AgentSkillResource) {
    try {
      await downloadFile(skill.download_url, skill.filename)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Agent skill 下载失败')
    }
  }

  return (
    <section className="agent-skills-page data-resources-page">
      <div className="hero-card card resource-hero-card">
        <div>
          <p className="eyebrow">其他公共资源</p>
          <h2>Agent Skill</h2>
          <p>分享可复用的 agent skill 文件。建议上传 zip 压缩包，打包 skill 文件、README、示例输入输出和依赖说明，其他成员可直接下载复用。</p>
        </div>
        <div className="resource-hero-stats"><span>{skills.length} 个 skill</span></div>
      </div>

      <section className="card resource-panel agent-skill-panel">
        <div className="resource-panel-header">
          <div className="resource-title-group">
            <span className="resource-icon">✓</span>
            <div>
              <p className="eyebrow">Agent Skill 分享</p>
              <h3>已分享 agent skill 文件</h3>
              <small>推荐上传 zip 压缩包，并写明来源模型、来源 agent、使用场景和运行依赖。</small>
            </div>
          </div>
          <div className="resource-panel-actions">
            <span>{skills.length} 个</span>
            <button className="secondary" type="button" onClick={() => showSkillForm ? cancelSkillForm() : setShowSkillForm(true)}>{showSkillForm ? '收起表单' : '分享 skill'}</button>
          </div>
        </div>

        {showSkillForm && (
          <form className="resource-form resource-form-card" onSubmit={submitSkill}>
            <div className="resource-form-title">
              <strong>{editingSkillId ? '修改 Agent Skill' : '分享新的 Agent Skill'}</strong>
              <span>建议上传 zip 压缩包，把 skill、README、示例和依赖说明放在一起。</span>
            </div>
            <label>Skill 标题<input value={skillForm.title} onChange={(event) => setSkillForm({ ...skillForm, title: event.target.value })} placeholder="例如：Protocol 结构化整理 skill" /></label>
            <label>用途说明<textarea value={skillForm.description} onChange={(event) => setSkillForm({ ...skillForm, description: event.target.value })} placeholder="说明适用场景、输入输出、使用注意事项" /></label>
            <div className="resource-form-two-columns">
              <label>模型信息<input value={skillForm.source_model} onChange={(event) => setSkillForm({ ...skillForm, source_model: event.target.value })} placeholder="例如：Claude Sonnet 4 / GPT-4.1 / TRAE" /></label>
              <label>来源 Agent<input value={skillForm.source_agent} onChange={(event) => setSkillForm({ ...skillForm, source_agent: event.target.value })} placeholder="例如：protocol-parser agent" /></label>
            </div>
            <label>Skill 文件<input type="file" accept=".zip,.tar,.gz,.tgz,.7z,.rar,.md,.txt,.json,.yaml,.yml" onChange={(event) => setSkillForm({ ...skillForm, file: event.target.files?.[0] ?? null })} /></label>
            <div className="resource-form-footer">
              <span>{skillForm.file ? `已选择：${skillForm.file.name}` : editingSkillId ? '不选择新文件则保留原文件。' : '推荐上传 .zip 压缩包。'}</span>
              <div className="action-row">
                <button className="secondary" type="button" onClick={cancelSkillForm}>取消</button>
                <button className="primary" type="submit" disabled={savingSkill || !skillForm.title.trim() || !skillForm.source_model.trim() || !skillForm.source_agent.trim() || (!editingSkillId && !skillForm.file)}>{savingSkill ? '保存中...' : editingSkillId ? '保存修改' : '发布 skill'}</button>
              </div>
            </div>
          </form>
        )}

        <div className="resource-list featured-resource-list agent-skill-list">
          {skills.length === 0 && <div className="resource-empty-state"><strong>暂无 Agent Skill</strong><span>点击右上角“分享 skill”，上传第一个可下载复用的 agent skill 压缩包。</span></div>}
          {skills.map((skill) => (
            <article className="resource-item agent-skill-item" key={skill.id}>
              <div className="resource-item-header">
                <div>
                  <strong>{skill.title}</strong>
                  <span>上传者：{skill.author_name || '未知上传者'} · {formatFileSize(skill.file_size)} · {new Date(skill.created_at).toLocaleDateString()}</span>
                </div>
                <div className="resource-card-actions">
                  <em>Agent Skill</em>
                  {(user.is_admin || skill.author_id === user.id) && <>
                    <button className="secondary compact-button" type="button" onClick={() => startEditSkill(skill)}>编辑</button>
                    <button className="danger compact-button" type="button" onClick={() => { void handleDeleteSkill(skill) }}>删除</button>
                  </>}
                </div>
              </div>
              {skill.description && <p>{skill.description}</p>}
              <div className="agent-skill-source">
                <span>模型信息：<strong>{skill.source_model}</strong></span>
                <span>来源 Agent：<strong>{skill.source_agent}</strong></span>
              </div>
              <div className="tool-download-row">
                <span>{skill.filename}</span>
                <button className="secondary compact-button download-link" type="button" onClick={() => { void handleDownloadSkill(skill) }}>下载文件</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  )
}
