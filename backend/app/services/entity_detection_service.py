"""Cheap, deterministic entity / topic detection for the pre-scan.

This is intentionally dumb: regex tickers gated by an allowlist, a small
company-name dictionary, and a small topic keyword dictionary. We will swap in
an LLM-backed detector later (see AI_PIPELINE §17.1). Do NOT call an LLM here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ~200 common US tickers. Curated to cover the names users are most likely to
# paste links about. Extend cautiously: every false positive becomes noise in
# the scan output.
COMMON_TICKERS: frozenset[str] = frozenset(
    {
        # Mega caps / FAANG-ish
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AVGO",
        "ORCL", "ADBE", "CRM", "NFLX", "AMD", "INTC", "QCOM", "CSCO", "TXN",
        "IBM", "MU", "AMAT", "LRCX", "KLAC", "ASML", "TSM", "PLTR", "SNOW",
        "PANW", "CRWD", "FTNT", "ZS", "DDOG", "NET", "MDB", "OKTA", "WDAY",
        "NOW", "SHOP", "SQ", "PYPL", "COIN", "ABNB", "UBER", "LYFT", "DASH",
        "ROKU", "SPOT", "PINS", "SNAP", "RBLX", "U", "DIS", "WBD", "PARA",
        "CMCSA", "T", "VZ", "TMUS",
        # Financials
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "V",
        "MA", "PYPL", "USB", "PNC", "TFC", "COF", "DFS", "BK", "STT", "ALLY",
        "BX", "KKR", "APO", "ARES",
        # Energy
        "XOM", "CVX", "COP", "EOG", "OXY", "SLB", "HAL", "BKR", "MPC", "PSX",
        "VLO", "FANG", "DVN", "PXD", "HES", "APA",
        # Healthcare
        "UNH", "JNJ", "PFE", "MRK", "LLY", "ABBV", "TMO", "DHR", "ABT", "BMY",
        "AMGN", "GILD", "MDT", "CVS", "ELV", "CI", "HUM", "ISRG", "VRTX",
        "REGN", "BIIB", "MRNA", "BNTX",
        # Consumer
        "WMT", "COST", "TGT", "HD", "LOW", "MCD", "SBUX", "NKE", "LULU", "PG",
        "KO", "PEP", "MDLZ", "MO", "PM", "KHC", "GIS", "K", "HSY", "CL",
        "EL", "ULTA", "TJX", "ROST", "DG", "DLTR", "BBY",
        # Industrials / transports
        "BA", "GE", "CAT", "DE", "HON", "MMM", "LMT", "RTX", "NOC", "GD",
        "UPS", "FDX", "CSX", "UNP", "NSC", "DAL", "UAL", "AAL", "LUV",
        # Materials / staples / utilities / REITs
        "LIN", "FCX", "NEM", "DOW", "DD", "PPG", "SHW", "ECL", "NEE", "DUK",
        "SO", "AEP", "EXC", "XEL", "AMT", "PLD", "CCI", "EQIX", "DLR", "O",
        "SPG", "WELL", "AVB",
        # ETFs / index proxies often seen in finance content
        "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "VEA", "VWO", "EEM", "EFA",
        "TLT", "IEF", "SHY", "GLD", "SLV", "USO", "UNG", "XLF", "XLK", "XLE",
        "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "XLRE", "XLC",
        # Crypto-adjacent equities frequently mentioned alongside markets
        "MSTR", "MARA", "RIOT", "HUT",
        # International ADRs that show up in US finance media
        "BABA", "JD", "PDD", "NIO", "BIDU", "TM", "SONY", "SHEL", "BP",
        "RIO", "BHP", "VALE",
    }
)


# {Common name → primary US ticker}. Lower-case keys for case-insensitive
# matching; values are the preferred ticker we surface in detected_entities.
COMPANY_NAME_TO_TICKER: dict[str, str] = {
    # Tech
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "broadcom": "AVGO",
    "oracle": "ORCL",
    "adobe": "ADBE",
    "salesforce": "CRM",
    "netflix": "NFLX",
    "amd": "AMD",
    "advanced micro devices": "AMD",
    "intel": "INTC",
    "qualcomm": "QCOM",
    "cisco": "CSCO",
    "texas instruments": "TXN",
    "ibm": "IBM",
    "micron": "MU",
    "applied materials": "AMAT",
    "lam research": "LRCX",
    "kla": "KLAC",
    "asml": "ASML",
    "tsmc": "TSM",
    "taiwan semiconductor": "TSM",
    "palantir": "PLTR",
    "snowflake": "SNOW",
    "palo alto networks": "PANW",
    "crowdstrike": "CRWD",
    "fortinet": "FTNT",
    "zscaler": "ZS",
    "datadog": "DDOG",
    "cloudflare": "NET",
    "mongodb": "MDB",
    "okta": "OKTA",
    "workday": "WDAY",
    "servicenow": "NOW",
    "shopify": "SHOP",
    "block": "SQ",
    "square": "SQ",
    "paypal": "PYPL",
    "coinbase": "COIN",
    "airbnb": "ABNB",
    "uber": "UBER",
    "lyft": "LYFT",
    "doordash": "DASH",
    "roku": "ROKU",
    "spotify": "SPOT",
    "pinterest": "PINS",
    "snap": "SNAP",
    "snapchat": "SNAP",
    "roblox": "RBLX",
    "disney": "DIS",
    "warner bros discovery": "WBD",
    "paramount": "PARA",
    "comcast": "CMCSA",
    "verizon": "VZ",
    "t-mobile": "TMUS",
    # Financials
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "wells fargo": "WFC",
    "citigroup": "C",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "blackrock": "BLK",
    "schwab": "SCHW",
    "american express": "AXP",
    "visa": "V",
    "mastercard": "MA",
    "blackstone": "BX",
    "kkr": "KKR",
    "apollo": "APO",
    # Energy
    "exxon": "XOM",
    "exxonmobil": "XOM",
    "chevron": "CVX",
    "conocophillips": "COP",
    "occidental": "OXY",
    "schlumberger": "SLB",
    # Healthcare
    "unitedhealth": "UNH",
    "johnson & johnson": "JNJ",
    "pfizer": "PFE",
    "merck": "MRK",
    "eli lilly": "LLY",
    "abbvie": "ABBV",
    "moderna": "MRNA",
    "biontech": "BNTX",
    # Consumer
    "walmart": "WMT",
    "costco": "COST",
    "target": "TGT",
    "home depot": "HD",
    "lowe's": "LOW",
    "mcdonald's": "MCD",
    "starbucks": "SBUX",
    "nike": "NKE",
    "lululemon": "LULU",
    "procter & gamble": "PG",
    "coca-cola": "KO",
    "coca cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    # Industrials
    "boeing": "BA",
    "general electric": "GE",
    "caterpillar": "CAT",
    "deere": "DE",
    "honeywell": "HON",
    "lockheed martin": "LMT",
    "raytheon": "RTX",
    "ups": "UPS",
    "fedex": "FDX",
    # International
    "alibaba": "BABA",
    "jd.com": "JD",
    "pinduoduo": "PDD",
    "nio": "NIO",
    "baidu": "BIDU",
    "toyota": "TM",
    "sony": "SONY",
}


# Short macro / market-theme keyword dictionary. Matched as case-insensitive
# substrings; multi-word phrases match as written.
TOPIC_KEYWORDS: tuple[str, ...] = (
    "AI chips",
    "artificial intelligence",
    "machine learning",
    "earnings",
    "guidance",
    "buyback",
    "dividend",
    "Fed",
    "Federal Reserve",
    "rate cut",
    "rate hike",
    "interest rates",
    "inflation",
    "CPI",
    "PPI",
    "PCE",
    "jobs report",
    "unemployment",
    "tariffs",
    "trade war",
    "China",
    "geopolitics",
    "oil",
    "crude",
    "OPEC",
    "natural gas",
    "gold",
    "copper",
    "lithium",
    "uranium",
    "semiconductors",
    "cloud",
    "data center",
    "cybersecurity",
    "EV",
    "electric vehicles",
    "autonomous driving",
    "biotech",
    "FDA",
    "M&A",
    "IPO",
    "SPAC",
    "crypto",
    "bitcoin",
    "ethereum",
    "stablecoin",
    "regulation",
    "antitrust",
    "supply chain",
    "recession",
    "soft landing",
    "yield curve",
    "treasuries",
    "credit spreads",
    "housing",
    "mortgage rates",
    "labor market",
    "consumer spending",
    "retail sales",
    "manufacturing",
    "ISM",
    "PMI",
    "GDP",
    "balance sheet",
    "QT",
    "QE",
)


_TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")
# Common English short caps that look like tickers but aren't in finance text.
# Filtering against COMMON_TICKERS already handles most, but we drop these
# explicitly because some belong to the allowlist (e.g. "T" is a single letter
# below the 2-char threshold, but "OK"/"USA"-style noise should never match).
_HARD_BLOCK_TOKENS: frozenset[str] = frozenset(
    {"USA", "USD", "EUR", "GBP", "CEO", "CFO", "COO", "CTO", "AI", "API"}
)


@dataclass(frozen=True)
class DetectedEntity:
    name: str
    type: str  # "COMPANY", "TICKER", "MACRO"
    ticker: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"name": self.name, "type": self.type, "ticker": self.ticker}


def detect_tickers(text: str) -> list[str]:
    """Return tickers (deduped, ordered by first appearance) gated by allowlist."""

    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for m in _TICKER_RE.finditer(text):
        token = m.group(0)
        if token in _HARD_BLOCK_TOKENS:
            continue
        if token not in COMMON_TICKERS:
            continue
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def detect_companies(text: str) -> list[tuple[str, str]]:
    """Return [(canonical_name, ticker)] pairs from the company-name dictionary."""

    if not text:
        return []
    lowered = text.lower()
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for name, ticker in COMPANY_NAME_TO_TICKER.items():
        # Word-boundary check on the lower-cased text to avoid sub-word hits.
        if not re.search(rf"(?<!\w){re.escape(name)}(?!\w)", lowered):
            continue
        canonical = _canonical_company_name(name)
        if canonical in seen:
            continue
        seen.add(canonical)
        out.append((canonical, ticker))
    return out


def detect_topics(text: str) -> list[str]:
    """Return topic strings whose keyword appears (case-insensitive) in text."""

    if not text:
        return []
    lowered = text.lower()
    out: list[str] = []
    seen: set[str] = set()
    for kw in TOPIC_KEYWORDS:
        if kw.lower() in lowered and kw not in seen:
            seen.add(kw)
            out.append(kw)
    return out


def detect_entities(text: str) -> list[DetectedEntity]:
    """Combine company + ticker detection into a single deduped entity list.

    Companies are emitted with their canonical name and primary ticker. Bare
    tickers found by the regex but not already paired with a company name are
    emitted as TICKER entries. Topics are returned separately by detect_topics.
    """

    companies = detect_companies(text)
    tickers_from_companies = {ticker for _, ticker in companies}

    entities: list[DetectedEntity] = [
        DetectedEntity(name=name, type="COMPANY", ticker=ticker)
        for name, ticker in companies
    ]
    for ticker in detect_tickers(text):
        if ticker in tickers_from_companies:
            continue
        entities.append(DetectedEntity(name=ticker, type="TICKER", ticker=ticker))
    return entities


def _canonical_company_name(lower_name: str) -> str:
    """Return a display-cased company name from the dictionary key."""

    return " ".join(part.capitalize() for part in lower_name.split())
