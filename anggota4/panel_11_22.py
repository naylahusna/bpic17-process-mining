"""Panel Exercise 11.22 (F06)."""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from .analysis_info import AnalysisInfoBar
from .case_explorer import CaseExplorerWidget
from .columns import ACT, CASE, POS, TS
from .ordering_11_22 import OrderingResult, analyze_cancel_then_accept, prepare_log


class _Worker(QThread):
    done = Signal(object, object)
    failed = Signal(str)

    def __init__(self, df):
        super().__init__()
        self._df = df

    def run(self):
        try:
            d = self._df if POS in self._df.columns else prepare_log(self._df)
            self.done.emit(d, analyze_cancel_then_accept(d))
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"{type(e).__name__}: {e}")


class Panel1122(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df: pd.DataFrame | None = None
        self._prepared: pd.DataFrame | None = None
        self.result: OrderingResult | None = None
        self._worker: _Worker | None = None

        self.btn_run = QPushButton("Jalankan Analisis")
        self.btn_run.setObjectName("PrimaryButton")
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setObjectName("SecondaryButton")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setMaximumWidth(160)
        self.status = QLabel("Impor log XES dulu.")
        self.status.setObjectName("Muted")
        self.answer = QLabel("")
        self.answer.setObjectName("AnswerBanner")
        self.note = QLabel("Catatan: 11.22 = urutan O_Cancelled sebelum O_Accepted (tidak harus "
                           "bertetangga). Berbeda dengan 11.7 E (event TERAKHIR = O_Cancelled).")
        self.note.setObjectName("InfoText")
        self.note.setWordWrap(True)
        self.info = AnalysisInfoBar()
        self.explorer = CaseExplorerWidget()

        bar = QHBoxLayout()
        bar.setSpacing(10)
        bar.addWidget(self.btn_run)
        bar.addWidget(self.btn_reset)
        bar.addWidget(self.progress)
        bar.addWidget(self.status, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.addLayout(bar)
        lay.addWidget(self.note)
        lay.addWidget(self.answer)
        lay.addWidget(self.info)
        lay.addWidget(self.explorer, 1)

        self.btn_run.clicked.connect(self.run)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_run.setEnabled(False)

    # ---- API untuk Anggota 1 (MainWindow) ----
    def set_log(self, df: pd.DataFrame):
        self._df = df
        self._prepared = None
        self.reset()
        self.btn_run.setEnabled(True)
        self.status.setText("Log siap. Klik Jalankan Analisis.")

    def export_payload(self):
        """(summary_dict, DataFrame case terpilih) untuk CSV."""
        if self.result is None:
            return None
        ev = self.result.evidence.rename(columns={
            CASE: "case_id", "first_pos": "pos_O_Cancelled", "second_pos": "pos_O_Accepted",
            "first_ts": "ts_O_Cancelled", "second_ts": "ts_O_Accepted"})
        for c in ("pos_O_Cancelled", "pos_O_Accepted"):
            ev[c] = ev[c] + 1
        return self.result.summary_dict(), ev

    # ---- logic ----
    def run(self):
        if self._df is None:
            return
        missing = [c for c in (CASE, ACT, TS) if c not in self._df.columns]
        if missing:
            self.status.setText(f"Atribut wajib tidak ada: {missing}")
            return
        self.btn_run.setEnabled(False)
        self.progress.setRange(0, 0)
        self.status.setText("Memproses...")
        src = self._prepared if self._prepared is not None else self._df
        self._worker = _Worker(src)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def _on_fail(self, msg):
        self.progress.setRange(0, 1)
        self.btn_run.setEnabled(True)
        self.status.setText(f"Gagal: {msg}")

    def _on_done(self, prepared, res: OrderingResult):
        self._prepared = prepared
        self.result = res
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.btn_run.setEnabled(True)
        self.status.setText("Selesai.")

        verdict = "ADA" if res.exists else "TIDAK ADA"
        self.answer.setText(
            f"<b>Jawaban:</b> {verdict} case dengan O_Cancelled yang kemudian diikuti O_Accepted. "
            f"<b>{res.matched_count:,}</b> dari {res.total_cases:,} case ({res.percentage:.2f}%).")
        self.info.set_info(res.rule_text, res.matched_count, res.total_cases, res.percentage)

        ev = res.evidence
        table = pd.DataFrame({
            "Case ID": ev[CASE].astype(str),
            "Pos O_Cancelled": ev["first_pos"] + 1,
            "Pos O_Accepted": ev["second_pos"] + 1,
            "Event penyela": ev["events_between"],
            "Waktu O_Cancelled": ev["first_ts"].dt.strftime("%Y-%m-%d %H:%M:%S"),
            "Waktu O_Accepted": ev["second_ts"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        })
        evidence = {str(r[CASE]): {int(r["first_pos"]): res.first_activity,
                                   int(r["second_pos"]): res.second_activity}
                    for _, r in ev.iterrows()}
        self.explorer.set_log(prepared)
        self.explorer.set_cases(table, evidence)

    def reset(self):
        self.result = None
        self.answer.setText("")
        self.info.clear()
        self.explorer.clear()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        if self._df is not None:
            self.status.setText("Direset. Klik Jalankan Analisis.")
