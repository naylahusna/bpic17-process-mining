from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pm4py

from anggota4.columns import CASE, ACT, TS, LIFE, RES


class XESImportError(Exception):
    """Error khusus ketika proses impor XES gagal."""


@dataclass
class ImportResult:
    dataframe: pd.DataFrame
    source_path: str
    attributes: tuple
    lifecycle_available: bool
    resource_available: bool

    @property
    def total_cases(self) -> int:
        return int(self.dataframe[CASE].nunique())

    @property
    def total_events(self) -> int:
        return len(self.dataframe)


def load_xes(file_path: str | Path) -> ImportResult:
    """
    Membaca file XES menggunakan PM4Py,
    mengubahnya menjadi Pandas DataFrame,
    dan memvalidasi atribut wajib.
    """

    path = Path(file_path)

    # 1. Validasi file
    if not path.is_file():
        raise XESImportError(
            f"File tidak ditemukan: {path}"
        )

    if not path.name.lower().endswith((".xes", ".xes.gz")):
        raise XESImportError(
            "Format file harus .xes atau .xes.gz"
        )

    # 2. Baca XES menggunakan PM4Py
    try:
        event_log = pm4py.read_xes(str(path))

        if isinstance(event_log, pd.DataFrame):
            df = event_log.copy()
        else:
            df = pm4py.convert_to_dataframe(event_log)

    except Exception as exc:
        raise XESImportError(
            f"Gagal membaca file XES: {exc}"
        ) from exc

    if not isinstance(df, pd.DataFrame):
        raise XESImportError(
            "Hasil konversi PM4Py bukan Pandas DataFrame."
        )

    if df.empty:
        raise XESImportError(
            "Event log kosong dan tidak memiliki event."
        )

    # 3. Catat atribut asli sebelum menambahkan kolom opsional
    attributes = tuple(str(column) for column in df.columns)

    # 4. Validasi atribut wajib
    required_columns = [CASE, ACT, TS]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise XESImportError(
            "Atribut wajib tidak ditemukan: "
            + ", ".join(missing)
        )

    # 5. Validasi Case ID dan Activity
    for column in (CASE, ACT):
        invalid = (
            df[column].isna()
            | df[column].astype("string").str.strip().eq("")
        )

        if invalid.any():
            raise XESImportError(
                f"Atribut {column} memiliki "
                f"{int(invalid.sum())} nilai kosong."
            )

    # 6. Validasi dan normalisasi timestamp
    timestamps = pd.to_datetime(
        df[TS],
        errors="coerce",
        utc=True
    )

    invalid_timestamps = timestamps.isna()

    if invalid_timestamps.any():
        raise XESImportError(
            f"Ditemukan {int(invalid_timestamps.sum())} "
            "timestamp kosong atau tidak valid."
        )

    df[TS] = timestamps

    # 7. Deteksi lifecycle dan resource
    lifecycle_available = (
        LIFE in df.columns and df[LIFE].notna().any()
    )

    resource_available = (
        RES in df.columns and df[RES].notna().any()
    )

    # 8. Pastikan kolom opsional tersedia
    if LIFE not in df.columns:
        df[LIFE] = pd.NA

    if RES not in df.columns:
        df[RES] = pd.NA

    # 9. Standarisasi urutan kolom
    standard_columns = [CASE, ACT, TS, LIFE, RES]

    other_columns = [
        column
        for column in df.columns
        if column not in standard_columns
    ]

    df = df[
        standard_columns + other_columns
    ].reset_index(drop=True)

    # PENTING:
    # Jangan melakukan sorting di importer.
    # Urutan baris asli diteruskan ke prepare_log().

    return ImportResult(
        dataframe=df,
        source_path=str(path.resolve()),
        attributes=attributes,
        lifecycle_available=bool(lifecycle_available),
        resource_available=bool(resource_available)
    )
