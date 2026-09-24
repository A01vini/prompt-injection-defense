# AI Jailbreak & Prompt Injection Defense System — starter scaffold

Milestone 1 (target + baseline attacks) and Milestone 3's first defense
layer (instruction/data segregator) are implemented and runnable right now
with zero setup, using a mock LLM backend. Milestones 2 (full evaluation
harness), 4 (mutating attack generator), and 5 (adaptive testing) build on
top of this.

## Run it

```bash
pip install -r requirements.txt

# Baseline: no defense
python3 evaluation/runner.py --defense none

# With the instruction/data segregator active
python3 evaluation/runner.py --defense segregator
```

Each run prints the Attack Success Rate and writes a per-attack CSV to
`results/`.

## Structure

```
target/         # the victim RAG chatbot
  chatbot.py    # RAGChatbot class -- retrieves docs, calls the LLM, applies defense
  llm_backend.py# swap between mock / ollama / openai via LLM_BACKEND env var
  documents/    # clean + poisoned .txt files the chatbot retrieves from
attacks/
  seeds.py      # SEED_ATTACKS list -- direct, roleplay, obfuscation, indirect
defense/
  segregator.py # pattern-based override detector (stand-in for the classifier)
evaluation/
  runner.py     # runs every seed attack, logs outcome + latency to CSV
results/        # CSV output per run
```

## Switching to a real model

Currently `LLM_BACKEND` defaults to `mock` -- a rule-based stand-in that
mimics a vulnerable model so you can test the pipeline logic before
spending GPU time. To use a real model:

```bash
# Option A: local model via Ollama
ollama pull llama3.1:8b
export LLM_BACKEND=ollama
python3 evaluation/runner.py --defense none

# Option B: OpenAI API (needs OPENAI_API_KEY set)
export LLM_BACKEND=openai
python3 evaluation/runner.py --defense none
```

**Known limitation of the mock backend:** it signals compromise by
returning a fixed `[COMPROMISED] ...` string rather than actually
leaking the system prompt or complying with the injected task the way a
real LLM would. This means some `success_keywords` checks (written
expecting the real system prompt text to leak) won't match against the
mock's output even when the mock *did* detect an override phrase — you'll
see this as attacks marked "blocked/failed" that arguably should count as
compromised. This is fine for testing your defense layer's *detection*
logic now, but re-run against a real model (Ollama/OpenAI) before trusting
the ASR numbers you report at your review — the mock is a development
aid, not your source of truth.

## Next steps (in priority order for your mid-sem)

1. Switch `LLM_BACKEND` to `ollama` and re-run both commands above to get
   real, reportable ASR numbers.
2. Expand `attacks/seeds.py` to 15+ attacks (pull more from JailbreakBench
   / AdvBench for direct/roleplay/obfuscation; write 2-3 more indirect
   ones using the same `<rule>` template style already in A05/A06).
3. Replace the keyword-based `check_success()` in `runner.py` with an
   LLM-judge call (a second, cheap model call scoring "complied /
   refused") — this fixes the mock-backend limitation above and is more
   robust for a real model too.
4. Add the DistilBERT classifier and perplexity filter as additional
   defense options in `defense/`, following the same
   `(text) -> (allowed, reason)` interface as `segregator.py` so
   `runner.py` doesn't need to change.
