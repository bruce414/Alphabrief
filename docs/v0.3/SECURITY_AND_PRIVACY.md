# Alphabrief v0.3 Security and Privacy

## Version

`v0.3 MVP`

## Purpose

This document defines minimum security and privacy expectations for Alphabrief v0.3.

## Security Principles

Alphabrief should:

- Protect user accounts
- Protect API keys
- Keep user briefs private
- Validate external URLs carefully
- Avoid exposing sensitive content in logs
- Treat AI output as untrusted

## API Keys

API keys must:

- Be stored in environment variables
- Never be committed to Git
- Never be sent to frontend
- Never appear in logs

Examples:

```text
AI_PROVIDER_API_KEY
MARKET_DATA_API_KEY
NEWS_API_KEY
```

## Authentication

The system should support authenticated user sessions or token-based auth.

Minimum requirements:

- Passwords must be hashed
- Users can only access their own briefs
- Premium features require premium tier
- Admin features require admin role

## Authorization Rules

```text
Users can only read their own briefs.
Users can only delete their own briefs.
Users can only view their own usage data.
Premium-only brief generation requires PREMIUM tier.
```

## URL Safety

Because Alphabrief may fetch external URLs, the backend should defend against server-side request forgery risks.

Reject or block:

```text
localhost
127.0.0.1
0.0.0.0
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

Also reject:

- Unsupported protocols
- File URLs
- Internal metadata endpoints
- Extremely large responses

## Logging

Safe to log:

- Brief generation started
- Brief generation completed
- Source extraction failed
- Error code
- User ID
- Source type
- Processing time

Avoid logging:

- API keys
- Auth tokens
- Passwords
- Full raw source text in production
- Private user content unless required for debugging and safely redacted

## AI Output Safety

AI output should be validated before display.

Check for:

- Required fields
- Valid JSON structure
- Missing disclaimer
- Premium-only leakage to free users
- Dangerous or unsupported financial advice wording

## Financial Disclaimer

Every generated brief should include:

```text
This brief is for informational purposes only and is not financial advice.
```

## Frontend Rendering

Sanitize rendered AI output.

Do not blindly render raw HTML from AI output.

## Production Checklist

Before public beta:

- HTTPS enabled
- API keys stored securely
- User ownership enforced
- Rate limiting enabled
- Usage limits enabled
- Logs reviewed for sensitive data
- Error responses do not leak internal stack traces
