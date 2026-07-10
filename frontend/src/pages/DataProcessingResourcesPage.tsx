import { FormEvent, useEffect, useState } from 'react'
import { createImageMacro, deleteAnalysisTool, deleteImageMacro, downloadFile, listAnalysisTools, listImageMacros, updateAnalysisTool, updateImageMacro, uploadAnalysisTool } from '../api'
import { copyText } from '../clipboard'
import type { AnalysisToolResource, ImageMacroResource, User } from '../types'

const initialMacroForm = { title: '', description: '', code: '' }
const initialToolForm = { title: '', description: '' }

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

export function DataProcessingResourcesPage({ user, setMessage }: { user: User; setMessage: (message: string) => void }) {
  const [macros, setMacros] = useState<ImageMacroResource[]>([])
  const [tools, setTools] = useState<AnalysisToolResource[]>([])
  const [macroForm, setMacroForm] = useState(initialMacroForm)
  const [toolForm, setToolForm] = useState(initialToolForm)
  const [toolFile, setToolFile] = useState<File | null>(null)
  const [savingMacro, setSavingMacro] = useState(false)
  const [uploadingTool, setUploadingTool] = useState(false)
  const [showMacroForm, setShowMacroForm] = useState(false)
  const [showToolForm, setShowToolForm] = useState(false)
  const [editingMacroId, setEditingMacroId] = useState<string | null>(null)
  const [editingToolId, setEditingToolId] = useState<string | null>(null)

  async function refreshResources() {
    const [nextMacros, nextTools] = await Promise.all([listImageMacros(), listAnalysisTools()])
    setMacros(nextMacros)
    setTools(nextTools)
  }

  useEffect(() => {
    void refreshResources().catch((error) => setMessage(error instanceof Error ? error.message : '公共资源加载失败'))
  }, [])

  async function copyMacroCode(code: string) {
    try {
      await copyText(code)
      setMessage('Macro 代码已复制')
    } catch {
      setMessage('复制失败，请手动选择代码复制')
    }
  }

  async function submitMacro(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSavingMacro(true)
    try {
      if (editingMacroId) {
        await updateImageMacro(editingMacroId, macroForm)
      } else {
        await createImageMacro(macroForm)
      }
      setMacroForm(initialMacroForm)
      setEditingMacroId(null)
      setShowMacroForm(false)
      await refreshResources()
      setMessage(editingMacroId ? 'Image macro 已更新' : 'Image macro 指令已分享')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Macro 分享失败')
    } finally {
      setSavingMacro(false)
    }
  }

  function startEditMacro(macro: ImageMacroResource) {
    setEditingMacroId(macro.id)
    setMacroForm({ title: macro.title, description: macro.description, code: macro.code })
    setShowMacroForm(true)
  }

  function cancelMacroForm() {
    setEditingMacroId(null)
    setMacroForm(initialMacroForm)
    setShowMacroForm(false)
  }

  async function submitTool(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingToolId && !toolFile) {
      setMessage('请选择需要上传的分析工具文件')
      return
    }
    setUploadingTool(true)
    try {
      if (editingToolId) {
        await updateAnalysisTool(editingToolId, { ...toolForm, file: toolFile })
      } else {
        await uploadAnalysisTool({ ...toolForm, file: toolFile as File })
      }
      setToolForm(initialToolForm)
      setToolFile(null)
      setEditingToolId(null)
      setShowToolForm(false)
      await refreshResources()
      setMessage(editingToolId ? '原创分析工具已更新' : '原创分析工具已上传')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '分析工具上传失败')
    } finally {
      setUploadingTool(false)
    }
  }

  function startEditTool(tool: AnalysisToolResource) {
    setEditingToolId(tool.id)
    setToolForm({ title: tool.title, description: tool.description })
    setToolFile(null)
    setShowToolForm(true)
  }

  function cancelToolForm() {
    setEditingToolId(null)
    setToolForm(initialToolForm)
    setToolFile(null)
    setShowToolForm(false)
  }

  async function handleDeleteMacro(macro: ImageMacroResource) {
    if (!window.confirm(`确认删除 macro「${macro.title}」？`)) {
      return
    }
    try {
      await deleteImageMacro(macro.id)
      await refreshResources()
      setMessage('Image macro 已删除')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Macro 删除失败')
    }
  }

  async function handleDeleteTool(tool: AnalysisToolResource) {
    if (!window.confirm(`确认删除分析工具「${tool.title}」？`)) {
      return
    }
    try {
      await deleteAnalysisTool(tool.id)
      await refreshResources()
      setMessage('分析工具已删除')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '分析工具删除失败')
    }
  }

  async function handleDownloadTool(tool: AnalysisToolResource) {
    try {
      await downloadFile(tool.download_url, tool.filename)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '分析工具下载失败')
    }
  }

  return (
    <section className="data-resources-page">
      <div className="hero-card card resource-hero-card">
        <div>
          <p className="eyebrow">其他公共资源</p>
          <h2>数据处理</h2>
          <p>沉淀实验室常用 ImageJ / Fiji macro 指令和原创数据分析工具，让数据处理流程像 Protocol 一样可复用、可追踪。</p>
        </div>
        <div className="resource-hero-stats"><span>{macros.length} 条 macro</span><span>{tools.length} 个工具</span></div>
      </div>
      <div className="resource-grid">
        <section className="card resource-panel macro-panel">
          <div className="resource-panel-header">
            <div className="resource-title-group"><span className="resource-icon">⌘</span><div><p className="eyebrow">ImageJ macro 指令</p><h3>已分享 macro 代码</h3><small>优先展示可复用的 ImageJ / Fiji macro，点击卡片内按钮可一键复制代码。</small></div></div>
            <div className="resource-panel-actions"><span>{macros.length} 条</span><button className="secondary" type="button" onClick={() => showMacroForm ? cancelMacroForm() : setShowMacroForm(true)}>{showMacroForm ? '收起表单' : '分享 macro'}</button></div>
          </div>
          {showMacroForm && (
            <form className="resource-form resource-form-card" onSubmit={submitMacro}>
              <div className="resource-form-title"><strong>{editingMacroId ? '修改 Image macro 指令' : '分享新的 Image macro 指令'}</strong><span>填写后会展示在下方 macro 资源列表中。</span></div>
              <label>Macro 标题<input value={macroForm.title} onChange={(event) => setMacroForm({ ...macroForm, title: event.target.value })} placeholder="例如：批量测量荧光强度" /></label>
              <label>用途说明<textarea value={macroForm.description} onChange={(event) => setMacroForm({ ...macroForm, description: event.target.value })} placeholder="适用图像类型、使用前准备或注意事项" /></label>
              <label>Macro 代码<textarea className="code-input" value={macroForm.code} onChange={(event) => setMacroForm({ ...macroForm, code: event.target.value })} placeholder="粘贴 ImageJ / Fiji macro 代码" /></label>
              <div className="resource-form-footer"><span>建议包含输入路径、输出路径和关键参数说明。</span><div className="action-row"><button className="secondary" type="button" onClick={cancelMacroForm}>取消</button><button className="primary" type="submit" disabled={savingMacro || !macroForm.title.trim() || !macroForm.code.trim()}>{savingMacro ? '保存中...' : editingMacroId ? '保存修改' : '发布 macro'}</button></div></div>
            </form>
          )}
          <div className="resource-list featured-resource-list">
            {macros.length === 0 && <div className="resource-empty-state"><strong>暂无 macro 指令</strong><span>点击右上角“分享 macro”，沉淀第一段可复用 Image macro。</span></div>}
            {macros.map((macro) => <article className="resource-item macro-item" key={macro.id}><div className="resource-item-header"><div><strong>{macro.title}</strong><span>上传者：{macro.author_name || '未知上传者'} · {new Date(macro.created_at).toLocaleDateString()}</span></div><div className="resource-card-actions"><em>Macro</em>{(user.is_admin || macro.author_id === user.id) && <><button className="secondary compact-button" type="button" onClick={() => startEditMacro(macro)}>编辑</button><button className="danger compact-button" type="button" onClick={() => { void handleDeleteMacro(macro) }}>删除</button></>}<button className="secondary compact-button" type="button" onClick={() => { void copyMacroCode(macro.code) }}>复制代码</button></div></div>{macro.description && <p>{macro.description}</p>}<pre>{macro.code}</pre></article>)}
          </div>
        </section>
        <section className="card resource-panel tool-panel">
          <div className="resource-panel-header">
            <div className="resource-title-group"><span className="resource-icon">⬡</span><div><p className="eyebrow">原创分析工具</p><h3>已上传分析工具</h3><small>优先展示实验室自研工具、脚本包、插件、安装包或分析模板，便于成员下载复用。</small></div></div>
            <div className="resource-panel-actions"><span>{tools.length} 个</span><button className="secondary" type="button" onClick={() => showToolForm ? cancelToolForm() : setShowToolForm(true)}>{showToolForm ? '收起表单' : '上传工具'}</button></div>
          </div>
          {showToolForm && (
            <form className="resource-form resource-form-card" onSubmit={submitTool}>
              <div className="resource-form-title"><strong>{editingToolId ? '修改原创分析工具' : '上传新的原创分析工具'}</strong><span>上传完成后会展示在下方工具资源列表中。</span></div>
              <label>工具名称<input value={toolForm.title} onChange={(event) => setToolForm({ ...toolForm, title: event.target.value })} placeholder="例如：细胞迁移定量工具" /></label>
              <label>工具说明<textarea value={toolForm.description} onChange={(event) => setToolForm({ ...toolForm, description: event.target.value })} placeholder="工具用途、安装方式、适用数据格式" /></label>
              <label className="resource-file-field">上传文件<input type="file" onChange={(event) => setToolFile(event.target.files?.[0] ?? null)} /><span>{toolFile ? `${toolFile.name} · ${formatFileSize(toolFile.size)}` : editingToolId ? '不选择新文件则保留原文件' : '支持安装包、压缩包、脚本或插件文件'}</span></label>
              <div className="resource-form-footer"><span>请在说明中补充运行环境和依赖。</span><div className="action-row"><button className="secondary" type="button" onClick={cancelToolForm}>取消</button><button className="primary" type="submit" disabled={uploadingTool || !toolForm.title.trim() || (!editingToolId && !toolFile)}>{uploadingTool ? '保存中...' : editingToolId ? '保存修改' : '发布工具'}</button></div></div>
            </form>
          )}
          <div className="resource-list featured-resource-list">
            {tools.length === 0 && <div className="resource-empty-state"><strong>暂无原创分析工具</strong><span>点击右上角“上传工具”，上传第一个实验室自研数据处理工具。</span></div>}
            {tools.map((tool) => <article className="resource-item tool-item" key={tool.id}><div className="resource-item-header"><div><strong>{tool.title}</strong><span>上传者：{tool.author_name || '未知上传者'} · {formatFileSize(tool.file_size)} · {new Date(tool.created_at).toLocaleDateString()}</span></div><div className="resource-card-actions"><em>Tool</em>{(user.is_admin || tool.author_id === user.id) && <><button className="secondary compact-button" type="button" onClick={() => startEditTool(tool)}>编辑</button><button className="danger compact-button" type="button" onClick={() => { void handleDeleteTool(tool) }}>删除</button></>}</div></div>{tool.description && <p>{tool.description}</p>}<div className="tool-download-row"><span>{tool.filename}</span><button className="secondary compact-button download-link" type="button" onClick={() => { void handleDownloadTool(tool) }}>下载文件</button></div></article>)}
          </div>
        </section>
      </div>
    </section>
  )
}
