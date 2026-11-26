"""Exercise 11.22: adakah O_Cancelled yang kemudian diikuti O_Accepted?

Aturan (level case/trace):
  case lolos jika ada i < j dengan event[i] = O_Cancelled dan event[j] = O_Accepted.
  Event TIDAK harus bertetangga. Beda dengan 11.7 E (event terakhir = O_Cancelled).

Urutan event: sort stabil by (case, timestamp, urutan baris asli di XES).
Jadi kalau timestamp sama, urutan di file XES yang dipakai.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .columns import ACT, CASE, ORIG, POS, TS

FIRST_ACT = "O_Cancelled"
SECOND_ACT = "O_Accepted"


def prepare_log(df: pd.DataFrame) -> pd.DataFrame:
    """Urutkan event per case dan beri kolom _pos. Tidak menghapus event apa pun."""
    d = df.copy()
    d[ORIG] = range(len(d))
    d[TS] = pd.to_datetime(d[TS], utc=True)
    d = d.sort_values([CASE, TS, ORIG], kind="mergesort").reset_index(drop=True)
    d[POS] = d.groupby(CASE, sort=False).cumcount()
    return d


@dataclass
class OrderingResult:
    first_activity: str
    second_activity: str
    total_cases: int
    matched_case_ids: list[str]
    evidence: pd.DataFrame = field(repr=False)

    @property
    def matched_count(self) -> int:
        return len(self.matched_case_ids)

    @property
    def percentage(self) -> float:
        return self.matched_count / self.total_cases * 100 if self.total_cases else 0.0

    @property
    def exists(self) -> bool:
        return self.matched_count > 0

    @property
    def rule_text(self) -> str:
        return (f"Case dipilih jika ada {self.first_activity} pada posisi i dan "
                f"{self.second_activity} pada posisi j, dengan i < j "
                f"(tidak harus bertetangga). Level case: 1 case dihitung 1 kali.")

    def summary_dict(self) -> dict:
        """Untuk ekspor CSV (Anggota 1)."""
        return {
            "exercise": "11.22",
            "rule": self.rule_text,
            "answer_exists": "Ya" if self.exists else "Tidak",
            "matched_cases": self.matched_count,
            "denominator_total_cases": self.total_cases,
            "percentage": round(self.percentage, 4),
        }


def analyze_cancel_then_accept(df: pd.DataFrame,
                               first: str = FIRST_ACT,
                               second: str = SECOND_ACT) -> OrderingResult:
    d = df if POS in df.columns else prepare_log(df)
    total = d[CASE].nunique()

    a = (d.loc[d[ACT] == first, [CASE, POS, TS]]
         .rename(columns={POS: "first_pos", TS: "first_ts"})
         .sort_values("first_pos")
         .drop_duplicates(CASE))                      # O_Cancelled paling awal per case
    b = (d.loc[d[ACT] == second, [CASE, POS, TS]]
         .rename(columns={POS: "second_pos", TS: "second_ts"}))

    pairs = a.merge(b, on=CASE)
    pairs = pairs[pairs["second_pos"] > pairs["first_pos"]]
    ev = (pairs.sort_values("second_pos")
          .drop_duplicates(CASE)                      # O_Accepted pertama setelah cancel
          .sort_values(CASE)
          .reset_index(drop=True))
    ev["events_between"] = ev["second_pos"] - ev["first_pos"] - 1

    return OrderingResult(first, second, int(total), ev[CASE].astype(str).tolist(), ev)
