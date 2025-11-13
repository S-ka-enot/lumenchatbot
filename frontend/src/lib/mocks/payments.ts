import type { PaymentListItem } from '@/lib/api'

export const PAYMENTS_MOCK: PaymentListItem[] = [
  {
    id: 1042,
    invoice: 'INV-1042',
    member: 'Екатерина Белкина',
    amount: '1 990.00 RUB',
    status: 'succeeded',
    created_at: new Date().toISOString(),
  },
  {
    id: 1041,
    invoice: 'INV-1041',
    member: 'Мария Соколова',
    amount: '1 990.00 RUB',
    status: 'pending',
    created_at: new Date().toISOString(),
  },
  {
    id: 1040,
    invoice: 'INV-1040',
    member: 'Анна Кузнецова',
    amount: '3 490.00 RUB',
    status: 'canceled',
    created_at: new Date().toISOString(),
  },
]


