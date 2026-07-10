import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadCommercialProtocol } from '../api'

export function CreateCommercialProtocolPage() {
  const navigate = useNavigate()
  const [message, setMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [form, setForm] = useState({ title: '', manufacturer: '', catalog_no: '', description: '' })
  const [file, setFile] = useState<File | null>(null)

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!form.title.trim()) {
      setMessage('请填写标题')
      return
    }
    if (!form.manufacturer.trim()) {
      setMessage('请填写厂家')
      return
    }
    if (!file) {
      setMessage('请选择 PDF 文件')
      return
    }
    setIsUploading(true)
    setMessage('')
    try {
      await uploadCommercialProtocol({ ...form, file })
      setMessage('商品化试剂 Protocol 已上传')
      navigate('/commercial-protocols')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '上传失败')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <section className="commercial-create-page">
      <form className="card commercial-upload-card" onSubmit={handleUpload}>
        <p className="eyebrow">新建商品化 Protocol</p>
        <h2>上传商品化试剂 PDF Protocol</h2>
        <p className="muted">上传后会进入商品化试剂 Protocol 库，用于在线预览和下载原始 PDF。</p>
        {message && <div className="app-message success inline-message">{message}</div>}
        <div className="edit-row two">
          <label>标题<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label>
          <label>厂家<input value={form.manufacturer} onChange={(event) => setForm({ ...form, manufacturer: event.target.value })} required /></label>
        </div>
        <div className="edit-row two">
          <label>货号<input value={form.catalog_no} onChange={(event) => setForm({ ...form, catalog_no: event.target.value })} /></label>
          <label>PDF 文件<input type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        </div>
        <label>说明<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
        <div className="action-row">
          <button className="primary" type="submit" disabled={isUploading}>{isUploading ? '上传中...' : '上传 PDF'}</button>
          <button className="secondary" type="button" onClick={() => navigate('/commercial-protocols')}>返回列表</button>
        </div>
      </form>
    </section>
  )
}
