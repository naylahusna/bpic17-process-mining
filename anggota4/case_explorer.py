"""Case Explorer: tabel hasil (cari by case ID) + rincian event + timeline.

Cara pakai dari panel mana pun:
    ex = CaseExplorerWidget()
    ex.set_log(df)                       # df log aktif (boleh belum diprepare)
    ex.set_cases(table_df, evidence)     # table_df kolom pertama = Case ID
        # evidence (opsional): {case_id: {pos_0based: "label"}} -> baris disorot
Dari panel lain tanpa explorer: open_case_detail_dialog(parent, df, case_id, evidence)
"""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QHeaderView, QLabel, QLineEdit, QSplitter,
                               QTableView, QVBoxLayout, QWidget)

from .columns import ACT, CASE, LIFE, POS, RES, TS
from .ordering_11_22 import prepare_log

EVIDENCE_BG = QColor(255, 235, 150)
PALETTE = [QColor(200, 60, 60), QColor(40, 150, 80), QColor(60, 100, 200), QColor(220, 140, 30)]


class TimelineWidget(QWidget):
    """Timeline sederhana: event berurutan, event bukti diberi warna + label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self._n = 0
        self._evidence: dict[int, str] = {}

    def set_events(self, n: int, evidence: dict[int, str] | None):
        self._n = n
        self._evidence = evidence or {}
        self.update()

    def paintEvent(self, _):
        if self._n == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m, y = 24, self.height() // 2
        step = (self.width() - 2 * m) / max(self._n - 1, 1)
        p.setPen(QPen(QColor(160, 160, 160), 2))
        p.drawLine(m, y, self.width() - m, y)
        r = 3 if self._n > 40 else 5
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(120, 120, 120)))
        for i in range(self._n):
            if i not in self._evidence:
                p.drawEllipse(int(m + i * step) - r, y - r, 2 * r, 2 * r)
        for k, pos in enumerate(sorted(self._evidence)):
            if pos >= self._n:
                continue
            x = int(m + pos * step)
            col = PALETTE[k % len(PALETTE)]
            p.setBrush(QBrush(col))
            p.drawEllipse(x - 7, y - 7, 14, 14)
            p.setPen(col)
            ty = y - 16 if k % 2 == 0 else y + 26
            p.drawText(max(x - 40, 0), ty, f"#{pos + 1} {self._evidence[pos]}")
            p.setPen(Qt.NoPen)


class CaseDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df: pd.DataFrame | None = None
        self._idx: dict = {}
        self.title = QLabel("Pilih case untuk melihat rincian.")
        self.timeline = TimelineWidget()
        self.table = QTableView()
        self.model = QStandardItemModel(0, 0)
        self.table.setModel(self.model)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        lay = QVBoxLayout(self)
        lay.addWidget(self.title)
        lay.addWidget(self.timeline)
        lay.addWidget(self.table)

    def set_log(self, df: pd.DataFrame):
        self._df = df if POS in df.columns else prepare_log(df)
        self._idx = self._df.groupby(CASE, sort=False).indices

    def show_case(self, case_id: str, evidence: dict[int, str] | None = None):
        if self._df is None or case_id not in self._idx:
            self.title.setText(f"Case {case_id} tidak ditemukan di log aktif.")
            return
        ev = self._df.iloc[self._idx[case_id]].sort_values(POS)
        cols = [("No", None), ("Timestamp", TS), ("Aktivitas", ACT)]
        if LIFE in ev.columns:
            cols.append(("Lifecycle", LIFE))
        if RES in ev.columns:
            cols.append(("Resource", RES))
        cols.append(("Bukti", None))

        self.model.clear()
        self.model.setHorizontalHeaderLabels([c[0] for c in cols])
        evidence = evidence or {}
        first_ev_row = None
        for _, row in ev.iterrows():
            pos = int(row[POS])
            vals = []
            for name, col in cols:
                if name == "No":
                    vals.append(str(pos + 1))
                elif name == "Bukti":
                    vals.append(evidence.get(pos, ""))
                elif col == TS:
                    vals.append(row[TS].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
                else:
                    v = row[col]
                    vals.append("" if pd.isna(v) else str(v))
            items = [QStandardItem(v) for v in vals]
            if pos in evidence:
                if first_ev_row is None:
                    first_ev_row = self.model.rowCount()
                for it in items:
                    it.setBackground(QBrush(EVIDENCE_BG))
            self.model.appendRow(items)
        self.title.setText(f"<b>Case {case_id}</b> - {len(ev)} event")
        self.timeline.set_events(len(ev), evidence)
        if first_ev_row is not None:
            self.table.scrollTo(self.model.index(first_ev_row, 0),
                                QAbstractItemView.ScrollHint.PositionAtCenter)


class CaseExplorerWidget(QWidget):
    caseSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._evidence: dict[str, dict[int, str]] = {}
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari Case ID...")
        self.count_lbl = QLabel("0 case")
        self.model = QStandardItemModel(0, 0)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.detail = CaseDetailWidget()

        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(self.search)
        tl.addWidget(self.count_lbl)
        tl.addWidget(self.table)
        split = QSplitter(Qt.Vertical)
        split.addWidget(top)
        split.addWidget(self.detail)
        lay = QVBoxLayout(self)
        lay.addWidget(split)

        self.search.textChanged.connect(self._on_search)
        self.table.selectionModel().currentRowChanged.connect(self._on_row)

    def set_log(self, df: pd.DataFrame):
        self.detail.set_log(df)

    def set_cases(self, table_df: pd.DataFrame, evidence: dict | None = None):
        """Kolom pertama table_df harus Case ID."""
        self._evidence = evidence or {}
        self.model.clear()
        self.model.setHorizontalHeaderLabels([str(c) for c in table_df.columns])
        for row in table_df.itertuples(index=False):
            items = []
            for v in row:
                it = QStandardItem()
                it.setData(v if isinstance(v, (int, float)) else str(v), Qt.DisplayRole)
                items.append(it)
            self.model.appendRow(items)
        self.count_lbl.setText(f"{len(table_df):,} case")
        self.table.sortByColumn(0, Qt.AscendingOrder)

    def clear(self):
        self.model.clear()
        self._evidence = {}
        self.count_lbl.setText("0 case")
        self.detail.title.setText("Pilih case untuk melihat rincian.")
        self.detail.model.clear()
        self.detail.timeline.set_events(0, None)

    def _on_search(self, text: str):
        self.proxy.setFilterFixedString(text)
        self.count_lbl.setText(f"{self.proxy.rowCount():,} case (terfilter)")

    def _on_row(self, current, _prev):
        if not current.isValid():
            return
        cid = self.proxy.index(current.row(), 0).data()
        self.detail.show_case(cid, self._evidence.get(cid))
        self.caseSelected.emit(cid)


class CaseDetailDialog(QDialog):
    def __init__(self, parent, df: pd.DataFrame, case_id: str, evidence=None):
        super().__init__(parent)
        self.setWindowTitle(f"Rincian Case {case_id}")
        self.resize(850, 520)
        self.detail = CaseDetailWidget()
        self.detail.set_log(df)
        self.detail.show_case(case_id, evidence)
        QVBoxLayout(self).addWidget(self.detail)


def open_case_detail_dialog(parent, df, case_id, evidence=None):
    """Dipakai panel 11.7 / 11.15 / 11.18 untuk tombol 'buka rincian case'."""
    dlg = CaseDetailDialog(parent, df, case_id, evidence)
    dlg.exec()
