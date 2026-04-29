# Alphabrief v0.3 Observability

## Version

`v0.3 MVP`

## Purpose

This document defines basic logging and monitoring needs for Alphabrief v0.3.

## Why Observability Matters

Alphabrief relies on external services and AI generation.

Failures can happen in many places:

- Source extraction
- YouTube transcript retrieval
- Market data retrieval
- AI generation
- JSON validation
- Database persistence

Observability helps detect where the pipeline breaks.

## Events to Log

Log these events:

- User registered
- User created brief
- Source extraction started
- Source extraction succeeded
- Source extraction failed
- Entity detection started
- Entity detection succeeded
- Entity detection failed
- AI generation started
- AI generation succeeded
- AI generation failed
- AI output validation failed
- Usage limit reached
- Premium feature attempted by free user

## Metrics to Track

Track:

- Number of briefs generated per day
- Brief generation success rate
- Average generation time
- Source extraction failure rate
- AI generation failure rate
- Most common source type
- AI token usage estimate
- Free-to-premium upgrade clicks
- Usage limit hits

## Logging Fields

Recommended fields:

```text
timestamp
event_name
user_id
brief_id
source_id
source_type
status
duration_ms
error_code
```

## Sensitive Data Rules

Do not log:

- API keys
- Auth tokens
- Passwords
- Full raw user input in production
- Full AI prompt in production unless safely redacted
- Payment details

## Error Tracking

For v0.3, error tracking can be simple.

Options:

- Backend logs only
- Sentry
- Logtail
- Datadog later
- Cloud provider logs

## MVP Principle

Start with simple logs and clear error codes.

Do not build a giant observability cathedral before the first users arrive.
