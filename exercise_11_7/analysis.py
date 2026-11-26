from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import fmean
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame

CASE_ID = "case:concept:name"
ACTIVITY = "concept:name"
TIMESTAMP = "time:timestamp"


class Trace(Protocol):
    @property
    def attributes(self) -> Mapping[str, object]: ...

    def __iter__(self) -> Iterator[Mapping[str, object]]: ...


@dataclass(frozen=True)
class CaseDuration:
    case_id: str
    days: float


@dataclass(frozen=True)
class Answer:
    code: str
    title: str
    rule: str
    cases: tuple[CaseDuration, ...]

    @property
    def count(self) -> int:
        return len(self.cases)

    @property
    def mean_days(self) -> float | None:
        return fmean(case.days for case in self.cases) if self.cases else None


def _utc(timestamp: object) -> datetime:
    if not isinstance(timestamp, datetime) or timestamp != timestamp:
        raise ValueError("Timestamp event hilang atau bukan datetime.")
    if timestamp.utcoffset() is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def cycle_time_days(start: datetime, end: datetime) -> float:
    """Hitung durasi dalam hari dari dua timestamp batas trace."""
    return (_utc(end) - _utc(start)).total_seconds() / 86_400


def analyze(log: Iterable[Trace]) -> tuple[Answer, ...]:
    """Hitung A–E dari PM4Py EventLog. Trace dan event sumber tetap utuh."""
    return _analyze_traces((trace.attributes.get(ACTIVITY), (
        (event.get(ACTIVITY), event.get(TIMESTAMP)) for event in trace
    )) for trace in log)


def _analyze_traces(traces, *, prepared=False) -> tuple[Answer, ...]:
    all_cases = []
    accepted = []
    refused = []
    cancelled = []
    seen_ids = set()

    for case_id, events in traces:
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("Trace tidak memiliki case ID concept:name yang valid.")
        if case_id in seen_ids:
            raise ValueError(f"Case ID ganda: {case_id}.")
        seen_ids.add(case_id)

        first = last = None
        last_activity = None
        activities = set()
        for activity, timestamp in events:
            if not isinstance(activity, str) or not activity.strip():
                raise ValueError(f"Case {case_id}: nama aktivitas hilang.")
            try:
                stamp = _utc(timestamp)
            except ValueError as exc:
                raise ValueError(f"Case {case_id}: {exc}") from exc
            if first is None or stamp < first:
                first = stamp
            # Jika timestamp sama, event yang muncul belakangan di XES menjadi event akhir.
            if prepared or last is None or stamp >= last:
                last_activity = activity
            if last is None or stamp > last:
                last = stamp
            activities.add(activity)

        if first is None or last is None:
            raise ValueError(f"Case {case_id} tidak memiliki event.")
        case = CaseDuration(case_id, cycle_time_days(first, last))
        all_cases.append(case)
        if "O_Accepted" in activities:
            accepted.append(case)
        if "O_Refused" in activities:
            refused.append(case)
        if last_activity == "O_Cancelled":
            cancelled.append(case)

    every_case = tuple(all_cases)
    return (
        Answer("A", "Jumlah seluruh case", "Hitung setiap case ID satu kali dari seluruh log.", every_case),
        Answer("B", "Rata-rata cycle time seluruh case", "Rata-rata selisih timestamp awal dan akhir setiap trace, dalam hari.", every_case),
        Answer("C", "Successful cases", "Pilih case yang memuat minimal satu O_Accepted.", tuple(accepted)),
        Answer("D", "Unsuccessful cases", "Pilih case yang memuat minimal satu O_Refused.", tuple(refused)),
        Answer("E", "Canceled cases", "Pilih case yang event terakhirnya O_Cancelled.", tuple(cancelled)),
    )


def analyze_dataframe(
    log: "DataFrame", prepare_log: "Callable[[DataFrame], DataFrame]",
) -> tuple[Answer, ...]:
    """Hitung A–E dengan urutan trace hasil prepare_log milik tim."""
    from pandas import DataFrame

    if not isinstance(log, DataFrame):
        raise ValueError("Log aktif harus berupa pandas DataFrame.")
    missing = [column for column in (CASE_ID, ACTIVITY, TIMESTAMP) if column not in log.columns]
    if missing:
        raise ValueError("Kolom log hilang: " + ", ".join(missing))

    ordered = prepare_log(log)
    if not isinstance(ordered, DataFrame):
        raise ValueError("prepare_log harus mengembalikan DataFrame event.")
    missing = [column for column in (CASE_ID, ACTIVITY, TIMESTAMP) if column not in ordered.columns]
    if missing:
        raise ValueError("Kolom hilang setelah prepare_log: " + ", ".join(missing))

    groups = ordered.groupby(CASE_ID, sort=False, dropna=False, observed=True)
    traces = (
        (case_id, events[[ACTIVITY, TIMESTAMP]].itertuples(index=False, name=None))
        for case_id, events in groups
    )
    return _analyze_traces(traces, prepared=True)
