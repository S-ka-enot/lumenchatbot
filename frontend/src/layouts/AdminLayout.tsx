import Sidebar from '@/components/navigation/Sidebar'
import Topbar from '@/components/navigation/Topbar'
import { Outlet } from 'react-router-dom'

const AdminLayout = () => {
  return (
    <div className="flex min-h-screen bg-slate-100 text-slate-900">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AdminLayout



