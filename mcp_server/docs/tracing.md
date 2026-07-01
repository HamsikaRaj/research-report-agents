# Tracing and observability

Tracing records a trace per run containing spans for agent steps, model generations,
and tool calls. The built-in processor exports to the OpenAI dashboard. You can add
your own processor with add_trace_processor to also export custom telemetry, for
example tokens, latency, and estimated cost per step, without disabling the default.
Generation spans carry usage data with input and output token counts.
