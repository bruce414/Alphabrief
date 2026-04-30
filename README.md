# Alphabrief 📈

> **The AI-powered financial intelligence platform that turns hours of market content into actionable investor insight — personalised to your portfolio.**

---

## What is Alphabrief?

Generic AI summarisers can summarise a Bloomberg video. Alphabrief understands it.

While tools like NoteGPT or Eightify treat all words equally, Alphabrief is built exclusively for investors and traders. It doesn't just tell you *what happened* — it tells you *what it means for your money*.

Paste a YouTube link, article URL, or earnings call transcript. Alphabrief extracts the signal, enriches it with live market data, scores sentiment per ticker, and delivers a brief that's filtered through the lens of your own portfolio.

---

## Features

### 📊 Live Data Enrichment
When a video or article mentions a stock, Alphabrief doesn't just transcribe the mention — it pulls live market data inline. Every ticker that appears in your summary is automatically enriched with:

- Current price and intraday movement
- P/E ratio and 52-week high/low
- Recent analyst ratings and price targets
- A mini sparkline chart

So instead of reading *"Apple reported an earnings beat"*, you see that sentence alongside AAPL's current price, after-hours movement, and analyst consensus — without leaving the page.

---

### 🧠 Financial Entity Extraction
Alphabrief understands the language of markets. It automatically detects and tags every financially significant entity in your content:

- **Tickers** — $TSLA, $SPY, $BTC, $NVDA
- **People** — CEOs, Fed chairs, analysts, fund managers
- **Economic indicators** — CPI, interest rates, GDP, unemployment
- **Upcoming events** — earnings dates, FOMC meetings, product launches

Generic summarisers treat "Powell" the same as any other word. Alphabrief knows he moves markets.

---

### 📈 Per-Ticker Sentiment Scoring
Alphabrief doesn't just give you a vague "this was a bullish video" rating. It scores sentiment at the individual ticker level, so you get a clear, actionable read on each name mentioned:

```
NVDA  🟢 Bullish     — Strong earnings guidance, data centre demand cited
AAPL  🟡 Neutral     — Mixed iPhone demand signals, services growth positive
Fed   🔴 Bearish     — Higher-for-longer rhetoric, rate cut timeline pushed out
Oil   🟡 Neutral     — Supply constraints offset by demand concerns
```

---

### 💡 The "So What?" Layer
This is the feature no generic summariser offers. After every summary, Alphabrief adds an AI-generated investor insight section that translates news into portfolio implications:

> *"If the Fed pauses rate hikes as discussed in this video, this is historically bullish for growth and tech stocks. Watch: $NVDA earnings next Tuesday. $TLT may benefit if bond yields pull back."*

Turn passive consumption into active decision-making.

---

### 📰 Multi-Source Synthesis
Why summarise one source when the full picture requires many? Alphabrief lets you synthesise multiple sources about the same topic into a single unified brief:

- Bloomberg video ✅
- Reuters article ✅
- Earnings call transcript ✅
- Reddit / WallStreetBets sentiment ✅

One topic. One brief. Every angle covered. No other summariser does cross-source synthesis built specifically for finance.

---

### 🗂️ Portfolio-Aware Summaries
Connect your holdings and Alphabrief filters every summary through your personal portfolio lens. Instead of a generic brief, you get one written for *you*:

> *"This video is most relevant to you because you hold $TSLA — Elon Musk was mentioned at 14:32 in the context of production delays in Berlin. This may impact your position."*

Your portfolio. Your brief. Every morning.

---

### 🔔 Daily Morning Brief
Never miss a market-moving story. Alphabrief automatically monitors your chosen sources — YouTube channels, news outlets, podcast feeds — and delivers a curated morning brief to your inbox or app before the market opens.

- Scheduled delivery before market open
- Ranked by relevance to your portfolio
- Digest format: headlines, sentiment scores, and "So What?" insights

---

## How It Works

1. **Connect your sources** — paste a YouTube URL, article link, or earnings transcript, or subscribe to channels for automatic monitoring
2. **Add your portfolio** — enter your holdings so Alphabrief knows what matters to you
3. **Get your brief** — receive an enriched, personalised summary with live data, sentiment scores, and actionable insights
4. **Act with confidence** — use the "So What?" layer to understand implications before the market moves

---

## Who Is Alphabrief For?

- **Retail investors** who want institutional-quality research without the Bloomberg Terminal price tag
- **Active traders** who need to process large volumes of financial content quickly
- **Finance content creators** who need rapid research across multiple sources
- **Financial advisors** who want to stay on top of market narratives efficiently

---

## Tech Stack (Planned)

| Layer | Technology |
|---|---|
| AI Summarisation | Claude API (Anthropic) |
| Transcription | OpenAI Whisper |
| Live Market Data | Yahoo Finance API / Polygon.io |
| Sentiment Analysis | Custom NLP model fine-tuned on financial text |
| Entity Extraction | spaCy + custom financial NER |
| Backend | Node.js / Python FastAPI |
| Frontend | React |
| Database | PostgreSQL |

---

## Roadmap

**v1 — MVP**
- [ ] YouTube URL summarisation
- [ ] Ticker detection and live data enrichment
- [ ] Per-ticker sentiment scoring
- [ ] Basic "So What?" layer

**v2 — Personalisation**
- [ ] Portfolio-aware summaries
- [ ] Multi-source synthesis
- [ ] Daily morning brief delivery (email)

**v3 — Intelligence**
- [ ] Automatic source monitoring
- [ ] Historical sentiment tracking per ticker
- [ ] Push notifications for breaking market mentions
- [ ] Mobile app

---

## Getting Started

> 🚧 Alphabrief is currently in development. Star this repo to follow progress.

```bash
# Clone the repository
git clone https://github.com/yourusername/alphabrief.git
cd alphabrief

# Frontend (React + TypeScript)
cp frontend/.env.example frontend/.env
npm --prefix frontend install
npm --prefix frontend run dev

# Backend (Python + FastAPI) (in a second terminal)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

---

## Contributing

Alphabrief is an early-stage project. If you're a developer, designer, or finance nerd who wants to get involved, open an issue or reach out directly.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for investors who want the edge. Powered by AI. Personalised to your portfolio.*
