"""Exercise 11.15 — Repeated Complete
Bagian: Anggota 3

Tujuan:
Mengidentifikasi case yang memiliki aktivitas 'W_Assess Potential Fraud'
dengan status 'complete' minimal 2 kali.

Aturan analisis:
1. Satu case dihitung tepat satu kali.
2. Hanya kejadian berstatus lifecycle 'complete' yang dihitung (mengabaikan
   schedule, start, suspend, resume, ate_abort, dsb).
3. Pencocokan nama aktivitas dan status lifecycle bersifat case-insensitive
   dan toleran terhadap whitespace di awal/akhir string.
4. Posisi event mengikuti urutan prepare_log (sort stabil case, timestamp, urutan asli di XES)
   agar kompatibel dengan Case Explorer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import pandas as pd

try:
    from .columns import ACT, CASE, LIFE, ORIG, POS, RES, TS
except ImportError:
    from columns import ACT, CASE, LIFE, ORIG, POS, RES, TS

TARGET_ACTIVITY = "W_Assess Potential Fraud"
TARGET_LIFECYCLE = "complete"


def prepare_log(df: pd.DataFrame) -> pd.DataFrame:
    """Urutkan event per case secara stabil dan beri kolom _pos (0-based).
    Sama dengan prepare_log milik Anggota 4 dan Anggota 2.
    """
    d = df.copy()
    if ORIG not in d.columns:
        d[ORIG] = range(len(d))
    d[TS] = pd.to_datetime(d[TS], utc=True)
    d = d.sort_values([CASE, TS, ORIG], kind="mergesort").reset_index(drop=True)
    d[POS] = d.groupby(CASE, sort=False).cumcount()
    return d


@dataclass
class Exercise1115Result:
    exercise: str
    rule: str
    total_cases: int
    matched_case_ids: list[str]
    occurrence_counts: dict[str, int]
    summary_df: pd.DataFrame
    evidence_df: pd.DataFrame = field(repr=False)
    evidence_by_case: dict[str, dict[int, str]] = field(repr=False)

    @property
    def matched_count(self) -> int:
        return len(self.matched_case_ids)

    @property
    def percentage(self) -> float:
        return (self.matched_count / self.total_cases * 100) if self.total_cases > 0 else 0.0

    @property
    def exists(self) -> bool:
        return self.matched_count > 0

    def summary_dict(self) -> dict:
        """Format ringkasan untuk sistem ekspor CSV Anggota 1."""
        return {
            "exercise": self.exercise,
            "rule": self.rule,
            "matched_cases": self.matched_count,
            "denominator_total_cases": self.total_cases,
            "percentage": round(self.percentage, 4),
        }

    def export_payload(self) -> tuple[dict, pd.DataFrame]:
        """Mengembalikan (summary_dict, summary_df) untuk CSV export."""
        return self.summary_dict(), self.summary_df.copy()


def analyze_repeated_complete(df: pd.DataFrame,
                              target_activity: str = TARGET_ACTIVITY,
                              target_lifecycle: str = TARGET_LIFECYCLE,
                              min_count: int = 2) -> Exercise1115Result:
    """Menjalankan analisis Exercise 11.15 pada DataFrame log aktif."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input log harus berupa pandas DataFrame.")

    # Validasi atribut wajib
    required_cols = [CASE, ACT, TS, LIFE]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Atribut wajib tidak tersedia di DataFrame: {missing}. "
            f"Kolom '{LIFE}' wajib ada untuk memvalidasi status complete."
        )

    rule_text = (
        f"Case dipilih jika aktivitas '{target_activity}' diselesaikan (status '{target_lifecycle}') "
        f"minimal {min_count} kali. Level case: 1 case dihitung 1 kali."
    )

    if df.empty:
        empty_summary = pd.DataFrame(columns=[CASE, "complete_count"])
        empty_evidence = pd.DataFrame(columns=list(df.columns) + ([POS] if POS not in df.columns else []))
        return Exercise1115Result(
            exercise="11.15",
            rule=rule_text,
            total_cases=0,
            matched_case_ids=[],
            occurrence_counts={},
            summary_df=empty_summary,
            evidence_df=empty_evidence,
            evidence_by_case={},
        )

    # Pastikan log terurut secara konsisten dan memiliki kolom _pos
    d = df if POS in df.columns else prepare_log(df)
    total_cases = int(d[CASE].nunique())

    # Normalisasi string: case-insensitive & strip whitespace
    act_mask = d[ACT].astype(str).str.strip().str.lower() == target_activity.strip().lower()
    life_mask = d[LIFE].astype(str).str.strip().str.lower() == target_lifecycle.strip().lower()

    # Filter event yang memenuhi target activity dan target lifecycle
    target_events = d[act_mask & life_mask].copy()

    if target_events.empty:
        empty_summary = pd.DataFrame(columns=[CASE, "complete_count"])
        return Exercise1115Result(
            exercise="11.15",
            rule=rule_text,
            total_cases=total_cases,
            matched_case_ids=[],
            occurrence_counts={},
            summary_df=empty_summary,
            evidence_df=target_events,
            evidence_by_case={},
        )

    # Hitung jumlah complete per case
    case_counts = target_events.groupby(CASE, sort=False).size()
    qualifying_cases = case_counts[case_counts >= min_count]
    matched_case_ids = [str(cid) for cid in qualifying_cases.index]

    # Filter evidence events hanya dari case yang lolos
    matched_set = set(qualifying_cases.index)
    evidence_df = target_events[target_events[CASE].isin(matched_set)].copy()

    # Urutkan evidence berdasarkan case dan posisi trace
    evidence_df = evidence_df.sort_values([CASE, POS]).reset_index(drop=True)

    # Susun evidence mapping untuk Case Explorer: {case_id: {pos: label}}
    evidence_by_case: dict[str, dict[int, str]] = {}
    for case_id, group in evidence_df.groupby(CASE, sort=False):
        c_str = str(case_id)
        evidence_by_case[c_str] = {}
        for rank, pos in enumerate(group[POS], start=1):
            evidence_by_case[c_str][int(pos)] = f"Complete #{rank}"

    # Buat summary_df untuk tabel (1 baris per case, kolom pertama Case ID)
    summary_records = []
    occurrence_counts: dict[str, int] = {}
    for cid in matched_case_ids:
        cnt = int(qualifying_cases[cid])
        occurrence_counts[cid] = cnt
        summary_records.append({
            CASE: cid,
            "complete_count": cnt,
        })

    summary_df = pd.DataFrame(summary_records)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(CASE).reset_index(drop=True)

    return Exercise1115Result(
        exercise="11.15",
        rule=rule_text,
        total_cases=total_cases,
        matched_case_ids=matched_case_ids,
        occurrence_counts=occurrence_counts,
        summary_df=summary_df,
        evidence_df=evidence_df,
        evidence_by_case=evidence_by_case,
    )
