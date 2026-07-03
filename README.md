# Agentic AI for DevOps — Masterclass

A simple LangChain agent that uses a local LLM (via [Ollama](https://ollama.com)) to answer Kubernetes and Docker questions by calling real `kubectl` and `docker` commands as tools.

Built as part of the **TrainWithShubham** masterclass.

## What it does

The agent is wired up with two tools:

- `get_pods` — runs `kubectl get pods -A` and returns the output
- `get_docker_containers` — runs `docker ps` and returns the output

You ask a question in natural language; the LLM decides which tool to call and answers based on the live cluster / Docker state.

## Key concepts (30-second glossary)

| Term | In one line |
|------|-------------|
| **Agent** | An LLM + tools + a loop that lets the model decide *which* tool to call. |
| **Tool** | A plain Python function the LLM can call. Its **docstring** is what the model reads to decide when to use it — so docstrings matter. |
| **LLM** | The model doing the reasoning. Here `qwen3-coder:30b`, running locally via Ollama. |
| **Ollama** | Runs open models on your machine and exposes an API that LangChain talks to. |
| **System prompt** | Standing instructions that define the agent's role and rules. |
| **`temperature`** | Randomness of the output. `0` = deterministic — best for tool use. |
| **`num_ctx`** | Context window size (in tokens). Too small → tool output gets **silently truncated**. |

## How the agent works

```
  You ask a question
        │
        ▼
  LLM reads each tool's docstring  ──► decides which tool fits
        │
        ▼
  Tool runs the REAL command (kubectl / docker)
        │
        ▼
  LLM reads the live output ──► writes the answer
```

The LLM never runs commands itself — it only *chooses* a tool. The Python function runs the actual command and hands the output back to the model.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) running locally with the model pulled
- `kubectl` configured against a cluster (for pod queries)
- `docker` running locally (for container queries)

## Usage — one-liners

```bash
ollama serve                    # start Ollama (if not already running)
ollama pull qwen3-coder:30b     # get the model (~18GB, one time)
ollama list                     # see installed models

python3 -m venv venv            # create a virtualenv
source venv/bin/activate
pip install -r requirements.txt # install LangChain + Ollama bindings

python agent.py                 # run the agent
```

Example prompts:

```
Ask your Kubernetes Agent a Question: > show me all pods
Ask your Kubernetes Agent a Question: > what containers are running on docker?
```

## Choosing a model

`qwen3-coder:30b` is the default: it's a **Mixture-of-Experts** model (~3B active params, so it stays fast) that's purpose-built for agentic tool-calling — it reliably picks the right tool and parses `kubectl`/`docker` output. Swapping models is a one-line change to the `model=` argument in `agent.py` (plus an `ollama pull`):

| Model | Good for | Notes |
|-------|----------|-------|
| `qwen3-coder:30b` | **Default** — best tool-calling | ~18GB, needs decent RAM |
| `qwen3:8b` | Balanced, smaller footprint | ~5GB, solid tool-caller |
| `llama3.2` | Low RAM / no big download | ~2GB, lighter answers |

## Why `num_ctx` matters

Ollama defaults to a small context window (a couple thousand tokens). On a real cluster, `kubectl get pods -A` can return far more than that — and anything past the window is **silently dropped before the model ever sees it**, so the agent answers on partial data. Setting `num_ctx=8192` (or higher for large clusters) in `agent.py` gives the model room to read the full tool output.

## Troubleshooting

| Symptom | Likely cause & fix |
|---------|--------------------|
| `Connection refused` / no response | Ollama isn't running → `ollama serve` |
| `model 'qwen3-coder:30b' not found` | Model not pulled → `ollama pull qwen3-coder:30b` |
| Agent says pods/containers are empty | `kubectl` or `docker` not configured/running — the tool returns nothing (or its error). Check `kubectl get pods -A` and `docker ps` manually |
| `ImportError: cannot import name 'create_agent'` | You're on old LangChain. This uses the **1.x** API (`from langchain.agents import create_agent`) → `pip install -U -r requirements.txt` |

## Project layout

```
.
├── agent.py            # LangChain agent + tools + entry point
├── requirements.txt    # Python dependencies (LangChain 1.x)
└── README.md
```
