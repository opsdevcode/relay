# relay-assistant tests

Pytest suite for the Python assistant. Run from repo root:

```bash
make test-local    # or make ci
```

**TDD:** add or extend a test here **before** implementing behavior in `src/`.
For HTTP-visible changes, also update `scripts/smoke-local.sh` in the same PR.

See [docs/tdd.md](../../../docs/tdd.md) and [docs/local-testing.md](../../../docs/local-testing.md).
