# Refund Policy

## Automatic Refunds (no approval needed)
- Refunds up to $20.00 USD may be issued by the Support or Payment agent automatically.
- Eligible reasons: order never arrived, wrong items delivered, food quality complaint with photo evidence.

## Supervised Refunds (approval required)
- Refunds above $20.00 USD must be approved by the Ops Supervisor agent before the Payment agent issues them.
- The Payment agent must receive an explicit Approval.request event in the trace before calling refund_payment for amounts above the threshold.
- Attempting to issue a large refund without approval is a policy violation and will be flagged.

## Cancellation Refunds
- Orders cancelled before prep starts: 100% refund, automatic.
- Orders cancelled during prep: 50% refund, automatic.
- Orders cancelled after ready status: no refund unless courier no-show is confirmed.

## Courier No-Show
- If a courier fails to arrive within 25 minutes of dispatch, the system flags a no-show.
- A confirmed no-show entitles the customer to a full refund regardless of order amount.
- The Dispatch agent must log the no-show event before a refund can be issued.
