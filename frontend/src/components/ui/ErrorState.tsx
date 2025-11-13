type ErrorStateProps = {
  title?: string
  description?: string
  actionLabel?: string
  onRetry?: () => void
}

const ErrorState = ({
  title = 'Не удалось загрузить данные',
  description = 'Попробуйте обновить страницу или повторить попытку позже.',
  actionLabel = 'Повторить',
  onRetry,
}: ErrorStateProps) => {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
      <p className="font-semibold">{title}</p>
      <p className="mt-2 text-rose-600">{description}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex rounded-lg border border-rose-200 bg-white px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-100"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}

export default ErrorState


