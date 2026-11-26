"""Komponen bersama: aturan analisis, jumlah case, denominator, persentase.
Anggota 2 dan 3 pakai juga: bar.set_info(rule, selected, denominator, percentage)."""
import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class AnalysisInfoBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self._lbl = QLabel("Belum ada analisis dijalankan.")
        self._lbl.setWordWrap(True)
        self._lbl.setTextFormat(Qt.RichText)
        lay = QVBoxLayout(self)
        lay.addWidget(self._lbl)

    def clear(self):
        self._lbl.setText("Belum ada analisis dijalankan.")

    def set_info(self, rule: str, selected: int,
                 denominator: int | None = None, percentage: float | None = None):
        txt = f"<b>Aturan:</b> {html.escape(rule)}<br><b>Case terpilih:</b> {selected:,}"
        if denominator is not None:
            txt += f"<br><b>Denominator (seluruh case log aktif):</b> {denominator:,}"
        if percentage is not None:
            txt += f"<br><b>Persentase:</b> {percentage:.2f}%"
        self._lbl.setText(txt)
