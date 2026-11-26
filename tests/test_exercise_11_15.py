"""Unit tests untuk Exercise 11.15 — Repeated Complete."""
import sys
from pathlib import Path
import pandas as pd
import pytest

# Pastikan module src/analysis dapat diimpor
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from src.analysis.columns import ACT, CASE, LIFE, RES, TS
from src.analysis.exercise_11_15 import analyze_repeated_complete


def make_log(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for c in [CASE, ACT, TS, LIFE, RES]:
        if c not in df.columns:
            df[c] = None
    df[TS] = pd.to_datetime(df[TS], utc=True)
    return df


def test_test1_two_schedule_one_complete():
    """TEST 1: Dua schedule, satu complete -> 11.15 TIDAK LOLOS."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "schedule", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 11:00:00", LIFE: "schedule", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 12:00:00", LIFE: "complete", RES: "User_1"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 0
    assert "C1" not in res.matched_case_ids
    assert not res.exists


def test_test2_two_complete_different_resource():
    """TEST 2: Dua complete oleh resource berbeda -> 11.15 LOLOS."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: "User_2"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 1
    assert "C1" in res.matched_case_ids
    assert res.occurrence_counts["C1"] == 2
    assert len(res.evidence_df) == 2


def test_test3_two_complete_same_resource():
    """TEST 3: Dua complete oleh resource sama -> 11.15 LOLOS."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: "User_1"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 1
    assert "C1" in res.matched_case_ids
    assert res.occurrence_counts["C1"] == 2


def test_test4_two_complete_empty_resource():
    """TEST 4: Dua complete dengan resource kosong -> 11.15 LOLOS (11.15 tidak mensyaratkan resource)."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: None},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: ""},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 1
    assert "C1" in res.matched_case_ids
    assert res.occurrence_counts["C1"] == 2


def test_three_complete_resource_a_one_resource_b():
    """Satu case dengan 3 complete oleh resource A dan 1 complete oleh resource B."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_A"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: "User_A"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 12:00:00", LIFE: "complete", RES: "User_A"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 13:00:00", LIFE: "complete", RES: "User_B"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 1
    assert res.occurrence_counts["C1"] == 4
    assert len(res.evidence_df) == 4


def test_two_resources_each_qualifying():
    """Satu case dengan 2 resource masing-masing 2x complete -> case hanya dihitung 1x."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_A"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: "User_A"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 12:00:00", LIFE: "complete", RES: "User_B"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 13:00:00", LIFE: "complete", RES: "User_B"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 1
    assert res.matched_case_ids == ["C1"]
    assert res.occurrence_counts["C1"] == 4


def test_non_target_activities_ignored():
    """Aktivitas selain target tidak ikut dihitung."""
    df = make_log([
        {CASE: "C1", ACT: "W_Validate application", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "W_Validate application", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 12:00:00", LIFE: "complete", RES: "User_1"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 0


def test_lifecycle_capitalization_and_whitespace():
    """Variasi huruf besar/kecil dan spasi pada lifecycle."""
    df = make_log([
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: " Complete ", RES: "User_1"},
        {CASE: "C1", ACT: "w_assess potential fraud", TS: "2016-01-01 11:00:00", LIFE: "COMPLETE", RES: "User_2"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 1
    assert res.occurrence_counts["C1"] == 2


def test_case_without_target_activity():
    """Case tanpa aktivitas target."""
    df = make_log([
        {CASE: "C1", ACT: "A_Create Application", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_1"},
    ])
    res = analyze_repeated_complete(df)
    assert res.matched_count == 0
    assert len(res.summary_df) == 0


def test_empty_dataframe():
    """DataFrame kosong."""
    df = pd.DataFrame(columns=[CASE, ACT, TS, LIFE, RES])
    res = analyze_repeated_complete(df)
    assert res.total_cases == 0
    assert res.matched_count == 0
    assert res.matched_case_ids == []
    assert res.summary_df.empty


def test_missing_required_column_raises():
    """Kolom wajib tidak tersedia harus memunculkan ValueError."""
    df = pd.DataFrame({CASE: ["C1"], ACT: ["W_Assess Potential Fraud"], TS: ["2016-01-01"]})
    with pytest.raises(ValueError) as exc:
        analyze_repeated_complete(df)
    assert "lifecycle:transition" in str(exc.value)


def test_evidence_by_case_mapping():
    """Verifikasi format evidence mapping untuk Case Explorer."""
    df = make_log([
        {CASE: "C1", ACT: "A_Create Application", TS: "2016-01-01 09:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 10:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "O_Accepted", TS: "2016-01-01 11:00:00", LIFE: "complete", RES: "User_1"},
        {CASE: "C1", ACT: "W_Assess Potential Fraud", TS: "2016-01-01 12:00:00", LIFE: "complete", RES: "User_2"},
    ])
    res = analyze_repeated_complete(df)
    assert "C1" in res.evidence_by_case
    ev_map = res.evidence_by_case["C1"]
    assert len(ev_map) == 2
    # Event pertama ada di pos 1, event kedua di pos 3
    assert 1 in ev_map
    assert 3 in ev_map
    assert "Complete #1" in ev_map[1]
    assert "Complete #2" in ev_map[3]
