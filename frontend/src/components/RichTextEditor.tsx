import { useEffect, useRef, useState, type MouseEvent } from 'react'

type RichTextEditorProps = {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
  minHeight?: number
}

type FormatState = Record<'bold' | 'italic' | 'underline' | 'superscript' | 'subscript' | 'justifyLeft' | 'justifyCenter' | 'justifyRight', boolean>

const fontSizeOptions = ['12px', '14px', '16px', '18px', '24px', '32px']

const emptyFormatState: FormatState = {
  bold: false,
  italic: false,
  underline: false,
  superscript: false,
  subscript: false,
  justifyLeft: false,
  justifyCenter: false,
  justifyRight: false,
}

export function RichTextEditor({ value, onChange, disabled = false, placeholder = '请输入 Protocol 内容', minHeight = 420 }: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement | null>(null)
  const toolbarRef = useRef<HTMLDivElement | null>(null)
  const savedRangeRef = useRef<Range | null>(null)
  const [tableRows, setTableRows] = useState(2)
  const [tableColumns, setTableColumns] = useState(2)
  const [fontSize, setFontSize] = useState('16px')
  const [formatState, setFormatState] = useState<FormatState>(emptyFormatState)

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
    const range = restoreSelection()
    if (!range) {
      return
    }
    const wasCollapsed = range.collapsed
    const toggleCommands: Array<keyof FormatState> = ['bold', 'italic', 'underline', 'superscript', 'subscript']
    const formatCommand = toggleCommands.find((item) => item === command)
    const nextCollapsedState = formatCommand ? !formatState[formatCommand] : undefined
    document.execCommand(command, false, commandValue)
    emitChange()
    saveSelection()
    if (wasCollapsed && formatCommand && nextCollapsedState !== undefined) {
      setFormatState((current) => ({ ...current, [formatCommand]: nextCollapsedState }))
    }
  }

  function keepEditorSelection(event: MouseEvent) {
    event.preventDefault()
    saveSelection()
  }

  function emitChange() {
    onChange(editorRef.current?.innerHTML ?? '')
  }

  function selectionIsInEditor(range: Range) {
    const editor = editorRef.current
    return Boolean(editor && editor.contains(range.commonAncestorContainer))
  }

  function refreshFormatState(range?: Range) {
    const nextState = { ...emptyFormatState }
    for (const command of Object.keys(nextState) as Array<keyof FormatState>) {
      try {
        nextState[command] = document.queryCommandState(command)
      } catch {
        nextState[command] = false
      }
    }
    setFormatState(nextState)

    if (range && editorRef.current?.textContent) {
      const container = range.startContainer
      const offsetNode = container.nodeType === Node.ELEMENT_NODE
        ? (container.childNodes[range.startOffset] ?? container.childNodes[Math.max(0, range.startOffset - 1)] ?? container)
        : container
      const element = offsetNode instanceof Element ? offsetNode : offsetNode.parentElement
      if (element && editorRef.current?.contains(element)) {
        const computedSize = Number.parseFloat(window.getComputedStyle(element).fontSize)
        const closestSize = fontSizeOptions.reduce((closest, option) => (
          Math.abs(Number.parseFloat(option) - computedSize) < Math.abs(Number.parseFloat(closest) - computedSize)
            ? option
            : closest
        ))
        setFontSize(closestSize)
      }
    }
  }

  function saveSelection() {
    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) {
      return
    }
    const range = selection.getRangeAt(0)
    if (selectionIsInEditor(range)) {
      savedRangeRef.current = range.cloneRange()
      refreshFormatState(range)
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

  function applyFontSize(nextSize: string) {
    if (disabled) {
      return
    }
    setFontSize(nextSize)
    const range = restoreSelection()
    if (!range) {
      return
    }
    if (range.collapsed) {
      document.execCommand('fontSize', false, getLegacyFontSize(nextSize))
      saveSelection()
      return
    }
    const span = document.createElement('span')
    span.style.fontSize = nextSize
    const contents = range.extractContents()
    contents.querySelectorAll<HTMLElement>('[style], font[size]').forEach((element) => {
      element.style.removeProperty('font-size')
      element.removeAttribute('size')
      if (!element.getAttribute('style')) {
        element.removeAttribute('style')
      }
    })
    span.appendChild(contents)
    range.insertNode(span)

    let ancestor = span.parentElement
    while (ancestor && ancestor !== editorRef.current) {
      const meaningfulChildren = Array.from(ancestor.childNodes).filter((node) => (
        node === span || node.nodeType !== Node.TEXT_NODE || node.textContent?.trim()
      ))
      if (meaningfulChildren.length !== 1 || meaningfulChildren[0] !== span) {
        break
      }
      ancestor.style.removeProperty('font-size')
      ancestor.removeAttribute('size')
      if (!ancestor.getAttribute('style')) {
        ancestor.removeAttribute('style')
      }
      ancestor = ancestor.parentElement
    }
    const nextRange = document.createRange()
    nextRange.selectNodeContents(span)
    const selection = window.getSelection()
    selection?.removeAllRanges()
    selection?.addRange(nextRange)
    savedRangeRef.current = nextRange.cloneRange()
    emitChange()
  }

  function getLegacyFontSize(size: string) {
    const numericSize = Number(size.replace('px', ''))
    if (numericSize <= 12) return '2'
    if (numericSize <= 16) return '3'
    if (numericSize <= 18) return '4'
    if (numericSize <= 24) return '5'
    if (numericSize <= 32) return '6'
    return '7'
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
      <div className="rich-text-toolbar" ref={toolbarRef}>
        <div className="rich-toolbar-group">
          <button className={`rich-tool-button ${formatState.bold ? 'active' : ''}`} type="button" title="加粗" aria-label="加粗" aria-pressed={formatState.bold} onMouseDown={keepEditorSelection} onClick={() => runCommand('bold')} disabled={disabled}><strong>B</strong></button>
          <button className={`rich-tool-button ${formatState.italic ? 'active' : ''}`} type="button" title="斜体" aria-label="斜体" aria-pressed={formatState.italic} onMouseDown={keepEditorSelection} onClick={() => runCommand('italic')} disabled={disabled}><em>I</em></button>
          <button className={`rich-tool-button ${formatState.underline ? 'active' : ''}`} type="button" title="下划线" aria-label="下划线" aria-pressed={formatState.underline} onMouseDown={keepEditorSelection} onClick={() => runCommand('underline')} disabled={disabled}><u>U</u></button>
          <button className={`rich-tool-button ${formatState.superscript ? 'active' : ''}`} type="button" title="上标" aria-label="上标" aria-pressed={formatState.superscript} onMouseDown={keepEditorSelection} onClick={() => runCommand('superscript')} disabled={disabled}><span className="rich-script-icon">x<sup>2</sup></span></button>
          <button className={`rich-tool-button ${formatState.subscript ? 'active' : ''}`} type="button" title="下标" aria-label="下标" aria-pressed={formatState.subscript} onMouseDown={keepEditorSelection} onClick={() => runCommand('subscript')} disabled={disabled}><span className="rich-script-icon">x<sub>2</sub></span></button>
        </div>
        <div className="rich-toolbar-group">
          <label className="rich-font-size-picker" title="字号">
            <span className="rich-font-size-label">字号</span>
            <select aria-label="字号" value={fontSize} disabled={disabled} onMouseDown={saveSelection} onChange={(event) => applyFontSize(event.target.value)}>
              <option value="12px">12</option><option value="14px">14</option><option value="16px">16</option><option value="18px">18</option><option value="24px">24</option><option value="32px">32</option>
            </select>
          </label>
          <label className="rich-color-picker" title="字体颜色">
            <span className="rich-color-icon">A</span>
            <input aria-label="字体颜色" type="color" disabled={disabled} onMouseDown={saveSelection} onChange={(event) => runCommand('foreColor', event.target.value)} />
          </label>
        </div>
        <div className="rich-toolbar-group">
          <button className={`rich-tool-button rich-align-icon align-left ${formatState.justifyLeft ? 'active' : ''}`} type="button" title="左对齐" aria-label="左对齐" aria-pressed={formatState.justifyLeft} onMouseDown={keepEditorSelection} onClick={() => runCommand('justifyLeft')} disabled={disabled}><i /><i /><i /></button>
          <button className={`rich-tool-button rich-align-icon align-center ${formatState.justifyCenter ? 'active' : ''}`} type="button" title="居中" aria-label="居中" aria-pressed={formatState.justifyCenter} onMouseDown={keepEditorSelection} onClick={() => runCommand('justifyCenter')} disabled={disabled}><i /><i /><i /></button>
          <button className={`rich-tool-button rich-align-icon align-right ${formatState.justifyRight ? 'active' : ''}`} type="button" title="右对齐" aria-label="右对齐" aria-pressed={formatState.justifyRight} onMouseDown={keepEditorSelection} onClick={() => runCommand('justifyRight')} disabled={disabled}><i /><i /><i /></button>
        </div>
        <div className="rich-toolbar-group rich-table-picker">
          <div className="rich-table-size-control"><span>行</span><div className="rich-table-stepper" aria-label="表格行数"><button className="rich-stepper-button" type="button" onMouseDown={keepEditorSelection} onClick={() => adjustTableRows(-1)} disabled={disabled || tableRows <= 1} aria-label="减少表格行数">−</button><strong>{tableRows}</strong><button className="rich-stepper-button" type="button" onMouseDown={keepEditorSelection} onClick={() => adjustTableRows(1)} disabled={disabled || tableRows >= 12} aria-label="增加表格行数">+</button></div></div>
          <div className="rich-table-size-control"><span>列</span><div className="rich-table-stepper" aria-label="表格列数"><button className="rich-stepper-button" type="button" onMouseDown={keepEditorSelection} onClick={() => adjustTableColumns(-1)} disabled={disabled || tableColumns <= 1} aria-label="减少表格列数">−</button><strong>{tableColumns}</strong><button className="rich-stepper-button" type="button" onMouseDown={keepEditorSelection} onClick={() => adjustTableColumns(1)} disabled={disabled || tableColumns >= 12} aria-label="增加表格列数">+</button></div></div>
          <button className="rich-insert-table-button" type="button" onMouseDown={keepEditorSelection} onClick={insertTable} disabled={disabled}><span className="rich-table-grid-icon" aria-hidden="true"><i /><i /><i /><i /></span><span>插入表格</span></button>
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
