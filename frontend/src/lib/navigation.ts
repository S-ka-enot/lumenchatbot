import {
  Banknote,
  Bot,
  CreditCard,
  LayoutDashboard,
  Megaphone,
  MessageSquare,
  Settings,
  Ticket,
  Users,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type NavigationItem = {
  label: string
  to: string
  icon: LucideIcon
  description?: string
  badge?: string
}

export type NavigationSection = {
  title: string
  items: NavigationItem[]
}

export const NAVIGATION: NavigationSection[] = [
  {
    title: 'Основное',
    items: [
      {
        label: 'Дашборд',
        to: '/',
        icon: LayoutDashboard,
        description: 'Метрики подписок и выручки',
      },
      {
        label: 'Участницы клуба',
        to: '/subscribers',
        icon: Users,
        description: 'Профили, статусы и активность',
      },
      {
        label: 'Подписки',
        to: '/subscriptions',
        icon: CreditCard,
        description: 'Тарифы, периоды и автоматизации',
      },
      {
        label: 'Платежи',
        to: '/payments',
        icon: Banknote,
        description: 'История транзакций и статусы',
      },
    ],
  },
  {
    title: 'Контент',
    items: [
      {
        label: 'Каналы',
        to: '/channels',
        icon: MessageSquare,
        description: 'Закрытые чаты и приглашения',
      },
      {
        label: 'Промокоды',
        to: '/promo-codes',
        icon: Ticket,
        description: 'Скидки и специальные предложения',
      },
      {
        label: 'Рассылки',
        to: '/broadcasts',
        icon: Megaphone,
        description: 'Планирование объявлений и напоминаний',
      },
    ],
  },
  {
    title: 'Управление',
    items: [
      {
        label: 'Боты',
        to: '/bots',
        icon: Bot,
        description: 'Статусы и ключи интеграций',
      },
      {
        label: 'Настройки',
        to: '/settings',
        icon: Settings,
        description: 'Реквизиты оплаты и команда',
      },
    ],
  },
]

