# LLM Theory and AI Lab Practice (in Russian)

A free Russian-language textbook on how large language models work and what surrounds them in a product: tokenization, attention, pretraining, SFT, RLHF, DPO, RLVR, LoRA, inference, KV cache, RAG, tool calls, prompt injection, evaluation. Comes with a reproducible TypeScript laboratory and an optional live lab on a local Ollama model.

- [Book PDF (Russian)](../../releases/latest) · [Interactive atlas](interactive/index.html) · [Changelog](CHANGELOG.md) · [Report an error](../../issues/new/choose)
- The book itself is Russian-only for now; this file explains the repository for international visitors.

## The laboratory

```bash
npm test          # deterministic tests, no network, no dependencies
npm run demo      # "я люблю чай" → token IDs → logits → softmax → loss → gradient
npm run attention # one causal attention head, computed by hand
npm run live      # optional: a real local LLM via Ollama (data never leaves the machine)
```

Book sources and the Python PDF pipeline live in [manual/](manual/README.md); fonts are committed, so the book builds from a clean clone.

## Series

1. LLM Theory and AI Lab Practice (this repo)
2. [Agent Engineering](https://github.com/ilyautov/agents-manual-lab)
3. [RAG: Search, Context, Answer](https://github.com/ilyautov/rag-manual-lab)

## Licenses

Book text: CC BY-NC 4.0. Laboratory code: MIT. Fonts: SIL OFL 1.1 / free licenses.
