import ProtectedRoute from '@/components/routing/ProtectedRoute'
import AdminLayout from '@/layouts/AdminLayout'
import AuthLayout from '@/layouts/AuthLayout'
import BotsPage from '@/pages/bots/BotsPage'
import BroadcastsPage from '@/pages/broadcasts/BroadcastsPage'
import ChannelsPage from '@/pages/channels/ChannelsPage'
import DashboardPage from '@/pages/dashboard/DashboardPage'
import LoginPage from '@/pages/auth/LoginPage'
import PaymentsPage from '@/pages/payments/PaymentsPage'
import PromoCodesPage from '@/pages/promocodes/PromoCodesPage'
import SettingsPage from '@/pages/settings/SettingsPage'
import SubscribersPage from '@/pages/subscribers/SubscribersPage'
import SubscriptionsPage from '@/pages/subscriptions/SubscriptionsPage'
import { queryClient } from '@/lib/queryClient'
import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route element={<AdminLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="/subscribers" element={<SubscribersPage />} />
              <Route path="/subscriptions" element={<SubscriptionsPage />} />
              <Route path="/payments" element={<PaymentsPage />} />
              <Route path="/channels" element={<ChannelsPage />} />
              <Route path="/promo-codes" element={<PromoCodesPage />} />
              <Route path="/broadcasts" element={<BroadcastsPage />} />
              <Route path="/bots" element={<BotsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>
          <Route element={<AuthLayout />}>
            <Route path="/auth/login" element={<LoginPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
