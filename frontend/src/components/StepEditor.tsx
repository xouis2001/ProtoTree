import { stripStepPrefix } from '../appUtils'
import type { StructuredStep } from '../types'

export function StepEditor({ step, index, steps, onChange, onRemove }: { step: StructuredStep; index: number; steps: StructuredStep[]; onChange: (steps: StructuredStep[]) => void; onRemove: (steps: StructuredStep[]) => void }) {
  function updateStep(next: StructuredStep) {
    onChange(steps.map((item, itemIndex) => itemIndex === index ? next : item))
  }
  return (
    <div className="edit-step step-editor">
      <strong className="step-fixed-label">Step {index + 1}</strong>
      <input value={stripStepPrefix(step.title ?? '')} onChange={(event) => updateStep({ ...step, order: index + 1, title: event.target.value })} placeholder="步骤概括" />
      <textarea value={step.content ?? ''} onChange={(event) => updateStep({ ...step, order: index + 1, content: event.target.value })} placeholder="步骤内容阐述" />
      <button className="secondary" type="button" onClick={() => onRemove(steps.filter((_, itemIndex) => itemIndex !== index))}>删除</button>
    </div>
  )
}
