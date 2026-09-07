# Signing in: your line is enough

The account is the phone line. In Uganda a line already is an identity — it is registered, it
carries the mobile-money wallet, and it is the thing people give each other. So UG does not ask
for a password, an email or a form. It asks which line you are on, confirms it, and you are in.

The target is **under a minute from installing to riding**, and the honest way to hit it is to
need almost nothing.

## The rule that makes it fast

**Looking costs nothing.** Comparing every price on the market, turning the map, reading the
Atlas, planning a park weekend — none of it needs an account. The account is only required at the
moment money moves. So the first minute is spent on the trip, not on you.

In the code that is `requireAccount(fn)`: run it if signed in, otherwise sign in and then run it.
Tapping **Book on UG** on a quote signs you in and lands you on the checkout for that same quote;
nothing is retyped and nothing is lost.

## The fast path: the line in the phone

1. **The app reads the SIM.** On Android that is `SubscriptionManager.getActiveSubscriptionInfoList()`,
   on iOS the carrier information — so the number is already known and never typed.
2. **Dual SIM gets a chooser.** Two SIMs is the norm here, not an edge case: MTN for one thing,
   Airtel for another. UG asks which line it should be, shows the operator and the slot, and that
   line becomes the account and the wallet.
3. **The operator confirms the line, silently.** Over mobile data the carrier can confirm that the
   device really is that number — the GSMA Mobile Connect work, now standardised as the
   [CAMARA Number Verification API](https://camaraproject.org/). No SMS, no code, about a second.
4. **Otherwise an SMS code that types itself.** On wifi, roaming, or when the carrier check is
   unavailable, UG sends a code and the phone fills it in through the
   [Web OTP API](https://developer.mozilla.org/en-US/docs/Web/API/WebOTP_API) (`OTPCredential`)
   or Android SMS Retriever. There is still nothing to read or type.
5. **Your records come back.** A line that has used UG before returns to its trips, stages,
   vouches and wallet. "Welcome back" is literal: the line is the key.

Two taps on a phone that has one SIM. Three if you have two.

## What a web page genuinely cannot do

A browser **cannot read a SIM**. There is no web API for it and there should not be. So:

- In the **installed app**, steps 1–3 above are real.
- On the **web**, the sheet shows the chooser with clearly-marked sandbox lines, says on screen
  that a web page cannot read a SIM, and falls straight through to *Use another number*.

The sheet carries a one/two/no-SIM switch so all three cases can be seen without a phone. It is
labelled sandbox. Nothing here pretends the browser did something it cannot.

## Visitors: no Ugandan line, still no dead end

A tourist landing at Entebbe has a phone, a foreign number that may not receive SMS cheaply, and
hotel wifi. Every one of these gives the same account, wallet and trip history:

| Way in | Why it suits a visitor |
| --- | --- |
| **Passkey** (WebAuthn, Face or fingerprint) | No password, no SMS, no network dependency. The fastest and the safest. |
| **Google or Apple** | They are already signed in on the phone; it is one tap. |
| **WhatsApp code** | Works on hotel wifi with their own foreign number — no roaming SMS, no charge. WhatsApp is already how East Africa talks. |
| **Their own number, roaming** | Any international line, standard SMS code. |
| **A Ugandan eSIM, bought in UG** | The interesting one: order an eSIM from MTN or Airtel inside the app, install it from a QR code, and in about a minute they have a local number *and* data — which also unlocks mobile money. Their home SIM keeps taking calls. |
| **Stay a guest** | Compare everything and book with a card. The account materialises after the first trip. |

Payment follows the same logic: **MoMo needs a Ugandan line; a card does not.** A visitor is never
blocked from paying, only from the wallet that requires a local number.

## Roles come later, not at the door

Being a driver or renting out a car needs more — a Comfort Map, documents, verification. None of
that belongs in the way of a first ride. Signing in creates a rider; the driver and owner steps
live behind the Drive door and Me, and they can be done at leisure. The old flow asked for all of
it up front, which is exactly what made it slow.

## What is real in this build

- **Real:** the sheet, the dual-SIM chooser, the fallbacks, the one-tap continue, the pending
  action resuming into checkout, the Web OTP call where the browser supports it
  (`'OTPCredential' in window`), and `requireAccount` gating only payment.
- **Sandbox:** the SIM lines on the web (labelled), the operator verification (the server exposes
  `POST /api/auth/number-verify`, which answers `verified:false, sandbox:true` and says why), the
  passkey and social sign-ins, the WhatsApp channel, and the eSIM purchase.
- **Needs a contract before it is live:** an MTN or Airtel Number Verification agreement, a
  WhatsApp Business sender, an eSIM reseller arrangement, and a real WebAuthn relying party.

Nothing above is a live carrier integration today. The flow, the fallbacks and the honesty about
which is which are what this build delivers.
