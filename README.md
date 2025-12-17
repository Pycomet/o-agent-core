# O‑Agent Core

A minimal, production‑minded **LLM Agent Execution Core** built in Python.

This project was implemented as part of the *Python Engineer – LLM Team* task for **O.Foundation**. The goal is not to over‑engineer, but to demonstrate clean architecture, safe tool execution, clear reasoning traces, and readiness for AI‑led organizational workflows.

At its core, this service accepts a natural‑language goal, decides whether to answer directly or use tools, executes those tools safely, and returns a structured result with a full execution trace.

---

## Why this exists

AI‑led systems need more than raw LLM calls. They need:

* A clear execution loop
* Safe, well‑defined tools
* Transparent traces that other systems can inspect
* An API boundary that is easy to integrate and extend

This repository is a small but realistic foundation for that kind of agent.

---

## High‑Level Architecture

**Conceptually:**

```
Client / AI CEO
      ↓
 FastAPI API
      ↓
  Agent Core (Python)
      ↓
 LLM Client (abstracted)
      ↓
 Tool Registry → Tools
      ↓
 Execution Trace + Result
```

**Key ideas:**

* The **Agent** owns decision‑making and state
* **Tools** are isolated, schema‑driven, and safe to call
* The **LLM client** is abstracted so it can later be replaced by a sovereign or internal model
* Every step produces a **machine‑readable trace**

The code is structured so this same agent can be run synchronously via HTTP or asynchronously via an orchestration layer like Trigger.dev.

---

## Core Features

### Agent Execution Core

The `Agent` class:

* Accepts a **goal**, optional **context**, and a set of **tool definitions**
* Uses an LLM to decide whether to answer directly or call tools
* Can call **multiple tools in sequence**
* Maintains execution state:

  * tool calls
  * arguments
  * results
  * timestamps
* Returns a **final structured response**:

```json
{
  "status": "success",
  "output": "...",
  "trace": [...]
}
```

The agent’s internal reasoning is intentionally abstracted, but the structure of each step is preserved for later inspection by an AI CEO or governance layer.

---

## Multi-Runtime Architecture

This project uses a **hybrid Python + Node.js architecture** to leverage the best of both ecosystems:

```
┌─────────────────────────────────────────────────────────────┐
│                      Client / AI CEO                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI (Python) - Agent Core                  │
│  • Agent logic & tool execution                             │
│  • Tool registry                                            │
│  • HTTP API endpoints                                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│            Trigger.dev - Job Orchestration                  │
│  • Reliable job execution                                   │
│  • Automatic retries                                        │
│  • Environment routing (via API key prefixes)               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│         Node.js Job Runner (trigger/llm-jobs.ts)            │
│  • Wraps Vercel AI SDK v5                                   │
│  • Handles streaming & tool calls                           │
│  • Type-safe with Zod schemas                               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│             Vercel AI SDK v5 + OpenAI                       │
│  • Latest AI SDK features                                   │
│  • Native tool calling                                      │
│  • Streaming support                                        │
└─────────────────────────────────────────────────────────────┘
```

**Why this architecture?**

* **Vercel AI SDK v5** is only available in Node.js/TypeScript
* **Agent logic & tools** are better suited to Python's ecosystem
* **Trigger.dev** bridges both runtimes seamlessly
* **Future-proof**: Easy to add sovereign AI models or swap components

---

## Trigger.dev Integration

### 🔑 API Keys & Environment Routing

Trigger.dev uses **API key prefixes** to route requests to different environments:

| API Key Prefix | Environment | Use Case |
|---------------|-------------|----------|
| `tr_dev_*` | Development | Local testing with `npx trigger.dev@latest dev` |
| `tr_prod_*` | Production | Deployed jobs (after `npx trigger.dev@latest deploy`) |

**No environment parameter needed** - just use the right API key!

### How It Works

1. **Development**: 
   - Start dev server: `cd trigger && npx trigger.dev@latest dev`
   - Use `tr_dev_*` API key in `.env`
   - Jobs run locally in your terminal

