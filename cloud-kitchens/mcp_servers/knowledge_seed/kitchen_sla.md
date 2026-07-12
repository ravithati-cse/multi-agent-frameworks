# Kitchen SLA Policy

## Prep Time Targets
- Standard orders: prep must complete within the item's stated prepTime + 2 minutes buffer.
- Rush orders (priority=high): prep must complete within stated prepTime + 30 seconds.
- SLA breach: if prep exceeds target, the Kitchen agent must emit an SLA_BREACH event.

## Station Capacity
- Each kitchen station handles a maximum of 10 concurrent orders.
- If all stations are at capacity, new orders enter a holding queue.
- The Ops Supervisor agent monitors station utilization and alerts if any station exceeds 80% for more than 5 minutes.

## Order Ready Handling
- Once an order status is "ready", it must be picked up within 10 minutes.
- After 10 minutes, food quality is degraded and the Kitchen agent should flag the order.
- After 20 minutes, the order must be remade at kitchen cost (no charge to customer).

## Inter-agent Coordination
- Kitchen agent notifies Dispatch agent immediately on OrderReady.
- Kitchen agent notifies Inventory agent after each order to deduct consumed ingredients.
- Kitchen agent may request ingredient substitution from Inventory agent if a stockout occurs mid-prep.
