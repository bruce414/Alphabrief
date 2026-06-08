from app.services.reply_tail_sections import parse_reply_tail_sections, split_follow_up_questions


def test_parse_reply_tail_sections_full() -> None:
    md = """Body.

---
### Key entities
- NVDA
- SPY

---
### Canvas insight cards
- {"elementType":"CLAIM","title":"T","contentMarkdown":"C body here."}

---
### Follow-up questions
- Next?
"""
    main, ent, canvas, fq = parse_reply_tail_sections(md)
    assert "Body" in main
    assert "NVDA" in ent
    assert len(canvas) == 1
    assert canvas[0]["elementType"] == "CLAIM"
    assert canvas[0]["contentMarkdown"] == "C body here."
    assert fq == ["Next?"]


def test_split_follow_up_questions_compat() -> None:
    md = """Hi.

---
### Follow-up questions
- Q1?
"""
    main, qs = split_follow_up_questions(md)
    assert "Hi" in main
    assert qs == ["Q1?"]


def test_parse_no_sections() -> None:
    md = "Just prose."
    main, e, c, f = parse_reply_tail_sections(md)
    assert main == "Just prose."
    assert e == [] and c == [] and f == []


def test_parse_preserves_prose_in_key_entities_section() -> None:
    """Non-bullet lines after ### Key entities must stay in main (not dropped)."""
    md = """Main body.

---
### Key entities

Intro paragraph before bullets.

- NVDA

More prose after bullet with **Key** takeaways.
"""
    main, ent, _c, fq = parse_reply_tail_sections(md)
    assert "Main body" in main
    assert "Intro paragraph" in main
    assert "NVDA" in ent
    assert "takeaways" in main
    assert fq == []


def test_parse_merges_unrecognized_segment_into_main() -> None:
    """A standalone --- used like a Markdown HR must not drop following prose."""
    md = """# Title

Intro.

---

## More detail

Body after rule.

---
### Key entities
- AAPL

---
### Follow-up questions
- Next?
"""
    main, ent, _c, fq = parse_reply_tail_sections(md)
    assert "Intro" in main
    assert "More detail" in main
    assert "Body after rule" in main
    assert "AAPL" in ent
    assert fq == ["Next?"]