2. **Production**:
   - Deploy: `cd trigger && npx trigger.dev@latest deploy`
   - Use `tr_prod_*` API key in `.env` or Docker
   - Jobs run on Trigger.dev infrastructure

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM calls | `sk-proj-...` |
| `OPENAI_MODEL` | No | Model to use (default: gpt-4o-mini) | `gpt-4o-mini` |
| `TRIGGER_API_KEY` | Yes | Trigger.dev API key (`tr_dev_*` or `tr_prod_*`) | `tr_prod_...` |
| `TRIGGER_API_URL` | No | Trigger.dev API URL (default: https://api.trigger.dev) | `https://api.trigger.dev` |
| `LLMCLIENT_PROVIDER` | No | LLM client provider (default: vercel) | `vercel` |
| `LOG_LEVEL` | No | Logging level (default: INFO) | `INFO`, `DEBUG` |
| `ENVIRONMENT` | No | Environment name (default: production) | `production`, `development` |
| `HOST` | No | Server host (default: 0.0.0.0) | `0.0.0.0` |
| `PORT` | No | Server port (default: 8000) | `8000` |

**Example `.env` file:**

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Trigger.dev Configuration
TRIGGER_API_KEY=tr_prod_your-key-here
TRIGGER_API_URL=https://api.trigger.dev

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
```

---

## Implemented Tools

### 1. MathTool (`math_evaluate`)

Safely evaluates arithmetic expressions using Python's `ast` module.

**Parameters:**
- `expression` (string): Mathematical expression to evaluate

**Supported operators:** `+`, `-`, `*`, `/`, `**`, `%`, `//`

**Returns:** Numeric result

**Example:**
```json
{
  "expression": "12 * (4 + 6)"
}
```

**Security:** Uses AST parsing with operator whitelist - no arbitrary code execution.

---

### 2. WebSearchTool (`web_search`)

Real web search using DuckDuckGo (free, no API key required). Falls back to mock results if package not installed.

**Parameters:**
- `query` (string): Search query
- `num_results` (integer, optional): Number of results to return (default: 5, max: 10)

**Returns:** List of search results with title, snippet, URL

**Setup:**
1. Install dependency: `pip install ddgs`
2. No API key required - completely free!

**Example:**
```json
{
  "query": "Python best practices 2024",
  "num_results": 5
}
```

**Note:** Includes rate limiting (1 second between searches) to avoid being blocked.

---

### 3. GovernanceNoteTool (`add_governance_note`)

Appends governance notes to an in-memory store keyed by `proposal_id`.

**Parameters:**
- `proposal_id` (string): Unique proposal identifier
- `note` (string): Note content (max 500 characters)

**Returns:** Confirmation with timestamp

**Example:**
```json
{
  "proposal_id": "proposal-42",
  "note": "Technical review passed - approved for implementation"
}
```

**Use cases:**
- Proposal reviews
- Automated governance workflows
- Audit trails for AI decisions

**Note:** Uses in-memory storage. For production, replace with persistent storage (database, IPFS, etc).

---

## HTTP API

The service exposes a minimal FastAPI interface.

### `POST /run-task`

Run a task through the agent.

**Request:**

```json
{
  "goal": "string",
  "context": "optional string",
  "tools": ["optional", "tool", "names"]
}
```

**Response:**

```json
{
  "status": "success",
  "output": "final answer",
  "trace": [ ...step by step execution... ]
}
```

---

### `GET /governance-notes/{proposal_id}`

Retrieve all governance notes for a proposal.

---

## Running the Service

### Requirements

* **Python 3.11+**
* **Node.js 18+** (for Trigger.dev)
* **Docker & Docker Compose** (optional, for containerized deployment)

### Quick Start (Development)

**1. Clone and setup environment:**

```bash
# Copy environment template
cp env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY (from OpenAI)
# - TRIGGER_API_KEY (tr_dev_* for development)
```

**2. Install Python dependencies:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Install Node.js dependencies (for Trigger.dev):**

```bash
cd trigger
npm install
cd ..
```

**4. Start everything at once:**

```bash
./start-dev.sh
```

This script will:
- Start Trigger.dev dev server in background
- Build and start Docker container with the Python API

**Or start services individually:**

```bash
# Terminal 1: Start Trigger.dev dev server
cd trigger
npx trigger.dev@latest dev

# Terminal 2: Start Python API
python main.py
# Or with auto-reload:
uvicorn src.api.app:app --reload
```

### Access the Service

* **API**: [http://localhost:8000](http://localhost:8000)
* **Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Docker Deployment

### Development with Docker Compose

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Deployment

**1. Update environment variables:**

```bash
# In docker-compose.yml or .env file:
TRIGGER_API_KEY=tr_prod_your-production-key-here
OPENAI_API_KEY=your-openai-key-here
ENVIRONMENT=production
```

**2. Deploy Trigger.dev jobs:**

```bash
cd trigger
npx trigger.dev@latest deploy
```

**3. Start the service:**

```bash
docker-compose up -d
```

**Important:** Make sure to set `OPENAI_API_KEY` in your Trigger.dev dashboard environment variables for production jobs!

---

## Example Tasks

### Single‑Tool Usage

**Goal:**

```
Calculate 12 * (4 + 6)
```

The agent chooses `MathTool`, executes it, and returns the result with a trace.

---

### Multi‑Step Tool Usage

**Goal:**

```
Search for Python best practices and summarize what you find
```

The agent:

1. Calls `WebSearchTool`
2. Uses the results to generate a final answer
3. Returns a structured trace of both steps

---

### Governance Workflow

**Goal:**

```
Add a governance note to proposal-42 saying the technical review passed
```

The agent extracts the proposal ID and note content, calls `GovernanceNoteTool`, and stores the note.

---

## Code Structure

```
src/
├── agent/      # Agent core and execution logic
├── tools/      # Tool definitions and registry
├── llm/        # LLM client abstraction
├── api/        # FastAPI routes
├── storage/    # In‑memory governance store
└── schemas/    # Pydantic models
```

Each layer is intentionally small and readable. The goal is clarity over cleverness.

---

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Suite

```bash
# Test tools
pytest tests/test_tools.py -v

# Test agent
pytest tests/test_agent.py -v

# Test API
pytest tests/test_api.py -v
```

### Test Coverage

```bash
pytest --cov=src --cov-report=html
```

---

## Extending This Core

This project is designed to be extended, not rewritten.

### Possible Extensions

* **Persistent Storage**: Replace in‑memory storage with PostgreSQL, Redis, or decentralized stores (IPFS/Arweave)
* **On-Chain Tools**: Add tools for governance and treasury management on blockchain
* **Scheduled Jobs**: Use Trigger.dev's scheduled tasks for recurring workflows
* **Custom LLM**: Swap OpenAI for sovereign or internal AI models via the `LLMClient` interface
* **More Tools**: Add tools for email, Slack, GitHub, database queries, etc.
* **Streaming**: Add SSE/WebSocket support for real-time agent responses
* **Multi-Agent**: Coordinate multiple specialized agents for complex tasks

The abstractions are already in place to support these extensions.

---

## Troubleshooting

### Common Issues

**"Invalid API key" from OpenAI:**
- Check `OPENAI_API_KEY` is set correctly in `.env`
- For Trigger.dev jobs, also set it in the Trigger.dev dashboard

**Trigger.dev jobs not running:**
- Make sure `npx trigger.dev@latest dev` is running for development
- For production, ensure jobs are deployed: `npx trigger.dev@latest deploy`
- Check API key prefix matches environment (`tr_dev_*` vs `tr_prod_*`)

**WebSearchTool returns mock results:**
- Install DuckDuckGo package: `pip install ddgs`
- Check for rate limiting (1 second between searches)

**Docker container won't start:**
- Check all required environment variables are set
- Review logs: `docker-compose logs -f`
- Ensure ports 8000 is not already in use

---

## License

Built as a test task for **O.Foundation**.

---

## References
- Trigger.dev docs: https://trigger.dev/docs
- Vercel AI SDK docs: https://sdk.vercel.ai/docs
- My website: https://www.codefred.dev
