# Courier Dispatch Policy

## Dispatch Timing
- A courier must be dispatched at the same moment an order is received (not when it is ready).
- This ensures the courier arrives close to when the order completes prep.

## Arrival Window
- Couriers arrive uniformly between 3 and 15 seconds after dispatch (simulation units).
- In production: couriers arrive 3–15 minutes after dispatch.

## No-Show Definition
- A courier is considered a no-show if they have not arrived within 25 minutes of dispatch.
- On no-show: Dispatch agent must immediately dispatch a replacement courier.
- No-show events are logged and trigger a customer notification via the Support agent.

## Assignment Strategies
- Matched: each order is pre-assigned to one courier at dispatch time. Courier waits for their specific order.
- FIFO: couriers pick up the next available ready order upon arrival. No pre-assignment.
- Agentic: Dispatch LLM agent decides per order based on kitchen load, courier ETAs, and batch opportunities.

## Courier Wait Limit
- A courier should not wait more than 10 minutes for a pre-assigned order (Matched strategy).
- If the order is not ready within 10 minutes of courier arrival, the Dispatch agent may re-assign the courier.

## Batching (Agentic strategy only)
- The Dispatch agent may hold a courier for up to 60 seconds to batch two nearby orders.
- Batching is only allowed if it does not cause either order to exceed the food quality window (10 minutes ready).
