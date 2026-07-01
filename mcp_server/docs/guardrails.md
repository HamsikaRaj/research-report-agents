# Guardrails

Guardrails validate data crossing the system boundary. Input guardrails run before
the agent on the user input. Output guardrails run on the final output. Each returns
a GuardrailFunctionOutput with a tripwire_triggered flag. When a tripwire trips, the
SDK raises InputGuardrailTripwireTriggered or OutputGuardrailTripwireTriggered and
halts the run. Guardrails can be cheap deterministic checks or a separate LLM call.
