---
name: ollama-web-search
description: Call Ollama's cloud web_search/web_fetch API, and handle the API key without it ever touching chat or session transcripts.
---

# Ollama web search, called securely

## When to use

- User wants live web results (not just a plain `web_fetch` of one known
  URL) and mentions Ollama, or already has an Ollama account/CLI installed.
- Any time a task needs a *secret* (API key, token) passed into a shell
  command but must not appear in the visible conversation or in any file
  I create.

## The two Ollama auth mechanisms — don't confuse them

- `ollama signin` / the `id_ed25519` keypair in `~/.ollama/` — SSH-style
  identity used for the model **registry** (`push`/`pull`/`publish`). Being
  "signed in" this way grants nothing for the REST API below.
- **Web Search / Web Fetch REST API** (`https://ollama.com/api/web_search`,
  `.../api/web_fetch`) — needs a separate bearer token minted at
  https://ollama.com/settings/keys, sent as `Authorization: Bearer <key>`.
  `~/.ollama/config.json` does not store this; there is no local daemon
  proxy for it either (`127.0.0.1:11434/api/web_search` 404s — the local
  Ollama server only serves inference endpoints).

## Secure key handling protocol

Never ask the user to paste a secret into the chat, and never write a
command whose literal text contains the key. pi's bash tool logs record
command text, so the key must never appear in the command string itself.

1. Ask the user to create the key file **in their own terminal**, outside
   the conversation:
   ```bash
   printf '%s' 'THE_KEY' > ~/.ollama_web_search_key
   chmod 600 ~/.ollama_web_search_key
   ```
2. Once they confirm it exists, verify presence/permissions only —
   never `cat` the file to check it:
   ```bash
   test -f ~/.ollama_web_search_key && stat -f "%A %N" ~/.ollama_web_search_key
   ```
3. Use command substitution inline so the key only lives transiently in
   the child process's environment, never in the command text or any
   tool-call log:
   ```bash
   curl -s https://ollama.com/api/web_search \
     -H "Authorization: Bearer $(cat ~/.ollama_web_search_key)" \
     -H "Content-Type: application/json" \
     -d '{"query":"...", "max_results": 8}'
   ```
   - No `-v`/verbose curl flags (they can echo request headers back).
   - Only the JSON response body — public search results — re-enters
     context; the key itself never does.
4. If the response is large, the bash tool may save full output to a temp
   file — parse it with `python3 -c "import json..."` or `jq`, and prefer
   `jq`/`python3` filters over dumping raw output. The temp file holds
   public search results, not the secret, but there's no reason to leave
   litter if you can clean it up.
5. Leave the key file for reuse, or let the user `rm` it — that's their
   call, not something to do unprompted.

## API shape reference

- `POST /api/web_search` — body `{"query": str, "max_results"?: int (≤10)}`
  → `{"results": [{"title", "url", "content"}]}`.
- `POST /api/web_fetch` — body `{"url": str}` → `{"title", "content", "links"}`.