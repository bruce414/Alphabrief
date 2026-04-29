# Contributing to Alphabrief

## Version

`v0.3 MVP`

## Branch Strategy

Recommended branches:

```text
main
dev
feat/*
fix/*
chore/*
refactor/*
```

### main

Stable release branch.

Only production-ready code should be merged into `main`.

### dev

Main integration branch for active development.

Feature branches should usually merge into `dev`.

### feature branches

Examples:

```text
feat/brief-generation
feat/source-extraction
feat/entity-detection
feat/premium-context
```

## Commit Style

Recommended format:

```text
type: short description
```

Examples:

```text
feat: add pasted text brief generation
fix: handle source extraction failure
chore: add environment setup docs
refactor: isolate ai provider client
```

Common types:

```text
feat
fix
chore
docs
refactor
test
style
```

## Pull Request Checklist

Before opening a PR:

- Code builds locally
- Backend tests pass, if available
- Frontend builds successfully
- No API keys committed
- Relevant docs updated
- Error handling considered
- User ownership/security rules considered

## Coding Principles

For v0.3:

1. Keep the MVP focused.
2. Prefer clear code over clever code.
3. Keep AI logic isolated.
4. Validate AI output.
5. Enforce premium logic in backend.
6. Avoid leaking secrets.
7. Write docs when behavior becomes non-obvious.

## Documentation Rule

When adding or changing a major feature, update the relevant doc:

| Change | Update |
|---|---|
| New endpoint | `API_SPEC.md` |
| New table/entity | `DATA_MODEL.md` |
| New AI behavior | `AI_PIPELINE.md` |
| New premium rule | `PREMIUM_FEATURES.md` |
| New setup requirement | `ENVIRONMENT_SETUP.md` |
