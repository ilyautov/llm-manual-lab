/** Application/runtime boundary: the model does not read this data directly. */
import { pathToFileURL } from 'node:url';
export interface Order { id: string; date: string; status: 'paid' | 'pending' }
export interface OrderTrace { events: string[]; count: number | null }

export function fixtureOrders(): Order[] {
  const paid: Order[] = Array.from({ length: 42 }, (_, i) => ({
    id: `paid-${String(i + 1).padStart(2, '0')}`,
    date: '2025-03-01',
    status: 'paid',
  }));
  return [...paid,
    { id: 'pending-1', date: '2025-03-01', status: 'pending' },
    { id: 'pending-2', date: '2025-03-01', status: 'pending' },
    { id: 'other-date', date: '2025-03-02', status: 'paid' },
  ];
}

export function paidOrders(role: 'reader' | 'guest', date: string, orders = fixtureOrders()): OrderTrace {
  const events = [`model_proposal: paid_orders(date=${date}, status=paid)`];
  if (role !== 'reader') {
    events.push('runtime_denied: missing orders:read permission');
    return { events, count: null };
  }
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(date)) {
    events.push('runtime_denied: invalid ISO date');
    return { events, count: null };
  }
  events.push('runtime_allowed: orders:read');
  events.push(`db_query: date=${date}, status=paid`);
  const count = orders.filter((order) => order.date === date && order.status === 'paid').length;
  events.push(`db_result: count=${count}`);
  return { events, count };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(JSON.stringify({ allowed: paidOrders('reader', '2025-03-01'),
    denied: paidOrders('guest', '2025-03-01') }, null, 2));
}
