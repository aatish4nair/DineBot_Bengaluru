# Phase 4 - LLM Orchestration (Groq)

This phase provides the prompt construction and Groq integration points for the LLM
orchestrator. It intentionally does not execute real Groq requests until an API key
is configured.

## Integration points
- `GroqClient.generate()` is the placeholder for the Groq API call.
- `GroqConfig.api_key_env` expects `GROQ_API_KEY` in the environment.
- `LLMOrchestrator.generate_recommendation()` builds the prompt and delegates to
  `GroqClient`.

## Tests
Tests are deferred until the Groq API key is connected.
