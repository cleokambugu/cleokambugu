// Flutterwave v3: verify a transaction server-side, validate a webhook, create a transfer.
// Contract read first-hand from Flutterwave/React-v3 (client) and from general knowledge of the v3 REST API:
//   GET  https://api.flutterwave.com/v3/transactions/{id}/verify   Authorization: Bearer <secret key>
//   POST https://api.flutterwave.com/v3/transfers                    { account_bank: 'MPS', account_number: '256…', amount, currency: 'UGX', reference, narration }
//   Webhooks carry a `verif-hash` header equal to the secret hash configured in the dashboard.
// Verify every claim against the live docs before production; the docs host was blocked from the build session.
const BASE = process.env.FLW_BASE || 'https://api.flutterwave.com/v3';

export class Flutterwave {
  constructor({ secretKey = process.env.FLW_SECRET_KEY, publicKey = process.env.FLW_PUBLIC_KEY, webhookHash = process.env.FLW_WEBHOOK_HASH, fetchImpl = globalThis.fetch } = {}) {
    this.secretKey = secretKey; this.publicKey = publicKey; this.webhookHash = webhookHash; this.fetch = fetchImpl;
  }
  get live() { return !!this.secretKey; }

  async verify(transactionId) {
    if (!this.live) throw new Error('no FLW_SECRET_KEY');
    const res = await this.fetch(`${BASE}/transactions/${encodeURIComponent(transactionId)}/verify`, { headers: { Authorization: `Bearer ${this.secretKey}` } });
    const body = await res.json();
    if (!res.ok || body.status !== 'success') throw new Error(`verify failed: ${body.message || res.status}`);
    const d = body.data;
    return { ok: d.status === 'successful', status: d.status, amount: d.amount, currency: d.currency, tx_ref: d.tx_ref, flw_ref: d.flw_ref, id: d.id, customer: d.customer };
  }

  // Constant-time compare of the webhook hash header.
  webhookValid(headers) {
    if (!this.webhookHash) return false;
    const h = headers['verif-hash'] || headers['Verif-Hash'] || '';
    if (h.length !== this.webhookHash.length) return false;
    let diff = 0; for (let i = 0; i < h.length; i++) diff |= h.charCodeAt(i) ^ this.webhookHash.charCodeAt(i);
    return diff === 0;
  }

  async transfer({ phone, amount, reference, narration }) {
    if (!this.live) throw new Error('no FLW_SECRET_KEY');
    const res = await this.fetch(`${BASE}/transfers`, { method: 'POST', headers: { Authorization: `Bearer ${this.secretKey}`, 'content-type': 'application/json' },
      body: JSON.stringify({ account_bank: 'MPS', account_number: phone, amount, currency: 'UGX', reference, narration, debit_currency: 'UGX' }) });
    const body = await res.json();
    if (!res.ok || body.status !== 'success') throw new Error(`transfer failed: ${body.message || res.status}`);
    return body.data;
  }
}
