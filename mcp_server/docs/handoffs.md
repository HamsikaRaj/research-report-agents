# Handoffs

A handoff lets one agent delegate the conversation to another agent. Handoffs are
exposed to the model as tools named transfer_to_<agent_name>. You configure them
with the handoffs parameter on an Agent, optionally wrapping a target in handoff()
to add an on_handoff callback or an input_type that forces structured arguments.
In this project the Planner hands off to the Executor, which hands off to the
Reviewer.
