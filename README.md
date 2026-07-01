# Research-and-Report Agents

A multi-agent system built on the OpenAI Agents SDK. It takes a research question,
breaks it into steps, gathers evidence with tools and a Model Context Protocol (MCP)
server, and returns a validated, structured answer. I built it to get hands-on
experience with the OpenAI Agents SDK, the Responses API, and MCP, porting a research
pipeline I had originally written in LangGraph over to the OpenAI stack.

Three agents share the work. A Planner breaks the question into steps and hands it
off. An Executor runs the tools and collects grounded evidence. A Reviewer checks the
result and produces the final structured output. The run streams token by token to
both a command-line interface and an HTTP endpoint, and every step is traced for
tokens, latency, and cost.

## Architecture

```
User query
   |
   v  input guardrail (PII / empty)
Planner (gpt-4o)
   |  handoff() with a structured plan
   v
Executor (gpt-4o-mini)  --->  web_search, compute_metric, save_report (function tools)
   |                          list_docs, docs_lookup (MCP server, stdio)
   |  handoff() when research is complete
   v
Reviewer (gpt-4o)
   |  output guardrail (groundedness)
   v
ReportResult  { answer, sources[], confidence, reviewer_notes }
```

The Planner never answers the question. It plans and delegates. The Executor gathers
evidence and tracks which tool or doc each fact came from, then hands off to the
Reviewer. The Reviewer is the only agent with an `output_type`, so the pipeline
always ends in a typed, guardrail-checked `ReportResult`.

## Repository layout

```
research-report-agents/
  research_agents/     planner, executor, reviewer, schemas, pipeline assembly
  tools/               three function tools with Pydantic-validated arguments
  mcp_server/          the MCP server I built, plus a small local docs set
  guardrails/          input (PII) and output (groundedness) guardrails
  observability/       custom tracing processor and a cost summary script
  evals/               golden set, LLM judge, report, and a pytest regression gate
  api/                 FastAPI server with a streaming SSE endpoint
  main.py              command-line entry point
  config.py            models, pricing, and paths (secrets come from the environment)
```

A note on the package name. The SDK's own importable package is `agents`. A local
folder with that name would sit earlier on the import path and shadow the SDK, so the
local package is named `research_agents` instead. Every other folder matches its role.

## Setup

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then add your real OPENAI_API_KEY to .env
```

Secrets live only in `.env`, which is gitignored. Nothing is hardcoded. `config.py`
reads models and keys from the environment.

## Running it

```
# Command line, streamed to the console
python main.py "How do handoffs work in the Agents SDK?"

# Ask it to save a report, which triggers the human approval gate
python main.py "Summarize tracing, then SAVE a report about it"

# API: stream the same run over Server-Sent Events
uvicorn api.server:app --reload
curl -N -X POST localhost:8000/stream \
  -H 'content-type: application/json' -d '{"query":"What does MCPServerStdio do?"}'

# Evaluation report over all 15 golden cases
python -m evals.report

# Regression gate (fails if scores drop below thresholds)
pytest evals/test_regression.py -v

# Token, latency, and cost rollup from the run log
python -m observability.summarize
```

## How each part works

**Agents and handoffs.** Each agent has its own instructions and model. The Planner
uses `handoff()` with an `input_type`, so it must produce a real plan before control
moves to the Executor. The Executor lists the MCP tools, gathers evidence, then hands
off to the Reviewer. See `research_agents/`.

**Function tools.** `web_search`, `compute_metric`, and `save_report` are plain Python
functions wrapped with `@function_tool`. Their arguments are Pydantic models, so the
model cannot pass invalid input. See `tools/research_tools.py`.

**Structured output.** The Reviewer sets `output_type=ReportResult`, so the pipeline
returns a typed object with an answer, a list of sources, a confidence score, and a
short review note, rather than free text. A helper called `ensure_report` guarantees
this even if the Executor skips the handoff, so validation is never optional.

**MCP server.** `mcp_server/server.py` is a small MCP server I wrote with FastMCP. It
exposes two tools, `list_docs` and `docs_lookup`, over stdio. The Executor consumes it
through `MCPServerStdio`, which launches the server as a subprocess. The same standard
server could be consumed by any MCP client. If it were deployed behind a URL you would
switch to `HostedMCPTool`.

**Guardrails.** The input guardrail blocks empty or oversized queries and obvious PII.
The output guardrail rejects a final answer that cites no sources. Both are
deterministic, which keeps them fast and easy to reason about. See `guardrails/`.

**Human in the loop.** `save_report` is the only write action. It is marked
`needs_approval=True`, so the run pauses as an interruption and waits for a person to
approve or reject the write before anything is saved to disk.

**Streaming.** `Runner.run_streamed` produces events that are rendered token by token.
The command line prints them directly. The FastAPI endpoint forwards each token and
lifecycle event to the browser as a `data:` SSE frame.

**Retries.** The command-line runner retries transient failures with backoff and fails
fast on non-transient ones such as an invalid key or an exhausted quota, since
retrying those would not help.

**Observability.** A custom tracing processor runs alongside the built-in tracer and
writes one JSONL line per model step with the model name, input and output tokens,
latency, and estimated cost. `observability/summarize.py` rolls those up. The totals
reconcile exactly with the SDK's own usage counter.

**Evaluation.** `evals/golden.json` holds 15 question and reference-answer pairs. For
each one the harness runs the full pipeline, then an LLM judge scores the answer on
accuracy, groundedness, and faithfulness. `evals/report.py` prints per-metric averages
and `evals/test_regression.py` fails if any average drops below its threshold.

## Metrics

These come from live runs. The models are gpt-4o for the Planner, Reviewer, and Judge,
and gpt-4o-mini for the Executor.

Per research query:

| Measure | Value |
| --- | --- |
| Model calls | 8 (2 gpt-4o, 6 gpt-4o-mini) |
| Tokens | 7,967 (7,623 in, 344 out) |
| Estimated cost | $0.0061 |
| Mean step latency | about 2 seconds |

Evaluation over 15 golden cases, judged by gpt-4o:

| Metric | Score |
| --- | --- |
| Accuracy | 0.95 |
| Groundedness | 0.95 |
| Faithfulness | 0.95 |
| Overall | 0.95 |

The judge scores each metric from 0 to 1, where higher is better. Faithfulness is 1.0
when the answer contains no fabricated or contradictory claims. The regression gate
requires each average to stay above 0.85.

## Notes and next steps

The `web_search` tool reads a small local corpus so the repository runs with only an
OpenAI key. A real search backend or vector database can drop in behind the same
function signature. The guardrails are deterministic today and could be swapped for an
LLM-based guardrail for fuzzier policies. The SSE endpoint is non-interactive, so it
reports an approval request and declines the write, while the command line is where a
person actually approves.
