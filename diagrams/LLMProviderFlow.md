# LLM Provider and Model Routing Flow

```text
+-------------------+
| Human Manager     |
| selects provider  |
| and model         |
+---------+---------+
          |
          v
+---------------------------+
| Mission Control Dashboard |
| dashboard/app.py          |
| - reads /api/providers    |
| - shows detected Ollama   |
| - shows API key status    |
+-------------+-------------+
              |
              v
+---------------------------+
| FastAPI Provider Endpoint |
| GET /api/providers        |
+-------------+-------------+
              |
              v
+----------------------------------------------------+
| Provider Factory                                   |
| llm_providers/factory.py                           |
|                                                    |
| - normalize provider aliases                       |
| - detect local Ollama models                       |
| - auto-select installed local model                |
| - check OpenAI/Anthropic key configuration         |
| - resolve selected model                           |
| - expose recommendations                           |
+------------------------+---------------------------+
                         |
             +-----------+------------+
             |                        |
             v                        v
+----------------------+    +-------------------------+
| Provider Capability  |    | LangChain Chat Provider |
| Catalog              |    | langchain_client.py     |
| llm_providers/catalog|    |                         |
| - Ollama             |    | - builds chat model     |
| - LM Studio          |    | - validates readiness   |
| - OpenAI             |    | - handles provider API  |
| - Claude/Anthropic   |    |                         |
| - Gemini             |    +------------+------------+
| - Groq               |                 |
| - OpenRouter         |                 v
| - Together AI        |    +-------------------------+
+----------------------+    | Active Agent Invocation |
                            | BaseAgent + LangChain   |
                            +------------+------------+
                                         |
              +--------------------------+--------------------------+
              |                          |                          |
              v                          v                          v
      +---------------+          +---------------+          +---------------+
      | Local Models  |          | Cloud Models  |          | Future Router |
      | Ollama        |          | OpenAI        |          | fallback      |
      | LM Studio     |          | Anthropic     |          | token/cost    |
      | localhost     |          | Gemini/Groq   |          | streaming     |
      +---------------+          | OpenRouter    |          +---------------+
                                 | Together AI   |
                                 +---------------+
```

## Local-First Decision Logic

```text
1. If Ollama is running and has installed models:
      choose preferred detected model
      examples: qwen2.5-coder, qwen3:4b, llama3.1

2. If Ollama is running but no models are installed:
      suggest: ollama pull qwen2.5-coder

3. If Ollama is not running:
      suggest: ollama serve

4. If cloud provider is selected:
      require matching environment variable
      OpenAI: OPENAI_API_KEY
      Anthropic: ANTHROPIC_API_KEY

5. If future router is enabled:
      route by task capability, availability, cost, latency, and fallback policy
```

## Provider Responsibilities

```text
+----------------------+----------------------------------------------+
| Layer                | Responsibility                               |
+----------------------+----------------------------------------------+
| Dashboard            | Let manager choose provider/model             |
| FastAPI              | Validate request and expose provider status   |
| Provider Factory     | Normalize, detect, recommend, resolve         |
| Capability Catalog   | Describe provider features and constraints    |
| LangChain Provider   | Build actual chat model instance              |
| Agent Base           | Invoke model and parse structured output      |
| Future Router        | Fallbacks, retries, token/cost/latency metrics|
+----------------------+----------------------------------------------+
```
