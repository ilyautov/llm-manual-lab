import { DatabaseSync } from 'node:sqlite';

export function openWebhookDb(path: string): DatabaseSync {
  const db = new DatabaseSync(path);
  db.exec('PRAGMA busy_timeout = 5000');
  db.exec('CREATE TABLE IF NOT EXISTS deliveries (event_id TEXT NOT NULL UNIQUE, received_at TEXT NOT NULL)');
  return db;
}

export function receiveWebhook(db: DatabaseSync, eventId: string): boolean {
  if (!eventId) throw new Error('event_id is required');
  const result = db.prepare(
    "INSERT INTO deliveries (event_id, received_at) VALUES (?, '2025-03-01T00:00:00Z') ON CONFLICT(event_id) DO NOTHING",
  ).run(eventId);
  return result.changes === 1;
}

export function countDeliveries(db: DatabaseSync, eventId: string): number {
  const row = db.prepare('SELECT COUNT(*) AS count FROM deliveries WHERE event_id = ?').get(eventId) as { count: number };
  return row.count;
}
