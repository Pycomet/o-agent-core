# o-agent-core

A minimal, readable AI agent in Python. Give it a natural-language goal, watch the LLM decide which tools to call, and get back a final answer plus a full step-by-step execution trace.

> **NomadBrief** is the travel-brief demo built on top of this engine in the accompanying video. The engine is reusable — bring your own tools and you have your own agent.

## What you get

- **The agent loop** — `goal → LLM decides → call tool → feed result back → repeat → final answer`
- **A starter tool** — `math` (safe AST evaluator) you can use to verify the loop works in seconds
- **A tiny FastAPI** — one endpoint: `POST /api/v1/run-task`
- **Pluggable tools** — subclass `BaseTool`, register it, the agent picks it up automatically
- **No vendor lock-in beyond OpenAI** — swap the LLM client by implementing `LLMClient`

## Run it

```bash
git clone https://github.com/Pycomet/o-agent-core
cd o-agent-core

cp env.example .env
# edit .env and set OPENAI_API_KEY

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Server is at `http://localhost:8000`. Interactive docs at `/docs`.

## Hit it

```bash
curl -X POST http://localhost:8000/api/v1/run-task \
  -H "Content-Type: application/json" \
  -d '{"goal": "What is (12 * 8) + 47?"}'
```

You get back the final answer plus the trace — every tool call the agent made, with arguments and results.

## Add your own tool

1. Create `src/tools/my_tool.py`, subclass `BaseTool`, implement `execute()`.
2. Register it in `src/tools/registry.py` (default tool list).

That's it — the agent will see the new tool's schema and call it when relevant.

## Layout

```
src/
  agent/      — the loop (Agent.execute_task)
  api/        — FastAPI app + /run-task route
  llm/        — LLMClient interface + OpenAI implementation
  schemas/    — request/response Pydantic models
  tools/      — BaseTool, ToolRegistry, MathTool
tests/        — pytest suite (mocked LLM, real tools)
```

## Tests

```bash
pytest
```

All tests run without network or API keys.

## Deploy

- **Backend (Python):** [Railway](https://railway.app) or [Render](https://render.com). Both auto-detect FastAPI and need only `OPENAI_API_KEY` in env.
- **Docker:** `docker compose up --build`

## What's coming next

This repo is the foundation for a video series. Branches preserved for context:

- `backup/full-stack-trigger` — the original architecture with a Trigger.dev + Vercel AI SDK bridge (covered in a later video)

## License

MIT
