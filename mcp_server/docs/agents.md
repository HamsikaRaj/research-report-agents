# Agents and Runner

An Agent bundles instructions, a model, tools, handoffs, guardrails, and an
optional output_type. The Runner executes an agent loop: it calls the model,
runs any requested tools, follows handoffs to other agents, and stops when the
active agent produces a final output. Runner.run is async. Runner.run_streamed
returns a streaming result whose events can be consumed token-by-token.
