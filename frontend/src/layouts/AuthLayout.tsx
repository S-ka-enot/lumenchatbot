import { Outlet } from 'react-router-dom'

const AuthLayout = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-lg font-semibold text-primary-700">
            LP
          </div>
          <h1 className="mt-4 text-xl font-semibold text-slate-900">LumenPay Admin</h1>
          <p className="mt-1 text-sm text-slate-500">
            Войдите, чтобы управлять подписками и каналами клуба.
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}

export default AuthLayout


