# Catalog ownership resolution (Phase 2C.2)

Chat answers **“Who owns X?”** from **Backstage catalog YAML** in the repo (seed entities, golden-path examples, and GitHub discovery output)—not from RAG document search.

## How it works

1. Routing sends messages matching `who owns`, `ownership of`, `owner of`, or `which team owns` to the **`catalog_ownership`** tool ([`registry.yaml`](../packages/platform-services/registry.yaml)).
2. Relay loads catalog documents from:
   - `catalog/entities/catalog.yaml`
   - targets referenced by `scaffolded-services.yaml` and `discovered-github-location.yaml`
   - `catalog/entities/discovered-github.yaml` when populated ([catalog discovery](catalog-discovery.md))
3. The tool matches **Component** / **System** / **API** entities by name or title and resolves **`spec.owner`** against **Group** / **User** entities in the same corpus.

## Try it

In Relay chat (local `:3000`):

- `Who owns demo-api?`
- `Who owns relay?`

Expected: owner team (e.g. **platform-team**), lifecycle, repo slug annotation when present, and catalog file source.

## Configure

No extra env vars. Keep catalog files valid and run **`make catalog-discover`** so discovered repos appear in the index.

## Related

- [catalog-discovery.md](catalog-discovery.md) — Phase 2C.1
- [roadmap.md](roadmap.md) — Phase 2C.3 on-call linkage
