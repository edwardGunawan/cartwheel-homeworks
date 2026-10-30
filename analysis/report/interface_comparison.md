# Review interface comparison

## Retained

The new interface retains the reference's tool-call/result containers, selection-based free-form notes in a right margin, explicit acceptance/rejection of AI suggestions, and local autosaving. These keep annotations near their evidence while separating suggestions from human judgments.

## Changed after inspecting live traces

Eight complete live Langfuse traces were inspected: `d54d4cdb8ed096d36fff87e77781c958`, `a826cb29488dec3fffe96da6edba4262`, `421280fdf8cf6092ecd2959c13a1d62a`, `5a69969611ece19624ef820708d4982b`, `689a5d72dd6f9ac87442cd6ba689f8bf`, `4dc9730420a976c7e2a5f6e4d3216f72`, `b47e23a2532a00e200e74ffd0c6f5ae4`, and `2f9484f6dba9c0c1c460f82e4c57c309`.

The first two traces share a session and contain an order search followed by a product-name clarification. Single-trace navigation would hide that preceding context. The new interface groups by `metadata.attributes.cartwheel.session_id`, orders turns chronologically, and preserves each turn's trace ID for notes and binary scores. Grouping by scenario alone would incorrectly join separate runs with reused scenario IDs.

Trace-level `sessionId` and `userId` were null in the inspected records, so the app reads the application attributes. It renders order records as tables, ranked retrieval snippets as evidence cards, and full fetched policy documents separately. Repeated generation inputs remain available in raw execution details rather than being rendered repeatedly in the timeline. System content retains full readability. An execution adapter preserves tool-call IDs and marks its inferred call/result pairing.

The proposed design was approved before interface implementation. The live project subsequently loaded 388 traces in 362 sessions. This is a collection count, not the number reviewed by the student. The standard Langfuse annotation screen was not directly evaluated during this implementation; observations above come from its live API records. No offline fallback was needed. Student observations about the standard view and comparisons with preliminary Workshop runs remain pending.

## Remaining limitation

Some tool results include only product/store identifiers rather than names, and tool execution spans do not expose the model's tool-call ID. The interface preserves the original values, retains raw records, and discloses inferred matching by function, arguments, parent and time; it cannot reconstruct uncaptured evidence. Concurrent identical calls under the same parent can be ambiguous. Structural map points with identical features can overlap, so the searchable queue remains the reliable way to reach every trace.
