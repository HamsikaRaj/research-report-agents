# Streaming

Runner.run_streamed runs an agent and returns a streaming result. Iterating
result.stream_events() yields raw_response_event items (token-level deltas from the
Responses API), run_item_stream_event items (semantic events such as tool_called and
message_output_created), and agent_updated_stream_event items (emitted on handoffs).
The run is only complete once the async iterator is exhausted. The same events can be
relayed to a browser over Server-Sent Events.
