export type DashboardMetric = {
  id: string
  title: string
  value: string
  change?: string | null
  icon: string
}

export type RevenuePoint = {
  date: string
  value: number
}

export type ActivityItem = {
  id: string
  title: string
  description: string
  timestamp: string
}

export type DashboardSummary = {
  metrics: DashboardMetric[]
  revenue_trend: RevenuePoint[]
  recent_activity: ActivityItem[]
}

export const DASHBOARD_SUMMARY_MOCK: DashboardSummary = {
  metrics: [
    {
      id: 'active_subscriptions',
      title: 'Активные подписки',
      value: '428',
      change: '+12 за неделю',
      icon: 'users',
    },
    {
      id: 'monthly_revenue',
      title: 'Доход за 30 дней',
      value: '854 200 ₽',
      change: '+18%',
      icon: 'credit-card',
    },
    {
      id: 'renewals_today',
      title: 'Продлений сегодня',
      value: '23',
      change: '5 ожидают оплаты',
      icon: 'arrow-up-right',
    },
  ],
  revenue_trend: [
    { date: '01.11', value: 95000 },
    { date: '02.11', value: 102000 },
    { date: '03.11', value: 98000 },
    { date: '04.11', value: 110000 },
    { date: '05.11', value: 118000 },
    { date: '06.11', value: 123000 },
    { date: '07.11', value: 132000 },
  ],
  recent_activity: [
    {
      id: 'activity-1',
      title: 'Продление подписки',
      description: 'Ольга П. продлила тариф «Premium» до 10.12',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'activity-2',
      title: 'Новый платёж',
      description: 'Платёж 1 990 ₽ от Анны К. прошёл успешно',
      timestamp: new Date().toISOString(),
    },
  ],
}


