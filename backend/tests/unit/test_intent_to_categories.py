"""Unit: intent → enrichment category mapping."""

from __future__ import annotations

import uuid

from app.core.enums import AnalysisIntent
from app.services.prompt_builder import filter_enrichments_by_intent


def test_insider_activity_keeps_insider_ownership_governance():
    docs = [
        {"category": "INSIDER", "title": "Form 4"},
        {"category": "OWNERSHIP", "title": "13D"},
        {"category": "GOVERNANCE", "title": "DEF 14A"},
        {"category": "PERIODIC", "title": "10-Q"},
    ]
    out = filter_enrichments_by_intent(docs, AnalysisIntent.INSIDER_ACTIVITY)
    cats = {d["category"] for d in out}
    assert cats == {"INSIDER", "OWNERSHIP", "GOVERNANCE"}


def test_company_analysis_drops_insider():
    docs = [
        {"category": "INSIDER", "title": "Form 4"},
        {"category": "PERIODIC", "title": "10-K"},
    ]
    out = filter_enrichments_by_intent(docs, AnalysisIntent.COMPANY_ANALYSIS)
    assert len(out) == 1
    assert out[0]["category"] == "PERIODIC"


def test_empty_enrichment_docs():
    assert filter_enrichments_by_intent([], AnalysisIntent.MARKET_IMPACT) == []


def test_missing_category_field_dropped():
    docs = [{"title": "no category"}]
    assert filter_enrichments_by_intent(docs, AnalysisIntent.MARKET_IMPACT) == []


def test_uuid_category_no_match():
    docs = [{"category": str(uuid.uuid4()), "title": "x"}]
    assert filter_enrichments_by_intent(docs, AnalysisIntent.QUICK_SUMMARY) == []
