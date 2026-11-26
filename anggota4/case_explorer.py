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
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from anggota1.theme import (
    BURGUNDY_EVIDENCE_BG,
    BURGUNDY_EVIDENCE_FG,
    TIMELINE_PALETTE,
    WARM_GRAY,
    configure_table,
    fit_table_height,
)
from .columns import ACT, CASE, LIFE, POS, RES, TS
from .ordering_11_22 import prepare_log

EVIDENCE_BG = BURGUNDY_EVIDENCE_BG
PALETTE = TIMELINE_PALETTE


class _CasesTableModel(QAbstractTableModel):
    """Lightweight table model so 31,500+ cases load instantaneously without UI freeze."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._headers: list[str] = []
        self._rows: list[tuple] = []

    def set_data(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        if df is None or (df.empty and len(df.columns) == 0):
            self._headers = []
            self._rows = []
        else:
            self._headers = [str(c) for c in df.columns]
            self._rows = list(df.itertuples(index=False, name=None))
        self.endResetModel()

    def clear(self) -> None:
        self.beginResetModel()
        self._headers = []
        self._rows = []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        val = self._rows[index.row()][index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(val, (int, float)):
                return val
            return "" if pd.isna(val) else str(val)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() > 0 and isinstance(val, (int, float)):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return None


class TimelineWidget(QWidget):
    """Timeline sederhana: event berurutan, event bukti diberi warna + label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(92)
        self._n = 0
        self._evidence: dict[int, str] = {}

    def set_events(self, n: int, evidence: dict[int, str] | None):
        self._n = n
        self._evidence = evidence or {}
        # Expand horizontally for large cases so timeline points stay readable inside QScrollArea
        self.setMinimumWidth(max(560, n * 18))
        self.update()

    def paintEvent(self, _):
        if self._n == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m, y = 28, self.height() // 2
        step = (self.width() - 2 * m) / max(self._n - 1, 1)
        p.setPen(QPen(QColor("#CFC4B8"), 2))
        p.drawLine(m, y, self.width() - m, y)
        r = 3 if self._n > 40 else 5
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(WARM_GRAY)))
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
            p.drawText(max(x - 40, 4), ty, f"#{pos + 1} {self._evidence[pos]}")
            p.setPen(Qt.PenStyle.NoPen)


class CaseDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df: pd.DataFrame | None = None
        self._idx: dict[str, object] = {}

        card = QFrame()
        card.setObjectName("Card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(10)

        self.stack = QStackedWidget()

        # Page 0: Empty state when no case is selected
        empty_frame = QFrame()
        empty_frame.setObjectName("EmptyState")
        empty_lay = QVBoxLayout(empty_frame)
        empty_lay.setContentsMargins(24, 32, 24, 32)
        empty_lay.setSpacing(6)
        empty_lay.addStretch()

        self.empty_title = QLabel("Belum ada case dipilih")
        self.empty_title.setObjectName("EmptyTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_desc = QLabel(
            "Pilih salah satu case pada tabel di atas untuk melihat ringkasan waktu, "
            "timeline aktivitas, dan rincian event."
        )
        self.empty_desc.setObjectName("EmptyDesc")
        self.empty_desc.setWordWrap(True)
        self.empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_lay.addWidget(self.empty_title)
        empty_lay.addWidget(self.empty_desc)
        empty_lay.addStretch()

        # Page 1: Selected case details
        detail_page = QWidget()
        detail_lay = QVBoxLayout(detail_page)
        detail_lay.setContentsMargins(0, 0, 0, 0)
        detail_lay.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        self.title = QLabel("Rincian Case")
        self.title.setObjectName("SectionTitle")
        self.meta_lbl = QLabel("")
        self.meta_lbl.setObjectName("Muted")
        self.meta_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(self.title)
        header_row.addStretch()
        header_row.addWidget(self.meta_lbl)

        self.timeline = TimelineWidget()
        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(True)
        self.timeline_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.timeline_scroll.setFixedHeight(104)
        self.timeline_scroll.setWidget(self.timeline)

        self.table = QTableView()
        self.model = QStandardItemModel(0, 0)
        self.table.setModel(self.model)
        configure_table(self.table, min_rows=5, row_height=38, header_height=42)

        detail_lay.addLayout(header_row)
        detail_lay.addWidget(self.timeline_scroll)
        detail_lay.addWidget(self.table, 1)

        self.stack.addWidget(empty_frame)
        self.stack.addWidget(detail_page)
        self.stack.setCurrentIndex(0)

        card_lay.addWidget(self.stack)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(card)

    def reset_empty(self, message: str | None = None):
        self.model.clear()
        self.timeline.set_events(0, None)
        self.title.setText("Rincian Case")
        self.meta_lbl.setText("")
        if message:
            self.empty_title.setText(message)
        else:
            self.empty_title.setText("Belum ada case dipilih")
        self.stack.setCurrentIndex(0)

    def set_log(self, df: pd.DataFrame):
        self._df = df if POS in df.columns else prepare_log(df)
        grouped = self._df.groupby(CASE, sort=False).indices
        # Case ID pada model GUI selalu ditampilkan sebagai string. Normalisasi
        # key di sini agar pencarian detail tidak gagal karena perbedaan tipe.
        self._idx = {str(case_id): positions for case_id, positions in grouped.items()}

    def show_case(self, case_id: str, evidence: dict[int, str] | None = None):
        case_id = str(case_id)
        if self._df is None or case_id not in self._idx:
            self.reset_empty(f"Case {case_id} tidak ditemukan di log aktif.")
            return

        ev = self._df.iloc[self._idx[case_id]].sort_values(POS)
        cols = [("No", None), ("Timestamp", TS), ("Aktivitas", ACT)]
        if LIFE in ev.columns:
            cols.append(("Lifecycle", LIFE))
        if RES in ev.columns:
            cols.append(("Resource", RES))
        cols.append(("Bukti", None))

        self.table.setUpdatesEnabled(False)
        try:
            self.model.clear()
            self.model.setHorizontalHeaderLabels([c[0] for c in cols])
            evidence = evidence or {}
            first_ev_row = None
            bold_font = QFont()
            bold_font.setBold(True)

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
                        it.setForeground(QBrush(BURGUNDY_EVIDENCE_FG))
                        it.setFont(bold_font)
                self.model.appendRow(items)

            header = self.table.horizontalHeader()
            for col_idx, (name, _) in enumerate(cols):
                mode = (
                    QHeaderView.ResizeMode.Stretch
                    if name == "Aktivitas"
                    else QHeaderView.ResizeMode.ResizeToContents
                )
                header.setSectionResizeMode(col_idx, mode)
        finally:
            self.table.setUpdatesEnabled(True)

        start_ts = ev[TS].min()
        end_ts = ev[TS].max()
        dur_days = (end_ts - start_ts).total_seconds() / 86400.0
        self.title.setText(f"Case {case_id} — {len(ev):,} event")
        self.meta_lbl.setText(
            f"{start_ts.strftime('%Y-%m-%d %H:%M')}  →  {end_ts.strftime('%Y-%m-%d %H:%M')}  "
            f"|  Durasi: {dur_days:.2f} hari"
        )
        self.timeline.set_events(len(ev), evidence)
        self.stack.setCurrentIndex(1)
        if first_ev_row is not None:
            self.table.scrollTo(
                self.model.index(first_ev_row, 0),
                QAbstractItemView.ScrollHint.PositionAtCenter,
            )
        else:
            self.table.scrollToTop()


class CaseExplorerWidget(QWidget):
    caseSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._evidence: dict[str, dict[int, str]] = {}

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cari Case ID...")
        self.search.setClearButtonEnabled(True)

        self.count_lbl = QLabel("0 case")
        self.count_lbl.setObjectName("Muted")

        self.model = _CasesTableModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        configure_table(self.table, min_rows=5, row_height=40, header_height=44)

        self.detail = CaseDetailWidget()

        top = QFrame()
        top.setObjectName("Card")
        tl = QVBoxLayout(top)
        tl.setContentsMargins(16, 14, 16, 14)
        tl.setSpacing(10)

        search_bar = QHBoxLayout()
        search_bar.setSpacing(10)
        search_bar.addWidget(self.search, 1)
        search_bar.addWidget(self.count_lbl)

        tl.addLayout(search_bar)
        tl.addWidget(self.table, 1)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(top)
        self.splitter.addWidget(self.detail)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.splitter, 1)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.search.textChanged.connect(self._on_search)
        self.table.selectionModel().currentRowChanged.connect(self._on_row)
        self.table.doubleClicked.connect(self._open_case_dialog)

    def set_log(self, df: pd.DataFrame):
        self.detail.set_log(df)
        self.detail.reset_empty()

    def set_cases(self, table_df: pd.DataFrame, evidence: dict | None = None):
        """Kolom pertama table_df harus Case ID."""
        self._evidence = {
            str(case_id): labels
            for case_id, labels in (evidence or {}).items()
        }

        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.proxy.setFilterFixedString("")

        self.detail.reset_empty()

        self.table.setSortingEnabled(False)
        self.model.set_data(table_df)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        row_count = len(table_df)
        fit_table_height(self.table, row_count, min_rows=5, max_rows=7, row_height=40, header_height=44)

        self.count_lbl.setText(f"{row_count:,} case")
        self.table.clearSelection()
        self.table.scrollToTop()
        self.table.verticalScrollBar().setValue(0)

    def clear(self):
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.proxy.setFilterFixedString("")
        self.model.clear()
        self._evidence = {}
        fit_table_height(self.table, 0, min_rows=5, max_rows=7, row_height=40, header_height=44)
        self.count_lbl.setText("0 case")
        self.detail.reset_empty()

    def _on_search(self, text: str):
        self.proxy.setFilterFixedString(text)
        if text.strip():
            self.count_lbl.setText(f"{self.proxy.rowCount():,} case (terfilter)")
        else:
            self.count_lbl.setText(f"{self.proxy.rowCount():,} case")
        self.table.scrollToTop()
        self.table.verticalScrollBar().setValue(0)

    def _on_row(self, current, _prev):
        if not current.isValid():
            return
        cid = str(self.proxy.index(current.row(), 0).data())
        self.detail.show_case(cid, self._evidence.get(cid))
        self.caseSelected.emit(cid)

    def select_case(self, case_id: str) -> bool:
        """Pilih case dari kode luar, misalnya double-click tabel Overview."""
        target = str(case_id)
        self.search.clear()
        for row in range(self.proxy.rowCount()):
            index = self.proxy.index(row, 0)
            if str(index.data()) == target:
                self.table.setCurrentIndex(index)
                self.table.selectRow(row)
                self.table.scrollTo(index)
                self.detail.show_case(target, self._evidence.get(target))
                self.caseSelected.emit(target)
                return True
        return False

    def _open_case_dialog(self, index):
        if not index.isValid() or self.detail._df is None:
            return
        case_id = str(self.proxy.index(index.row(), 0).data())
        dialog = CaseDetailDialog(
            self,
            self.detail._df,
            case_id,
            self._evidence.get(case_id),
        )
        dialog.exec()


class CaseDetailDialog(QDialog):
    def __init__(self, parent, df: pd.DataFrame, case_id: str, evidence=None):
        super().__init__(parent)
        self.setWindowTitle(f"Rincian Case {case_id}")
        self.resize(900, 560)
        self.detail = CaseDetailWidget()
        self.detail.set_log(df)
        self.detail.show_case(case_id, evidence)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.addWidget(self.detail)


def open_case_detail_dialog(parent, df, case_id, evidence=None):
    """Dipakai panel 11.7 / 11.15 / 11.18 untuk tombol 'buka rincian case'."""
    dlg = CaseDetailDialog(parent, df, case_id, evidence)
    dlg.exec()
