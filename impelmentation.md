# HW1 Tool Implementation Plan

This document describes the implementation plan for the five unfinished tools in
`agent/tools.py`. The implementation must follow `SPEC.md`, each function's
docstring, and the existing database/authentication helpers.

## 1. Implementation steps

### 1.1 `get_policy`

1. Load the parsed policy documents with `load_policy_docs()`.
2. Find an exact, case-sensitive match on `policy_id`.
3. Return `ok`, `policy_id`, `title`, `audience`, and the Markdown `body` for a match.
4. Return a structured `not_found` result naming the requested identifier when there is no match.
5. Do not perform an authorization check: policy documents are public to every role.

### 1.2 `search_products`

1. Strip and validate `query`; return `invalid_argument` if it is empty.
2. Validate `max_price_usd` when provided; it must be strictly positive.
3. Clamp `limit` to the inclusive range 1 through `MAX_SEARCH_LIMIT`.
4. If `store` is provided, resolve it with `db.get_store_by_name`; return `not_found` if it does not resolve.
5. Load candidate products with `db.list_products` using the resolved store ID, or all stores when no store is supplied.
6. Keep products where every query token appears case-insensitively in the title or description.
7. Apply the inclusive price ceiling, then sort by price ascending and product ID ascending.
8. Convert results to the required public product fields and return `products` plus `count`.

### 1.3 `list_my_orders`

1. For a shopper, call `db.list_orders_for_user` with `ctx.user_id`.
2. For a merchant, call `db.list_orders_for_store` with `ctx.store_id`.
3. For support, return `invalid_argument` explaining that support staff should look up specific orders instead.
4. Convert each order with `to_public_dict()`.
5. Return `ok`, `orders`, and `count`; rely on the supplied database helpers for newest-first ordering and the 20-order limit.

### 1.4 `cancel_order`

1. Preserve the existing kill-switch check as the first operation.
2. Fetch the order with `db.get_order`.
3. Return `not_found` if the order does not exist.
4. Check access with `can_cancel_order(ctx, order.user_id, order.store_id)` before exposing status information.
5. On a scope failure, return `permission_denied` with a reason naming the role and order ID.
6. If authorized, require the current status to be exactly `placed`; otherwise return `not_eligible` and name the current status.
7. Persist the change with `db.set_order_status` and return `{ok: True, order_id, status: "cancelled"}`.
8. Do not validate or otherwise use `reason` beyond accepting the required tool input.

### 1.5 `find_order`

1. Derive the search scope only from the authenticated context:
   - shopper: `user_id=ctx.user_id`
   - merchant: `store_id=ctx.store_id`
   - support: `all_orders=True`
2. Reject unsupported roles or missing required identity rather than falling back to unrestricted access.
3. Retrieve the complete authorized candidate set with `db.list_order_search_candidates`.
4. Load products and map product IDs to titles.
5. Match the natural-language query against product names using case-insensitive substring or fuzzy matching.
6. Match before applying the result limit, preserving the helper's newest-first order.
7. Return at most five matching orders converted with `to_public_dict()`; return an empty list for no matches.

### 1.6 Verification sequence

1. Run the focused contract tests while implementing:

   ```bash
   uv run pytest --runxfail tests/test_hw_holes.py -k hw1
   ```

2. Run the broader offline tool and authorization checks:

   ```bash
   uv run pytest tests/test_agent_tools.py tests/test_auth.py tests/test_eligibility.py
   ```

3. Inspect the diff and confirm that permissions, kill-switch behavior, and structured result formats were preserved.

## 2. Acceptance criteria

### `get_policy`

- Exact known IDs return the complete policy metadata and body.
- The returned body excludes YAML front matter.
- Unknown IDs return `ok: False` and `error: "not_found"`.
- Shopper, merchant, and support contexts can all read policies.

### `search_products`

- Empty queries and nonpositive price ceilings return `invalid_argument`.
- Unknown stores return `not_found`.
- Matching is token-based and case-insensitive across title and description.
- Price filtering is inclusive, results are sorted deterministically, and limits are clamped to 1–25.
- No matches return a successful empty result.

### `list_my_orders`

- Shoppers see only their own recent orders.
- Merchants see only their store's recent orders.
- Support receives the specified `invalid_argument` response.
- Results are newest first, capped at 20, and use the public order schema.

### `cancel_order`

- The kill switch returns `paused` without changing state.
- Unknown orders return `not_found`.
- Unauthorized callers receive `permission_denied` before status details are revealed.
- Only `placed` orders can be cancelled.
- Successful cancellation persists the new status and returns the exact success schema.

### `find_order`

- Each role is restricted to its authorized order scope.
- Missing identity or unsupported roles never result in unrestricted searching.
- Matching covers the complete authorized scope, not only the 20 most recent orders.
- Results preserve newest-first ordering and are capped at five.
- No matches return `{ "ok": True, "orders": [] }`.

## 3. Potential edge cases

- Policy IDs are case-sensitive; do not normalize them before lookup.
- The policy directory may be missing or malformed; allow unexpected loading errors to surface as execution failures.
- Product queries with repeated whitespace should tokenize cleanly after stripping.
- A query token may occur in a product description but not its title.
- Store matching should support both a case-insensitive store name and slug through `get_store_by_name`.
- `limit` may be zero, negative, very large, non-integer-like, or omitted; follow the contract's clamping behavior without rejecting ordinary out-of-range values.
- `max_price_usd=0` and negative values are invalid; a price exactly equal to the ceiling is valid.
- A valid store can have no matching products; this is a successful empty search, not `not_found`.
- A shopper or merchant may legitimately have no orders; return an empty list and count zero.
- A merchant context without `store_id`, or a shopper context without `user_id`, must not broaden access.
- A support caller has no “own orders” list, but support may search any orders through `find_order`.
- Cancellation must check authorization before status eligibility so an unauthorized caller cannot learn whether an order is shipped.
- An authorized cancellation race or database failure should surface the database exception rather than claiming success.
- `find_order` queries may include conversational filler such as “I bought”; substring/fuzzy matching should still find the product when possible.
- Product names may be duplicated across orders; return each matching order while preserving database ordering.
- More than five matching orders must be truncated only after matching, so older authorized matches are not lost.
- Empty or whitespace-only `find_order` queries should produce no matches rather than broaden the search.
