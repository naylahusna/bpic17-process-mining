"""Exercise 11.18 — Same Resource
Bagian: Anggota 3

Tujuan:
Mengidentifikasi case yang memiliki minimal 2 aktivitas 'W_Assess Potential Fraud'
berstatus 'complete' yang dikerjakan oleh RESOURCE YANG SAMA.

Aturan analisis:
1. Satu case dihitung tepat satu kali meskipun memiliki lebih dari satu resource yang memenuhi syarat.
2. Menggunakan filter lifecycle 'complete' yang identik dengan Exercise 11.15.
3. Resource kosong, NaN, None, string kosong "", atau string "nan"/"none"
   TIDAK BOLEH dianggap sebagai resource yang sama dan wajib dikeluarkan.
4. Menampilkan case ID, resource ID, dan jumlah kejadian complete.
5. Posisi event mengikuti prepare_log (sort stabil case, timestamp, urutan asli di XES)
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


def is_valid_resource(res: object) -> bool:
    """Memeriksa apakah nilai resource valid (bukan NaN, None, atau string kosong/null)."""
    if pd.isna(res) or res is None:
        return False
    s = str(res).strip()
    return s != "" and s.lower() not in ("nan", "none", "null")


@dataclass
class Exercise1118Result:
    exercise: str
    rule: str
    total_cases: int
    matched_case_ids: list[str]
    qualifying_resources: dict[str, list[dict]]
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


def analyze_same_resource(df: pd.DataFrame,
                          target_activity: str = TARGET_ACTIVITY,
                          target_lifecycle: str = TARGET_LIFECYCLE,
                          min_count: int = 2) -> Exercise1118Result:
    """Menjalankan analisis Exercise 11.18 pada DataFrame log aktif."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input log harus berupa pandas DataFrame.")

    # Validasi keberadaan kolom wajib
    if LIFE not in df.columns:
        raise ValueError(
            f"Kolom '{LIFE}' tidak tersedia; analisis tidak dapat memastikan status complete."
        )
    if RES not in df.columns:
        raise ValueError(
            f"Kolom '{RES}' tidak tersedia; Exercise 11.18 memerlukan identitas resource."
        )
    required_cols = [CASE, ACT, TS]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Atribut wajib tidak tersedia di DataFrame: {missing}")

    rule_text = (
        f"Case dipilih jika memiliki minimal {min_count} aktivitas '{target_activity}' "
        f"berstatus '{target_lifecycle}' yang diselesaikan oleh RESOURCE YANG SAMA. "
        f"Resource kosong tidak dihitung. Level case: 1 case dihitung 1 kali."
    )

    if df.empty:
        empty_summary = pd.DataFrame(columns=[CASE, "resource_id", "complete_count"])
        empty_evidence = pd.DataFrame(columns=list(df.columns) + ([POS] if POS not in df.columns else []))
        return Exercise1118Result(
            exercise="11.18",
            rule=rule_text,
            total_cases=0,
            matched_case_ids=[],
            qualifying_resources={},
            summary_df=empty_summary,
            evidence_df=empty_evidence,
            evidence_by_case={},
        )

    # Pastikan urutan log konsisten dengan kolom _pos
    d = df if POS in df.columns else prepare_log(df)
    total_cases = int(d[CASE].nunique())

    # Normalisasi string target activity & lifecycle
    act_mask = d[ACT].astype(str).str.strip().str.lower() == target_activity.strip().lower()
    life_mask = d[LIFE].astype(str).str.strip().str.lower() == target_lifecycle.strip().lower()

    # Filter aktivitas target dan lifecycle complete
    complete_events = d[act_mask & life_mask].copy()

    if complete_events.empty:
        empty_summary = pd.DataFrame(columns=[CASE, "resource_id", "complete_count"])
        return Exercise1118Result(
            exercise="11.18",
            rule=rule_text,
            total_cases=total_cases,
            matched_case_ids=[],
            qualifying_resources={},
            summary_df=empty_summary,
            evidence_df=complete_events,
            evidence_by_case={},
        )

    # Filter resource yang valid (keluarkan resource kosong / NaN / None)
    valid_res_mask = complete_events[RES].apply(is_valid_resource)
    valid_events = complete_events[valid_res_mask].copy()

    if valid_events.empty:
        empty_summary = pd.DataFrame(columns=[CASE, "resource_id", "complete_count"])
        return Exercise1118Result(
            exercise="11.18",
            rule=rule_text,
            total_cases=total_cases,
            matched_case_ids=[],
            qualifying_resources={},
            summary_df=empty_summary,
            evidence_df=valid_events,
            evidence_by_case={},
        )

    # Group by [CASE, RES] untuk menghitung complete occurrence per resource dalam tiap case
    res_grouped = valid_events.groupby([CASE, RES], sort=False).size()
    qualifying_pairs = res_grouped[res_grouped >= min_count].reset_index(name="count")

    if qualifying_pairs.empty:
        empty_summary = pd.DataFrame(columns=[CASE, "resource_id", "complete_count"])
        return Exercise1118Result(
            exercise="11.18",
            rule=rule_text,
            total_cases=total_cases,
            matched_case_ids=[],
            qualifying_resources={},
            summary_df=empty_summary,
            evidence_df=pd.DataFrame(columns=valid_events.columns),
            evidence_by_case={},
        )

    # Filter matched cases (1 case dihitung 1 kali)
    matched_case_ids = [str(c) for c in qualifying_pairs[CASE].unique()]

    # Kumpulkan daftar resource yang lolos per case
    qualifying_resources: dict[str, list[dict]] = {}
    summary_rows = []
    qualifying_pairs_set = set(zip(qualifying_pairs[CASE], qualifying_pairs[RES]))

    for case_id, group in qualifying_pairs.groupby(CASE, sort=False):
        c_str = str(case_id)
        res_list = []
        res_str_items = []
        count_str_items = []
        for _, row in group.iterrows():
            r_val = str(row[RES])
            cnt = int(row["count"])
            res_list.append({"resource_id": r_val, "count": cnt})
            res_str_items.append(r_val)
            count_str_items.append(f"{r_val} ({cnt}x)")

        qualifying_resources[c_str] = res_list

        # Format 1 baris per case untuk tabel Case Explorer
        summary_rows.append({
            CASE: c_str,
            "resource_id": ", ".join(res_str_items),
            "complete_count": ", ".join(count_str_items) if len(count_str_items) > 1 else res_list[0]["count"],
        })

    summary_df = pd.DataFrame(summary_rows)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(CASE).reset_index(drop=True)

    # Filter event bukti: hanya event complete dari pasangan (case, resource) yang memenuhi syarat
    is_evidence = valid_events.apply(
        lambda r: (r[CASE], r[RES]) in qualifying_pairs_set, axis=1
    )
    evidence_df = valid_events[is_evidence].sort_values([CASE, POS]).reset_index(drop=True)

    # Susun evidence mapping untuk Case Explorer: {case_id: {pos: label}}
    evidence_by_case: dict[str, dict[int, str]] = {}
    for case_id, group in evidence_df.groupby(CASE, sort=False):
        c_str = str(case_id)
        evidence_by_case[c_str] = {}
        # Hitung ranking kejadian per resource dalam case ini
        res_counter: dict[str, int] = {}
        for _, row in group.iterrows():
            pos = int(row[POS])
            r_name = str(row[RES])
            res_counter[r_name] = res_counter.get(r_name, 0) + 1
            evidence_by_case[c_str][pos] = f"Complete #{res_counter[r_name]} by {r_name}"

    return Exercise1118Result(
        exercise="11.18",
        rule=rule_text,
        total_cases=total_cases,
        matched_case_ids=matched_case_ids,
        qualifying_resources=qualifying_resources,
        summary_df=summary_df,
        evidence_df=evidence_df,
        evidence_by_case=evidence_by_case,
    )
