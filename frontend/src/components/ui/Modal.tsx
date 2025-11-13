type ModalProps = {
  open: boolean
  title: string
  description?: string
  onClose: () => void
  children: React.ReactNode
  footer?: React.ReactNode
  isLoading?: boolean
}

const Modal = ({ open, title, description, onClose, children, footer, isLoading }: ModalProps) => {
  if (!open) {
    return null
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4 py-6 text-slate-900"
      role="dialog"
      aria-modal="true"
    >
      <div className="absolute inset-0" onClick={onClose} aria-hidden="true" />
      <div className="relative z-10 w-full max-w-xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
        <div className="border-b border-slate-200 px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
              {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-1 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              aria-label="Закрыть"
            >
              ×
            </button>
          </div>
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-6 py-4 text-sm">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center text-slate-500">Загрузка...</div>
          ) : (
            children
          )}
        </div>

        {footer ? <div className="border-t border-slate-200 bg-slate-50 px-6 py-4">{footer}</div> : null}
      </div>
    </div>
  )
}

export default Modal


