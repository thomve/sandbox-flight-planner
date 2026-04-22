# Flight Planner Sandbox

Sandbox project demonstrating an agentic flight planning system.
The agent uses LangGraph (ReAct loop) to orchestrate calls to a local FastAPI server
that exposes mock flight and user data.

## Project layout

```
src/
├── api/            # FastAPI mock server
│   ├── models.py   # Pydantic models (Flight, User, UserPreferences, …)
│   ├── data.py     # In-memory mock data (airports, flights, users)
│   ├── routes.py   # All HTTP endpoints + scoring/ranking logic
│   └── main.py     # FastAPI app factory + uvicorn entry point
└── agent/          # LangGraph agent
    ├── state.py    # AgentState TypedDict
    ├── config.py   # LLM factory (Anthropic / Azure OpenAI)
    ├── tools.py    # LangChain tools — thin wrappers around HTTP calls
    ├── graph.py    # LangGraph ReAct graph (agent ↔ tools loop)
    └── main.py     # CLI entry point (rich interactive REPL)
```

## Stack

| Layer | Technology |
|-------|-----------|
| Package management | `uv` + `pyproject.toml` |
| API server | FastAPI + Uvicorn |
| Agent orchestration | LangGraph |
| LLM (option A) | Anthropic Claude via `langchain-anthropic` |
| LLM (option B) | Azure OpenAI via `langchain-openai` |
| HTTP client (tools) | httpx (sync) |
| CLI UX | rich |

## Setup

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in your API keys
```

## Running

### Start the API server (terminal 1)

```bash
uv run flight-api
# Docs available at http://localhost:8000/docs
```

### Start the agent (terminal 2)

```bash
# Anthropic Claude (default)
uv run flight-agent

# Azure OpenAI
uv run flight-agent --provider azure_openai

# With a user context for personalized recommendations
uv run flight-agent --user-id user-001

# All options
uv run flight-agent --provider anthropic --user-id user-002 --api-url http://localhost:8000
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/airports` | List all airports |
| GET | `/airports/{code}` | Get airport by IATA code |
| GET | `/search-flights` | Search flights (origin, destination, optional filters) |
| GET | `/flights/{id}` | Get flight details |
| POST | `/flights/compare` | Compare & rank a set of flights |
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get user profile |
| GET | `/users/{id}/preferences` | Get user preferences |
| PUT | `/users/{id}/preferences` | Update user preferences |
| GET | `/users/{id}/recommendations` | Personalized ranked recommendations |

### Key query params for `/search-flights`

| Param | Type | Description |
|-------|------|-------------|
| `origin` | string | IATA code (required) |
| `destination` | string | IATA code (required) |
| `max_stops` | int | 0 = direct only |
| `max_price_eur` | float | Price ceiling |
| `max_co2_kg` | float | CO₂ ceiling |
| `cabin_class` | string | economy \| business \| first |

## Mock data

**Airports**: CDG · LHR · JFK · LAX · AMS · FRA · BCN · MAD · DXB · SIN

**Routes**:
- CDG → JFK: Air France, Delta, British Airways (1-stop), French Bee
- CDG → BCN: Air France, Vueling, Ryanair
- AMS → SIN: KLM, Singapore Airlines, Emirates (1-stop via DXB)
- FRA → LAX: Lufthansa, United Airlines

**Users**:
| ID | Name | Priority |
|----|------|----------|
| user-001 | Alice Martin | CO₂ (max 430 kg, direct only) |
| user-002 | Bob Dupont | Price (max €500) |
| user-003 | Carol Smith | Comfort (business preferred) |
| user-004 | David Chen | Balanced (max €800) |

## Agent architecture

```
User
 │
 ▼
CLI (rich REPL)  ──  HumanMessage  ──►  LangGraph graph
                                              │
                                    ┌─────────▼──────────┐
                                    │    agent node       │
                                    │  LLM + bound tools  │
                                    └─────────┬──────────┘
                                              │ tool_calls?
                                    ┌─────────▼──────────┐
                                    │    tools node       │
                                    │   ToolNode (httpx)  │
                                    └─────────┬──────────┘
                                              │ ToolMessages
                                              └──► agent node  ──► AIMessage ──► User
```

The graph follows the standard ReAct pattern:
**think → act (tool call) → observe → repeat** until the agent returns a final answer.

## Flight scoring

Flights are scored on a 0–1 scale using a weighted sum of three normalized metrics:

| Criterion | price weight | co₂ weight | comfort weight |
|-----------|-------------|-----------|----------------|
| `price`   | 0.70 | 0.15 | 0.15 |
| `co2`     | 0.15 | 0.70 | 0.15 |
| `comfort` | 0.15 | 0.15 | 0.70 |
| `balanced`| 0.33 | 0.33 | 0.34 |

Lower price/CO₂ and higher comfort score all increase the score.

## Development notes

- The API holds state **in memory** — restarting the server resets user preferences.
- Add new mock flights in `src/api/data.py` (`FLIGHTS` dict).
- Add new airports in `src/api/data.py` (`AIRPORTS` dict).
- To add a new tool: add an `@tool`-decorated function inside `get_tools()` in
  `src/agent/tools.py` and include it in the returned list.
- The LLM provider is selected at runtime via `--provider`; both providers bind
  the same tool list, so switching is transparent.
