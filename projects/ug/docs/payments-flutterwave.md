# Payments: Flutterwave

## What the prototype does

Every "pay" action on the site (pool seat, rental deposit, weekend deposit, wallet top-up,
subscription) opens one checkout sheet with the amount, a network picker (MTN MoMo, Airtel
Money, card), phone, and email. On **Pay now** the page:

1. builds a Flutterwave v3 inline config;
2. loads `https://checkout.flutterwave.com/v3.js` on demand;
3. calls `FlutterwaveCheckout(config)`;
4. on `callback`, shows the `flw_ref` and status and runs the local success handler (seat
   taken, wallet credited).

The config shape was read first-hand from Flutterwave's official React SDK
(`Flutterwave/React-v3`, `src/types.ts`, cloned from GitHub):

```js
FlutterwaveCheckout({
  public_key: 'FLWPUBK_TEST-…-X',
  tx_ref: 'UG-…',                      // unique per attempt
  amount: 25000,
  currency: 'UGX',
  payment_options: 'mobilemoneyuganda', // or 'card'
  customer: { email, phone_number: '2567…', name },
  customizations: { title: 'UG', description, logo },
  meta: { product: 'ug', label, network },
  callback: (data) => { /* data.flw_ref, data.status, data.transaction_id */ },
  onclose: () => {}
});
```

`mobilemoneyuganda` as the option name and the MTN/Airtel network split come from search
summaries of Flutterwave's Uganda docs *(snippet; the docs host was blocked from this
session)*. Flutterwave notes that `payment_options` only takes effect when "Enable Dashboard
Payment Options" is unchecked in the merchant dashboard *(snippet)*.

## The sandbox fallback

If no real public key is configured, or the checkout script cannot load (offline, blocked
host, the Artifact sandbox), the sheet runs the same sequence locally: "prompt sent", "waiting
for PIN", "approved (simulated)". No money moves, and the status line says so. This exists so
the flow can be reviewed anywhere. The key check is a regex on the `FLWPUBK…-X` format; the
placeholder in the file deliberately fails it.

## What production must add

- **Server-side verification.** Never fulfil on the client callback. Verify
  `transaction_id` against Flutterwave's verify endpoint from a backend, then fulfil.
- **Webhooks.** Register a webhook for `charge.completed`; mobile money approvals can arrive
  after the customer closes the sheet.
- **Split payments.** Use `subaccounts` (present in the SDK types) to route the driver's or
  yard's share at charge time, so UG never holds float it is not licensed to hold.
- **Payouts.** Weekly MoMo payouts to drivers via Flutterwave transfers where split is not
  used.
- **Fees.** Read the live Uganda pricing page (flutterwave.com/ug/pricing) and put the real
  collection rate into the business-plan model.
- **Receipts and statements.** The Executive plan promises a monthly statement; generate it
  from verified transactions only.
