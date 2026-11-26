import pandas as pd
import pytest

from .columns import ACT, CASE, TS
from .ordering_11_22 import analyze_cancel_then_accept


def make(cases, same_ts=False):
    rows = []
    for cid, acts in cases.items():
        for i, a in enumerate(acts):
            rows.append({CASE: cid, ACT: a, TS: pd.Timestamp("2016-01-01") + pd.Timedelta(
                minutes=0 if same_ts else i)})
    return pd.DataFrame(rows)


def ids(res):
    return set(res.matched_case_ids)


def test_non_adjacent_matches():
    r = analyze_cancel_then_accept(make({"c": ["A", "O_Cancelled", "X", "Y", "O_Accepted"]}))
    assert ids(r) == {"c"} and r.evidence.loc[0, "events_between"] == 2


def test_accepted_before_cancelled_no():
    assert not analyze_cancel_then_accept(make({"c": ["O_Accepted", "O_Cancelled"]})).exists


def test_cancelled_only_no():
    assert not analyze_cancel_then_accept(make({"c": ["O_Cancelled"]})).exists


def test_ends_with_cancelled_but_still_matches_if_accepted_between():
    assert ids(analyze_cancel_then_accept(
        make({"c": ["O_Cancelled", "O_Accepted", "O_Cancelled"]}))) == {"c"}


def test_accepted_cancelled_accepted_matches_with_later_accept():
    r = analyze_cancel_then_accept(make({"c": ["O_Accepted", "O_Cancelled", "O_Accepted"]}))
    assert ids(r) == {"c"} and r.evidence.loc[0, "second_pos"] == 2


def test_case_counted_once():
    r = analyze_cancel_then_accept(make({"c": ["O_Cancelled", "O_Accepted"] * 3}))
    assert r.matched_count == 1


def test_percentage_and_denominator():
    r = analyze_cancel_then_accept(make({
        "a": ["O_Cancelled", "O_Accepted"], "b": ["O_Accepted"],
        "c": ["X"], "d": ["O_Accepted", "O_Cancelled"]}))
    assert r.total_cases == 4 and r.matched_count == 1
    assert r.percentage == pytest.approx(25.0)


def test_equal_timestamp_uses_file_order():
    ok = analyze_cancel_then_accept(make({"c": ["O_Cancelled", "O_Accepted"]}, same_ts=True))
    bad = analyze_cancel_then_accept(make({"c": ["O_Accepted", "O_Cancelled"]}, same_ts=True))
    assert ok.exists and not bad.exists
