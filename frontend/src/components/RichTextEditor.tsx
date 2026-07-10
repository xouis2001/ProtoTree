import { useEffect, useRef, useState } from 'react'

type RichTextEditorProps = {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
  minHeight?: number
}

export function RichTextEditor({ value, onChange, disabled = false, placeholder = '请输入 Protocol 内容', minHeight = 420 }: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement | null>(null)
  const savedRangeRef = useRef<Range | null>(null)
  const [tableRows, setTableRows] = useState(2)
  const [tableColumns, setTableColumns] = useState(2)

  useEffect(() => {
    const editor = editorRef.current
    if (editor && editor.innerHTML !== value) {
      editor.innerHTML = value
    }
  }, [value])

  function runCommand(command: string, commandValue?: string) {
    if (disabled) {
      return
    }
    restoreSelection()
    document.execCommand(command, false, commandValue)
    emitChange()
    saveSelection()
  }

  function emitChange() {
    onChange(editorRef.current?.innerHTML ?? '')
  }

  function selectionIsInEditor(range: Range) {
    const editor = editorRef.current
    return Boolean(editor && editor.contains(range.commonAncestorContainer))
  }

  function saveSelection() {
    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) {
      return
    }
    const range = selection.getRangeAt(0)
    if (selectionIsInEditor(range)) {
      savedRangeRef.current = range.cloneRange()
    }
  }

  function placeCaretAtEnd() {
    const editor = editorRef.current
    if (!editor) {
      return null
    }
    const range = document.createRange()
    range.selectNodeContents(editor)
    range.collapse(false)
    const selection = window.getSelection()
    selection?.removeAllRanges()
    selection?.addRange(range)
    savedRangeRef.current = range.cloneRange()
    return range
  }

  function restoreSelection() {
    const editor = editorRef.current
    if (!editor) {
      return null
    }
    editor.focus()
    const selection = window.getSelection()
    const savedRange = savedRangeRef.current
    if (selection && savedRange && selectionIsInEditor(savedRange)) {
      selection.removeAllRanges()
      selection.addRange(savedRange)
      return savedRange
    }
    return placeCaretAtEnd()
  }

  function normalizeTableSize(value: number) {
    return Math.max(1, Math.min(12, Number.isFinite(value) ? value : 1))
  }

  function adjustTableRows(delta: number) {
    setTableRows((value) => normalizeTableSize(value + delta))
  }

  function adjustTableColumns(delta: number) {
    setTableColumns((value) => normalizeTableSize(value + delta))
  }

  function insertTable() {
    if (disabled) {
      return
    }
    const rows = normalizeTableSize(tableRows)
    const columns = normalizeTableSize(tableColumns)
    const table = Array.from({ length: rows }, () => `<tr>${Array.from({ length: columns }, () => '<td><br></td>').join('')}</tr>`).join('')
    insertHtmlAtSelection(`<table><tbody>${table}</tbody></table><p><br></p>`)
  }

  function insertHtmlAtSelection(html: string) {
    const range = restoreSelection()
    if (!range) {
      return
    }
    const template = document.createElement('template')
    template.innerHTML = html
    const fragment = template.content
    const lastNode = fragment.lastChild
    range.deleteContents()
    range.insertNode(fragment)
    if (lastNode) {
      const nextRange = document.createRange()
      nextRange.setStartAfter(lastNode)
      nextRange.collapse(true)
      const selection = window.getSelection()
      selection?.removeAllRanges()
      selection?.addRange(nextRange)
      savedRangeRef.current = nextRange.cloneRange()
    }
    emitChange()
  }

  return (
    <div className={`rich-text-editor ${disabled ? 'disabled' : ''}`}>
      <div className="rich-text-toolbar">
        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand('bold')} disabled={disabled}>加粗</button>
        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand('italic')} disabled={disabled}>斜体</button>
        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand('underline')} disabled={disabled}>下划线</button>
        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand('justifyLeft')} disabled={disabled}>左对齐</button>
        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand('justifyCenter')} disabled={disabled}>居中</button>
        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand('justifyRight')} disabled={disabled}>右对齐</button>
        <label className="rich-color-picker">
          字体颜色
          <input type="color" disabled={disabled} onChange={(event) => runCommand('foreColor', event.target.value)} />
        </label>
        <div className="rich-table-picker">
          <div className="rich-table-size-control">
            <span>行</span>
            <div className="rich-table-stepper" aria-label="表格行数">
              <button className="rich-stepper-button" type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => adjustTableRows(-1)} disabled={disabled || tableRows <= 1} aria-label="减少表格行数">-</button>
              <strong>{tableRows}</strong>
              <button className="rich-stepper-button" type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => adjustTableRows(1)} disabled={disabled || tableRows >= 12} aria-label="增加表格行数">+</button>
            </div>
          </div>
          <div className="rich-table-size-control">
            <span>列</span>
            <div className="rich-table-stepper" aria-label="表格列数">
              <button className="rich-stepper-button" type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => adjustTableColumns(-1)} disabled={disabled || tableColumns <= 1} aria-label="减少表格列数">-</button>
              <strong>{tableColumns}</strong>
              <button className="rich-stepper-button" type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => adjustTableColumns(1)} disabled={disabled || tableColumns >= 12} aria-label="增加表格列数">+</button>
            </div>
          </div>
          <button className="rich-insert-table-button" type="button" onMouseDown={(event) => event.preventDefault()} onClick={insertTable} disabled={disabled}>插入表格</button>
        </div>
      </div>
      <div
        ref={editorRef}
        className="rich-text-surface"
        contentEditable={!disabled}
        data-placeholder={placeholder}
        onInput={() => {
          emitChange()
          saveSelection()
        }}
        onBlur={() => {
          saveSelection()
          emitChange()
        }}
        onKeyUp={saveSelection}
        onMouseUp={saveSelection}
        style={{ minHeight }}
        suppressContentEditableWarning
      />
    </div>
  )
}
