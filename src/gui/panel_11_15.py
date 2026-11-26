"""Panel Exercise 11.15 — Repeated Complete (F04).
Bagian: Anggota 3
Framework: PySide6 (kompatibel dengan AnalysisInfoBar dan CaseExplorerWidget Anggota 4).
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

# Penanganan path agar modul dapat diimpor dalam semua konfigurasi IDE dan terminal
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for p in [str(REPO_ROOT), str(REPO_ROOT / "anggota4"), str(REPO_ROOT / "src")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.analysis.columns import ACT, CASE, LIFE, POS, TS
from src.analysis.exercise_11_15 import (Exercise1115Result,
                                         analyze_repeated_complete,
                                         prepare_log)
from anggota4.analysis_info import AnalysisInfoBar
from anggota4.case_explorer import CaseExplorerWidget


class _Worker1115(QThread):
    done = Signal(object, object)
    failed = Signal(str)

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def run(self):
        try:
            d = self._df if POS in self._df.columns else prepare_log(self._df)
            res = analyze_repeated_complete(d)
            self.done.emit(d, res)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"{type(e).__name__}: {e}")


class Panel1115(QWidget):
    """Panel GUI untuk Exercise 11.15: Repeated Complete."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df: pd.DataFrame | None = None
        self._prepared: pd.DataFrame | None = None
        self.result: Exercise1115Result | None = None
        self._worker: _Worker1115 | None = None

        self.btn_run = QPushButton("Jalankan Analisis")
        self.btn_reset = QPushButton("Reset")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setMaximumWidth(160)
        self.status = QLabel("Impor log XES dulu.")

        self.answer = QLabel("")
        self.answer.setStyleSheet("font-size: 15px; font-weight: bold;")

        self.note = QLabel(
            "<b>Exercise 11.15 (Repeated Complete):</b> Memilih case yang memiliki aktivitas "
            "<i>W_Assess Potential Fraud</i> dengan status <b>complete</b> minimal 2 kali. "
            "Status schedule/start/abort diabaikan. Level case: 1 case dihitung 1 kali."
        )
        self.note.setWordWrap(True)

        self.info = AnalysisInfoBar()
        self.explorer = CaseExplorerWidget()

        bar = QHBoxLayout()
        bar.addWidget(self.btn_run)
        bar.addWidget(self.btn_reset)
        bar.addWidget(self.progress)
        bar.addWidget(self.status, 1)

        lay = QVBoxLayout(self)
        lay.addLayout(bar)
        lay.addWidget(self.note)
        lay.addWidget(self.answer)
        lay.addWidget(self.info)
        lay.addWidget(self.explorer, 1)

        self.btn_run.clicked.connect(self.run)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_run.setEnabled(False)

    # ---- API untuk Anggota 1 (MainWindow) & Ekspor ----
    def set_log(self, df: pd.DataFrame):
        """Menerima DataFrame log aktif dari MainWindow."""
        self._df = df
        self._prepared = None
        self.reset()
        self.btn_run.setEnabled(True)
        self.status.setText("Log siap. Klik Jalankan Analisis.")

    def export_payload(self) -> tuple[dict, pd.DataFrame] | None:
        """Mengembalikan (summary_dict, df_terpilih) untuk ekspor CSV (Anggota 1)."""
        if self.result is None:
            return None
        return self.result.export_payload()

    # ---- Logika Analisis & Threading ----
    def run(self):
        if self._df is None:
            return
        missing = [c for c in (CASE, ACT, TS, LIFE) if c not in self._df.columns]
        if missing:
            self.status.setText(f"Atribut wajib tidak ada: {missing}")
            return

        self.btn_run.setEnabled(False)
        self.progress.setRange(0, 0)  # Indikator animasi loading
        self.status.setText("Memproses analisis Exercise 11.15...")

        src = self._prepared if self._prepared is not None else self._df
        self._worker = _Worker1115(src)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_done(self, prepared_df: pd.DataFrame, result: Exercise1115Result):
        self._prepared = prepared_df
        self.result = result
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.btn_run.setEnabled(True)
        self.status.setText("Selesai.")

        pct = f" ({result.percentage:.2f}%)" if result.total_cases > 0 else ""
        self.answer.setText(f"Hasil: {result.matched_count:,} case memenuhi syarat{pct}")

        self.info.set_info(
            rule=result.rule,
            selected=result.matched_count,
            denominator=result.total_cases,
            percentage=result.percentage,
        )

        # Sambungkan ke Case Explorer
        self.explorer.set_log(self._prepared)
        table_df = result.summary_df.rename(columns={
            CASE: "Case ID",
            "complete_count": "Jumlah Complete",
        })
        self.explorer.set_cases(table_df, result.evidence_by_case)

    def _on_failed(self, msg: str):
        self.progress.setRange(0, 1)
        self.btn_run.setEnabled(True)
        self.status.setText(f"Gagal: {msg}")

    def reset(self):
        self.result = None
        self.answer.setText("")
        self.info.clear()
        self.explorer.set_cases(pd.DataFrame(), {})
        self.status.setText("Siap." if self._df is not None else "Impor log XES dulu.")
