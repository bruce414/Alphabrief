# Alphabrief v0.3 Product Requirements

## Version

`v0.3 MVP`

## Product Summary

Alphabrief is an AI-powered summarisation and investment research assistant.

Users submit financial content, and Alphabrief generates a structured investor-friendly brief that highlights key takeaways, detected financial entities, risks, opportunities, and investor questions.

## Target Users

Primary users:

- Retail investors
- Finance students
- Early-career finance/tech professionals
- People who follow markets but do not want to read every long article or video transcript manually

## Core Problem

Financial content is noisy, long, repetitive, and often scattered across articles, videos, commentary, and market updates.

Users want the useful parts quickly:

- What happened?
- Which companies or sectors are affected?
- Why does it matter?
- What are the risks?
- What should I watch next?

## Product Positioning

Alphabrief should not feel like a generic chatbot.

It should feel like a focused investment briefing engine.

The difference is structure, repeatability, entity detection, premium context, and saved brief history.

## Core User Stories

### Source submission

As a user, I want to submit a finance article, YouTube video, or pasted text so that I can generate a brief.

### Brief result

As a user, I want the brief to be structured clearly so that I can understand the source quickly.

### Entity detection

As a user, I want Alphabrief to identify companies, tickers, sectors, and macro factors so that I can see what the source is really about.

### Premium enrichment

As a premium user, I want Alphabrief to add broader market, industry, macro, and regulatory context so that the brief is more useful than a normal summary.

### Brief history

As a user, I want to view my previous briefs so that I can revisit research later.

### Usage limit

As the product owner, I want free users to have limits so that AI costs stay controlled.

## v0.3 Pages

| Page | Purpose |
|---|---|
| Landing page | Explain Alphabrief and its value |
| Sign up / sign in | User authentication |
| Dashboard | Main user area and recent briefs |
| New Brief page | Submit URL or pasted text |
| Brief Detail page | Show generated brief |
| Brief History page | List previous briefs |
| Pricing page | Explain free vs premium |

## Brief Output Requirements

A generated brief should include:

- Title
- Source summary
- Key takeaways
- Detected entities
- Entity-specific insights
- Risks
- Opportunities
- Investor questions
- Disclaimer

## Free Tier Requirements

Free users should receive:

- Source summary
- Key takeaways
- Basic detected entity list
- Basic company/entity context
- Source-specific risks
- Simple investor questions

Free users should not receive full premium context.

Premium-only sections may be hidden, omitted, or shown as locked preview cards.

## Premium Tier Requirements

Premium users should receive:

- Everything in free tier
- Industry trends
- Competitor dynamics
- Macro factors
- Political/regulatory factors
- Broader risk/opportunity map
- Second-order implications

## UX Requirements

The product should feel:

- Fast
- Clear
- Trustworthy
- Investor-focused
- Not overloaded

Each brief should be skimmable.

Recommended sections:

```text
1. Quick Summary
2. Key Takeaways
3. Entities Mentioned
4. Why It Matters
5. Risks
6. Opportunities
7. Questions Investors Should Ask
8. Premium Context, if available
```

## Error Requirements

The app should handle:

- Invalid URL
- Unsupported source type
- Article extraction failure
- YouTube transcript unavailable
- AI generation failure
- Usage limit reached
- User not logged in
- Brief not found

Error messages should be user-friendly.

## Compliance and Disclaimer

Every brief should include a disclaimer:

```text
This brief is for informational purposes only and is not financial advice.
```

## v0.3 Success Metrics

Track:

- Number of briefs generated
- Brief generation success rate
- Average generation time
- Most common source type
- Free vs premium feature clicks
- Usage limit hits
- Returning users
