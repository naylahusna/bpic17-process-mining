from dataclasses import dataclass

import pandas as pd

from anggota4.columns import CASE, ACT, TS
from anggota4.ordering_11_22 import prepare_log
from exercise_11_7.analysis import cycle_time_days


@dataclass(frozen=True)
class OverviewResult:
    total_cases: int
    total_events: int
    activity_frequency: pd.DataFrame
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    average_cycle_time_days: float
    case_durations: pd.DataFrame


def build_overview(log: pd.DataFrame) -> OverviewResult:
    """
    Membuat statistik overview dari log aktif.

    Menggunakan prepare_log() milik Anggota 4
    dan cycle_time_days() milik Anggota 2.
    """

    if not isinstance(log, pd.DataFrame):
        raise TypeError("Log aktif harus berupa Pandas DataFrame.")

    if log.empty:
        raise ValueError("Event log kosong.")

    required = [CASE, ACT, TS]

    missing = [
        column for column in required
        if column not in log.columns
    ]

    if missing:
        raise ValueError(
            "Kolom wajib tidak ditemukan: "
            + ", ".join(missing)
        )

    # 1. Persiapkan urutan event menggunakan fungsi bersama
    df = prepare_log(log)

    # 2. Hitung total case dan event
    total_cases = int(df[CASE].nunique())
    total_events = len(df)

    # 3. Hitung frekuensi aktivitas
    activity_frequency = (
        df.groupby(ACT, sort=False, observed=True)
        .agg(
            event_count=(ACT, "size"),
            case_count=(CASE, "nunique")
        )
        .reset_index()
        .rename(columns={ACT: "activity"})
        .sort_values(
            ["event_count", "activity"],
            ascending=[False, True],
            kind="mergesort"
        )
        .reset_index(drop=True)
    )

    # 4. Tentukan rentang waktu keseluruhan
    start_time = df[TS].min()
    end_time = df[TS].max()

    # 5. Hitung durasi setiap case
    # Data sudah diurutkan berdasarkan timestamp
    case_bounds = (
        df.groupby(CASE, sort=False, observed=True)[TS]
        .agg(
            first_event="first",
            last_event="last"
        )
        .reset_index()
    )

    case_bounds["duration_days"] = [
        cycle_time_days(start, end)
        for start, end in zip(
            case_bounds["first_event"],
            case_bounds["last_event"]
        )
    ]

    # 6. Susun tabel durasi case
    case_durations = (
        case_bounds
        .rename(columns={CASE: "case_id"})
        .sort_values(
            "duration_days",
            ascending=False,
            kind="mergesort"
        )
        .reset_index(drop=True)
    )

    # 7. Hitung rata-rata cycle time
    average_cycle_time_days = (
        float(case_durations["duration_days"].mean())
        if not case_durations.empty
        else 0.0
    )

    return OverviewResult(
        total_cases=total_cases,
        total_events=total_events,
        activity_frequency=activity_frequency,
        start_time=start_time,
        end_time=end_time,
        average_cycle_time_days=average_cycle_time_days,
        case_durations=case_durations
    )
