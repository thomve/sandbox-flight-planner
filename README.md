# Sandbox Flight Planner

An agentic flight planning application built with **LangGraph** and **FastAPI**.
A conversational AI agent helps users find flights ranked by CO₂ emissions, price,
and comfort — pulling live data from a local mock REST API.

## Architecture

```
User ──► CLI agent (LangGraph ReAct loop)
               │
               ├── search_flights
               ├── compare_flights        ──► FastAPI server (mock data)
               ├── get_user_recommendations
               └── update_user_preferences
```

The agent follows a **think → call tool → observe → repeat** cycle until it has
enough information to answer the user.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`pip install uv` or via the installer)
- An **Anthropic API key** (or Azure OpenAI credentials)

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd sandbox-flight-planner

# 2. Install dependencies
uv sync

# 3. Configure environment variables
cp .env.example .env
```

Open `.env` and fill in at least one provider:

```dotenv
# For Anthropic Claude (default)
ANTHROPIC_API_KEY=sk-ant-...

# For Azure OpenAI (optional alternative)
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## Running the app

You need **two terminals** — one for the API server, one for the agent.

### Terminal 1 — API server

```bash
uv run flight-api
```

The server starts on `http://localhost:8000`.
Interactive docs are available at `http://localhost:8000/docs`.

### Terminal 2 — Agent

```bash
# Default (Anthropic Claude, no user context)
uv run flight-agent

# With a user profile for personalized recommendations
uv run flight-agent --user-id user-001

# Use Azure OpenAI instead
uv run flight-agent --provider azure_openai

# All options
uv run flight-agent --provider anthropic --user-id user-002 --api-url http://localhost:8000
```

Type your request in plain language, e.g.:

```
You: Find me flights from CDG to JFK and rank them by CO₂
You: Which is the cheapest direct flight from Amsterdam to Singapore?
You: What are my preferences? (with --user-id user-001)
You: Update my max CO₂ to 400 kg
```

Type `exit` or press `Ctrl+C` to quit.

## Mock data

### Available routes

| Route | Airlines |
|-------|---------|
| CDG → JFK | Air France · Delta · British Airways · French Bee |
| CDG → BCN | Air France · Vueling · Ryanair |
| AMS → SIN | KLM · Singapore Airlines · Emirates |
| FRA → LAX | Lufthansa · United Airlines |

### User profiles

| ID | Name | Priority | Notes |
|----|------|----------|-------|
| `user-001` | Alice Martin | CO₂ | Direct only, max 430 kg |
| `user-002` | Bob Dupont | Price | Max €500 |
| `user-003` | Carol Smith | Comfort | Business class preferred |
| `user-004` | David Chen | Balanced | Max €800 |

### Airport codes

`CDG` `LHR` `JFK` `LAX` `AMS` `FRA` `BCN` `MAD` `DXB` `SIN`

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/airports` | List all airports |
| GET | `/search-flights?origin=CDG&destination=JFK` | Search flights with optional filters |
| GET | `/flights/{id}` | Get a single flight's details |
| POST | `/flights/compare` | Rank a set of flights by criterion |
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get user profile and preferences |
| GET | `/users/{id}/preferences` | Get preferences only |
| PUT | `/users/{id}/preferences` | Update preferences |
| GET | `/users/{id}/recommendations?origin=CDG&destination=JFK` | Personalized ranked results |

Optional query params for `/search-flights`:

| Param | Type | Description |
|-------|------|-------------|
| `max_stops` | int | `0` = direct flights only |
| `max_price_eur` | float | Price ceiling |
| `max_co2_kg` | float | CO₂ ceiling |
| `cabin_class` | string | `economy` · `business` · `first` |

## Flight scoring

Flights are scored 0–1 using a weighted sum of normalized metrics.

| Criterion | Price weight | CO₂ weight | Comfort weight |
|-----------|:-----------:|:----------:|:--------------:|
| `price`   | 0.70 | 0.15 | 0.15 |
| `co2`     | 0.15 | 0.70 | 0.15 |
| `comfort` | 0.15 | 0.15 | 0.70 |
| `balanced`| 0.33 | 0.33 | 0.34 |

## Project structure

```
src/
├── api/
│   ├── models.py    # Pydantic models
│   ├── data.py      # In-memory mock data
│   ├── routes.py    # Endpoints + scoring logic
│   └── main.py      # FastAPI app + uvicorn entry point
└── agent/
    ├── state.py     # LangGraph AgentState
    ├── config.py    # LLM factory (Anthropic / Azure OpenAI)
    ├── tools.py     # LangChain tools (HTTP wrappers)
    ├── graph.py     # LangGraph ReAct graph
    └── main.py      # Interactive CLI
```
