# Alphabrief MVP Scope & Feature Specification

## 1. Product Overview

**Alphabrief** is an AI-powered investment research assistant that helps users turn financial content into structured, investor-style briefs.

Users can input a financial source such as an article, YouTube video, pasted text, PDF, or company ticker. Alphabrief summarises the content, extracts key information, enriches it with relevant public financial context, and produces a clear investment-focused analysis.

The goal of the MVP is not to build a general chatbot.

The goal is to build a focused investor workflow tool that helps users quickly understand:

- What happened
- Why it matters
- Which companies are affected
- What the bull and bear cases are
- What risks investors should pay attention to
- What questions the user should investigate next

---

## 2. Core MVP Value Proposition

> Alphabrief helps investors turn scattered financial content into structured, source-backed investment briefs.

Instead of asking a generic AI chatbot, users get a repeatable finance-specific workflow designed around investment research.

---

## 3. Target Users

### Primary Users

- Retail investors
- Finance students
- Early-career analysts
- Fintech/stock market enthusiasts
- People who consume financial news, YouTube videos, earnings reports, or company articles

### Secondary Users

- Content creators who want to summarise market content
- Investment club members
- Job seekers building financial research skills
- Small teams tracking companies or industries

---

## 4. MVP Goals

The MVP should prove that users find value in using Alphabrief to:

1. Summarise investment-related content quickly.
2. Extract important company, financial, and market signals.
3. Receive structured investor-style analysis.
4. Save time compared with manually reading/watching long sources.
5. Get more finance-specific output than a generic chatbot.

---

## 5. MVP Non-Goals

The MVP should **not** attempt to do everything.

For the first version, Alphabrief should not include:

- Real-time trading recommendations
- Buy/sell/hold signals
- Portfolio management
- Automated trading
- Personalised financial advice
- Complex valuation modelling
- Full Bloomberg-style terminal functionality
- Unlimited internet research across every possible website
- Scraping restricted or paywalled websites
- Social trading/community features
- Mobile app

---

# 6. MVP User Input Types

## 6.1 Article URL Input

Users can paste a public finance article URL.

Example inputs:

- CNBC article
- Reuters article
- company news page
- financial blog post
- market commentary article

### MVP Behaviour

Alphabrief should attempt to extract the article content if it is publicly accessible and allowed.

If extraction fails, Alphabrief should show a clear fallback message:

> “We couldn’t automatically access this article. Please paste the article text directly or upload the source as a file.”

---

## 6.2 YouTube URL Input

Users can paste a YouTube video URL.

Example inputs:

- earnings commentary video
- stock analysis video
- market news video
- investing education video

### MVP Behaviour

Alphabrief should attempt to access the available transcript where permitted.

If no transcript is available, Alphabrief should show:

> “No transcript was available for this video. Please paste the transcript manually if you have it.”

---

## 6.3 Pasted Text Input

Users can paste raw text directly.

Example inputs:

- article body
- YouTube transcript
- earnings call excerpt
- copied report section
- personal research notes

### MVP Behaviour

Alphabrief should analyse the pasted content directly.

This should be one of the safest and most reliable MVP input types.

---

## 6.4 PDF Upload

Users can upload a PDF document.

Example inputs:

- annual report
- quarterly report
- investor presentation
- earnings transcript
- broker report
- company announcement

### MVP Behaviour

Alphabrief should extract text from the PDF and generate an investor-style brief.

For MVP, PDF support can be limited by:

- file size
- page count
- number of documents per month
- text-based PDFs only

Scanned PDFs and image-heavy PDFs can be handled later.

---

## 6.5 Company / Ticker Input

Users can enter a company name or stock ticker.

Example inputs:

- AAPL
- MSFT
- NVDA
- V
- Tesla
- Fisher & Paykel Healthcare

### MVP Behaviour

Alphabrief should generate a basic company brief using public/company data sources.

This should include:

- business overview
- recent company context
- key financial metrics if available
- major risks
- bull case
- bear case
- investor questions

This feature should be more limited in the MVP than source summarisation.

---

# 7. Core MVP Features

## 7.1 Source Summarisation

### Description

Users submit a source, and Alphabrief generates a concise summary.

### Inputs

- article URL
- YouTube URL
- pasted text
- uploaded PDF

### Output

The summary should include:

- short overview
- 5 key takeaways
- companies mentioned
- key numbers mentioned
- important quotes or claims
- market/investment relevance

### Example Output Sections

```md
## Summary

## Key Takeaways

## Companies Mentioned

## Important Numbers

## Investment Relevance

## Risks or Concerns

## Questions to Investigate Next
```

## Usage limits

The system should support usage limits to control AI cost.

Suggested v0.3 assumptions:

| Feature | Free | Pro |
|---|---:|---:|
| Briefs per day | 3 | Unlimited |
| Pasted text length | 8,000 characters | 30,000 characters |
| Saved brief history | 20 briefs | High or unlimited |
| Premium context | No | Yes |