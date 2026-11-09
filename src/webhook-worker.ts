import { openWebhookDb, receiveWebhook } from './webhook.ts';

const [path, eventId] = process.argv.slice(2);
if (!path || !eventId) throw new Error('Usage: node src/webhook-worker.ts <db-path> <event-id>');
const db = openWebhookDb(path);
try {
  const inserted = receiveWebhook(db, eventId);
  console.log(JSON.stringify({ eventId, inserted }));
} finally {
  db.close();
}
