from chronology import Chronology, conflicts, merge


def account(**kwargs):
    return Chronology(matter="Example", entries=[{
        "id": "meeting", "date": "2026-03-01", "event": "A meeting took place.",
        "sources": [{"doc": "Minutes", "pincite": "p 1"}], **kwargs,
    }])


def test_reused_id_never_discards_a_conflicting_date():
    a, b = account(), account(date="2026-03-02")
    combined = merge(a, b)
    assert len(combined.entries) == 2
    assert len(conflicts(combined)) == 1
    assert a.entries[0].event_key is None
    assert b.entries[0].id == "meeting"


def test_unicode_events_and_distinct_times_remain_separate():
    assert len(merge(account(event="双方在新加坡开会。"),
                     account(id="payment", event="双方在新加坡付款。")).entries) == 2
    assert len(merge(account(time="10:00"), account(time="16:00")).entries) == 2


def test_both_notes_and_distinct_source_urls_survive():
    a = account(notes="Short but material", sources=[{"doc": "Record", "url": "https://a.test"}])
    b = account(notes="A much longer but different account", sources=[
        {"doc": "Record", "url": "https://b.test"}])
    result = merge(a, b).entries[0]
    assert "Short but material" in result.notes and "different account" in result.notes
    assert len(result.sources) == 2
