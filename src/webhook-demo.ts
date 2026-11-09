import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { countDeliveries, openWebhookDb } from './webhook.ts';

export function runWorker(path: string, eventId: string): Promise<{ eventId: string; inserted: boolean }> {
  return new Promise((resolve, reject) => {
    const worker = fileURLToPath(new URL('./webhook-worker.ts', import.meta.url));
    const child = spawn(process.execPath, [worker, path, eventId], { stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8').on('data', (part: string) => { stdout += part; });
    child.stderr.setEncoding('utf8').on('data', (part: string) => { stderr += part; });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code !== 0) reject(new Error(`worker exited ${code}: ${stderr}`));
      else resolve(JSON.parse(stdout.trim()) as { eventId: string; inserted: boolean });
    });
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const temp = mkdtempSync(join(tmpdir(), 'llm-manual-webhook-'));
  try {
    const path = join(temp, 'deliveries.sqlite');
    const initial = openWebhookDb(path);
    initial.close();
    const results = await Promise.all([runWorker(path, 'evt-42'), runWorker(path, 'evt-42')]);
    const db = openWebhookDb(path);
    try {
      console.log(JSON.stringify({ workerResults: results, rowsForEvent: countDeliveries(db, 'evt-42'),
        caveat: 'The unique row proves this database property only; external side effects need separate tests.' }, null, 2));
    } finally { db.close(); }
  } finally { rmSync(temp, { recursive: true, force: true }); }
}
