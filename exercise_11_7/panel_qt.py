"""PySide6 adapter for Nayla's Exercise 11.7 analysis.

The original Tkinter panel.py is preserved. This widget reuses the same
exercise_11_7.analysis logic and the team's shared prepare_log ordering rule,
so it can be embedded in the main PySide6 application.
"""
from __future__ import annotations

import math

import pandas as pd
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from anggota4.ordering_11_22 import prepare_log
from .analysis import (
    ACTIVITY,
    CASE_ID,
    TIMESTAMP,
    Answer,
    analyze_dataframe,
)

PAGE_SIZE = 100
LIFECYCLE = "lifecycle:transition"
RESOURCE = "org:resource"


class _Exercise117Worker(QThread):
    succeeded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, log: pd.DataFrame):
        super().__init__()
        self._log = log

    def run(self):
        try:
            # Prepare once, then let the existing analysis consume the
            # already ordered DataFrame without sorting it a second time.
            prepared = prepare_log(self._log)
            answers = analyze_dataframe(prepared, lambda frame: frame)
            self.succeeded.emit(prepared, answers)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class Panel117(QWidget):
    """Exercise 11.7 A-E embedded as a native PySide6 page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._log: pd.DataFrame | None = None
        self._prepared_log: pd.DataFrame | None = None
        self._worker: _Exercise117Worker | None = None

        self.answers: tuple[Answer, ...] = ()
        self.current_answer: Answer | None = None
        self.filtered_cases = []
        self.page = 0

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(12)

        # Actions and processing status.
        action_row = QHBoxLayout()

        self.btn_run = QPushButton("Jalankan Analisis")
        self.btn_run.setObjectName("PrimaryButton")
        self.btn_run.setEnabled(False)

        self.btn_reset = QPushButton("Reset Hasil")
        self.btn_reset.setObjectName("SecondaryButton")

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumWidth(150)

        self.status = QLabel("Impor log XES untuk memulai.")
        self.status.setObjectName("Muted")

        action_row.addWidget(self.btn_run)
        action_row.addWidget(self.btn_reset)
        action_row.addWidget(self.progress)
        action_row.addWidget(self.status, 1)
        root.addLayout(action_row)

        self.description = QLabel(
            "Exercise 11.7 — Case count and cycle time. "
            "Pilih salah satu butir A–E untuk melihat case yang termasuk "
            "dalam perhitungan."
        )
        self.description.setObjectName("InfoText")
        self.description.setWordWrap(True)
        root.addWidget(self.description)

        # Summary table.
        summary_title = QLabel("RINGKASAN HASIL ANALISIS")
        summary_title.setObjectName("SectionTitle")
        root.addWidget(summary_title)

        self.summary = QTableWidget(0, 4)
        self.summary.setObjectName("DataTable")
        self.summary.setHorizontalHeaderLabels(
            ["Butir", "Pertanyaan", "Jumlah Case", "Rata-rata (hari)"]
        )
        self.summary.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.summary.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.summary.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.summary.setAlternatingRowColors(True)
        self.summary.verticalHeader().setVisible(False)
        self.summary.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.summary.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.summary.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.summary.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.summary.setMaximumHeight(220)
        root.addWidget(self.summary)

        self.rule_label = QLabel(
            "Pilih baris A–E untuk melihat aturan dan daftar case."
        )
        self.rule_label.setWordWrap(True)
        self.rule_label.setObjectName("Muted")
        root.addWidget(self.rule_label)

        # Case search.
        search_row = QHBoxLayout()
        search_label = QLabel("Cari Case ID")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Masukkan Case ID...")
        self.search_button = QPushButton("Cari")
        self.search_button.setObjectName("SecondaryButton")

        search_row.addWidget(search_label)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        self.case_count_label = QLabel("0 case")
        self.case_count_label.setObjectName("Muted")
        root.addWidget(self.case_count_label)

        # Case result table.
        self.cases = QTableWidget(0, 2)
        self.cases.setObjectName("DataTable")
        self.cases.setHorizontalHeaderLabels(
            ["Case ID", "Durasi (hari)"]
        )
        self.cases.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.cases.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.cases.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.cases.setAlternatingRowColors(True)
        self.cases.verticalHeader().setVisible(False)
        self.cases.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.cases.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        root.addWidget(self.cases, 1)

        # Pagination and case detail.
        footer = QHBoxLayout()
        self.page_label = QLabel("0 case")
        self.page_label.setObjectName("Muted")

        self.btn_previous = QPushButton("Sebelumnya")
        self.btn_previous.setObjectName("SecondaryButton")
        self.btn_next = QPushButton("Berikutnya")
        self.btn_next.setObjectName("SecondaryButton")
        self.btn_open_case = QPushButton("Lihat Rincian Case")
        self.btn_open_case.setObjectName("PrimaryButton")
        self.btn_open_case.setEnabled(False)

        footer.addWidget(self.page_label)
        footer.addStretch()
        footer.addWidget(self.btn_previous)
        footer.addWidget(self.btn_next)
        footer.addWidget(self.btn_open_case)
        root.addLayout(footer)

        self.btn_run.clicked.connect(self.run)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_previous.clicked.connect(lambda: self._turn_page(-1))
        self.btn_next.clicked.connect(lambda: self._turn_page(1))
        self.btn_open_case.clicked.connect(self._open_selected_case)
        self.search_button.clicked.connect(self._apply_search)
        self.search_input.returnPressed.connect(self._apply_search)
        self.summary.itemSelectionChanged.connect(self._select_answer)
        self.cases.itemSelectionChanged.connect(self._sync_open_button)
        self.cases.cellDoubleClicked.connect(
            lambda _row, _column: self._open_selected_case()
        )

    # --------------------------------------------------
    # API for MainWindow
    # --------------------------------------------------

    def set_log(self, log: pd.DataFrame):
        """Receive the active DataFrame after each successful XES import."""
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(
                self,
                "Analisis sedang berjalan",
                "Tunggu analisis Exercise 11.7 selesai sebelum mengganti dataset.",
            )
            return

        self._log = log
        self._prepared_log = None
        self.reset()
        self.btn_run.setEnabled(log is not None)
        self.status.setText(
            "Log siap. Klik Jalankan Analisis."
            if log is not None
            else "Impor log XES untuk memulai."
        )

    def export_payload(self):
        """Return (summary_dict, case_dataframe) for the currently selected item."""
        if self.current_answer is None:
            return None

        answer = self.current_answer
        summary = {
            "exercise": "11.7",
            "item": answer.code,
            "question": answer.title,
            "rule": answer.rule,
            "case_count": answer.count,
            "mean_cycle_time_days": (
                round(answer.mean_days, 6)
                if answer.mean_days is not None
                else None
            ),
        }
        case_data = pd.DataFrame(
            [
                {"case_id": case.case_id, "duration_days": case.days}
                for case in answer.cases
            ],
            columns=["case_id", "duration_days"],
        )
        return summary, case_data

    # --------------------------------------------------
    # Analysis lifecycle
    # --------------------------------------------------

    def run(self):
        if self._log is None:
            self.status.setText("Impor log XES terlebih dahulu.")
            return

        if self._worker is not None and self._worker.isRunning():
            return

        missing = [
            column
            for column in (CASE_ID, ACTIVITY, TIMESTAMP)
            if column not in self._log.columns
        ]
        if missing:
            self.status.setText(
                "Atribut wajib tidak tersedia: " + ", ".join(missing)
            )
            return

        self.reset(clear_status=False)
        self.btn_run.setEnabled(False)
        self.progress.setRange(0, 0)
        self.status.setText(
            "Menghitung A–E dan cycle time seluruh case..."
        )

        self._worker = _Exercise117Worker(self._log)
        self._worker.succeeded.connect(self._on_analysis_done)
        self._worker.failed.connect(self._on_analysis_failed)
        self._worker.start()

    def _on_analysis_done(self, prepared, answers):
        self._prepared_log = prepared
        self.answers = tuple(answers)

        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.btn_run.setEnabled(True)
        self.status.setText("Analisis Exercise 11.7 selesai.")

        self.summary.setRowCount(len(self.answers))

        for row, answer in enumerate(self.answers):
            count_text = "—" if answer.code == "B" else f"{answer.count:,}"
            mean_text = (
                f"{answer.mean_days:.4f}"
                if answer.mean_days is not None
                else "—"
            )

            values = [
                answer.code,
                answer.title,
                count_text,
                mean_text,
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (0, 2, 3):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )
                self.summary.setItem(row, column, item)

        if self.answers:
            self.summary.selectRow(0)
            self._select_answer()

    def _on_analysis_failed(self, message: str):
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.btn_run.setEnabled(self._log is not None)
        self.status.setText("Analisis gagal.")
        QMessageBox.critical(
            self,
            "Exercise 11.7",
            message,
        )

    def reset(self, *, clear_status=True):
        self.answers = ()
        self.current_answer = None
        self.filtered_cases = []
        self.page = 0
        self.summary.setRowCount(0)
        self.cases.setRowCount(0)
        self.search_input.clear()
        self.rule_label.setText(
            "Pilih baris A–E untuk melihat aturan dan daftar case."
        )
        self.case_count_label.setText("0 case")
        self.page_label.setText("0 case")
        self.btn_open_case.setEnabled(False)
        self.btn_previous.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

        if clear_status:
            self.status.setText(
                "Log siap. Klik Jalankan Analisis."
                if self._log is not None
                else "Impor log XES untuk memulai."
            )

    # --------------------------------------------------
    # Summary selection, search and pagination
    # --------------------------------------------------

    def _select_answer(self):
        row = self.summary.currentRow()
        if row < 0 or row >= len(self.answers):
            return

        code_item = self.summary.item(row, 0)
        if code_item is None:
            return

        code = code_item.text()
        self.current_answer = next(
            (answer for answer in self.answers if answer.code == code),
            None,
        )
        if self.current_answer is None:
            return

        self.rule_label.setText(
            f"Butir {self.current_answer.code}: "
            f"{self.current_answer.rule}"
        )
        self.page = 0
        self._apply_search()

    def _apply_search(self):
        if self.current_answer is None:
            return

        query = self.search_input.text().strip().casefold()
        self.filtered_cases = [
            case
            for case in self.current_answer.cases
            if not query or query in case.case_id.casefold()
        ]
        self.page = 0
        self._render_cases()

    def _render_cases(self):
        total = len(self.filtered_cases)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        self.page = max(0, min(self.page, total_pages - 1))

        start = self.page * PAGE_SIZE
        visible = self.filtered_cases[start:start + PAGE_SIZE]

        self.cases.setRowCount(len(visible))
        for row, case in enumerate(visible):
            case_item = QTableWidgetItem(case.case_id)
            duration_item = QTableWidgetItem(f"{case.days:.4f}")
            duration_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.cases.setItem(row, 0, case_item)
            self.cases.setItem(row, 1, duration_item)

        if total:
            first = start + 1
            last = start + len(visible)
            self.case_count_label.setText(
                f"{total:,} case ditemukan"
            )
            self.page_label.setText(
                f"Menampilkan {first:,}–{last:,} dari {total:,} case "
                f"| Halaman {self.page + 1}/{total_pages}"
            )
        else:
            self.case_count_label.setText("0 case ditemukan")
            self.page_label.setText("Tidak ada case untuk ditampilkan.")

        self.btn_previous.setEnabled(self.page > 0)
        self.btn_next.setEnabled(self.page < total_pages - 1)
        self.btn_open_case.setEnabled(False)

    def _turn_page(self, direction: int):
        self.page += direction
        self._render_cases()

    def _sync_open_button(self):
        self.btn_open_case.setEnabled(
            self.cases.currentRow() >= 0
        )

    # --------------------------------------------------
    # Case detail
    # --------------------------------------------------

    def _open_selected_case(self):
        row = self.cases.currentRow()
        if row < 0 or self._prepared_log is None:
            return

        item = self.cases.item(row, 0)
        if item is None:
            return

        case_id = item.text()
        case_mask = self._prepared_log[CASE_ID].astype(str) == case_id
        events = self._prepared_log.loc[case_mask].copy()

        if events.empty:
            QMessageBox.information(
                self,
                "Case Explorer",
                f"Event untuk {case_id} tidak ditemukan.",
            )
            return

        columns = [TIMESTAMP, ACTIVITY]
        for optional in (LIFECYCLE, RESOURCE):
            if optional in events.columns:
                columns.append(optional)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Case Detail — {case_id}")
        dialog.resize(900, 560)

        layout = QVBoxLayout(dialog)

        heading = QLabel(case_id)
        heading.setStyleSheet(
            "font-size: 14pt; font-weight: 700; color: #17243A;"
        )
        layout.addWidget(heading)

        meta = QLabel(
            f"{len(events):,} event | "
            "Urutan mengikuti timestamp dan urutan asli pada file XES."
        )
        meta.setObjectName("Muted")
        layout.addWidget(meta)

        table = QTableWidget(0, len(columns))
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels(
            [
                "Timestamp" if column == TIMESTAMP
                else "Activity" if column == ACTIVITY
                else "Lifecycle" if column == LIFECYCLE
                else "Resource"
                for column in columns
            ]
        )
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table.setRowCount(len(events))

        for row_index, (_, event) in enumerate(events.iterrows()):
            for column_index, column in enumerate(columns):
                value = event[column]
                if pd.isna(value):
                    display = "—"
                elif column == TIMESTAMP:
                    display = pd.to_datetime(
                        value, utc=True
                    ).strftime("%Y-%m-%d %H:%M:%S UTC")
                else:
                    display = str(value)

                table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(display),
                )

        layout.addWidget(table, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec()
