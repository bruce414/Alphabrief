# Alphabrief v0.3 Premium Features

## Version

`v0.3 MVP`

## Purpose

This document defines the difference between free and premium behavior.

## Product Principle

Premium should not simply mean “more words.”

Premium should mean deeper, broader, and more useful investor context.

## Free Tier

Free users receive:

- Source summary
- Key takeaways
- Detected entities
- Basic company/entity explanation
- Source-specific risks
- Simple investor questions
- Limited brief history
- Daily generation limit

Suggested limits:

| Feature | Free |
|---|---:|
| Basic briefs per day | 3 |
| Pasted text length | 8,000 characters |
| Saved brief history | 20 briefs |
| Premium external context | No |

## Premium Tier

Premium users receive:

- Everything in free tier
- Industry context
- Competitor dynamics
- Macro factors
- Political/regulatory context
- Market sentiment where available
- Broader risk/opportunity map
- Second-order implications
- Higher usage limits
- Longer input support
- Larger brief history

Suggested limits:

| Feature | Premium |
|---|---:|
| Basic briefs per day | 50 |
| Deep briefs per day | 20 |
| Pasted text length | 30,000 characters |
| Saved brief history | High or unlimited |
| Premium external context | Yes |

## Locked Preview Cards

For free users, premium sections can appear as locked preview cards.

Examples:

```text
Industry context locked
Macro context locked
Regulatory context locked
Competitor context locked
```

This helps users understand what premium unlocks without making the free experience feel broken.

## Backend Enforcement

Premium logic must be enforced in the backend, not only the frontend.

The backend should check:

- User subscription tier
- Requested depth
- Usage limit
- Whether premium context should be retrieved
- Whether premium fields should be returned

## Frontend Display

The frontend should show:

- Free available sections
- Locked premium sections
- Upgrade prompt
- Current usage limit

## Future Premium Ideas

Not required for v0.3:

- Watchlist alerts
- Portfolio-specific brief analysis
- Earnings calendar monitoring
- Advanced valuation context
- Downloadable reports
- Email brief digest
- Saved research folders
