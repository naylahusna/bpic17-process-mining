from pathlib import Path
import sys

import pandas as pd

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QMessageBox,
    QProgressBar, QScrollArea, QStackedWidget, QInputDialog
)

from anggota1.importer import load_xes
from anggota1.overview import build_overview
from anggota4.columns import CASE, ACT, TS
from anggota4.case_explorer import CaseExplorerWidget
from anggota4.panel_11_22 import Panel1122
from exercise_11_7.panel_qt import Panel117
from src.gui.panel_11_15 import Panel1115
from src.gui.panel_11_18 import Panel1118
from anggota1.theme import build_stylesheet, configure_table


class DatasetWorker(QThread):
    """Membaca XES dan menghitung overview di background."""

    succeeded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            imported = load_xes(self.file_path)
            overview = build_overview(imported.dataframe)
            self.succeeded.emit(imported, overview)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("BPIC17 Process Mining")
        self.resize(1350, 850)
        self.setMinimumSize(1100, 720)

        self.worker = None
        self.active_log = None
        self.active_import = None
        self.active_overview = None

        self.metric_values = {}
        self.nav_buttons = {}
        self.page_scrolls = {}
        self.export_cards = {}

        self._build_ui()
        self._apply_style()

    # --------------------------------------------------
    # MAIN UI
    # --------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 25)
        content_layout.setSpacing(15)

        # HEADER
        header = QHBoxLayout()
        title_area = QVBoxLayout()

        self.page_title = QLabel("Overview Dashboard")
        self.page_title.setObjectName("PageTitle")

        self.page_subtitle = QLabel(
            "Business Process Intelligence | BPI Challenge 2017"
        )
        self.page_subtitle.setObjectName("Muted")

        title_area.addWidget(self.page_title)
        title_area.addWidget(self.page_subtitle)

        header.addLayout(title_area)
        header.addStretch()

        self.import_button = QPushButton("+ Import XES")
        self.import_button.setObjectName("PrimaryButton")
        self.import_button.clicked.connect(self.open_file)

        header.addWidget(self.import_button)
        content_layout.addLayout(header)

        # DATASET INFORMATION
        self.file_label = QLabel("No dataset loaded")
        self.file_label.setObjectName("FileInfo")
        content_layout.addWidget(self.file_label)

        # IMPORT PROGRESS
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        content_layout.addWidget(self.progress)

        # STACKED PAGES
        self.pages = QStackedWidget()

        # PAGE 1: OVERVIEW
        self.overview_page = QWidget()
        overview_layout = QVBoxLayout(self.overview_page)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.setSpacing(15)

        cards = QGridLayout()
        cards.setSpacing(15)
        for col in range(4):
            cards.setColumnStretch(col, 1)

        self._add_metric(
            cards, 0, 0, "TOTAL CASES", "—", "Unique process cases"
        )
        self._add_metric(
            cards, 0, 1, "TOTAL EVENTS", "—", "Total recorded events"
        )
        self._add_metric(
            cards, 0, 2, "CYCLE TIME", "—", "Average duration in days"
        )
        self._add_metric(
            cards, 0, 3, "ACTIVITIES", "—", "Unique activity types"
        )

        overview_layout.addLayout(cards)

        # PROCESS TIME RANGE
        range_card = QFrame()
        range_card.setObjectName("Card")
        range_layout = QVBoxLayout(range_card)
        range_layout.setContentsMargins(18, 14, 18, 14)
        range_layout.setSpacing(4)

        range_title = QLabel("PROCESS TIME RANGE")
        range_title.setObjectName("SectionTitle")

        self.range_label = QLabel("Waiting for dataset...")
        self.range_label.setObjectName("RangeValue")

        range_layout.addWidget(range_title)
        range_layout.addWidget(self.range_label)
        overview_layout.addWidget(range_card)

        # TABLES
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(15)

        activity_card = self._build_table_card(
            "ACTIVITY FREQUENCY",
            ["Activity", "Events", "Cases"]
        )
        self.activity_table = activity_card.findChild(
            QTableWidget, "DataTable"
        )
        self.activity_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.activity_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.activity_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )

        case_card = self._build_table_card(
            "LONGEST CASE DURATIONS",
            ["Case ID", "Start", "End", "Days"]
        )
        self.case_table = case_card.findChild(
            QTableWidget, "DataTable"
        )
        self.case_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for col_idx in (1, 2, 3):
            self.case_table.horizontalHeader().setSectionResizeMode(
                col_idx, QHeaderView.ResizeMode.ResizeToContents
            )
        self.case_table.cellDoubleClicked.connect(self._open_overview_case)

        tables_layout.addWidget(activity_card, 1)
        tables_layout.addWidget(case_card, 1)
        overview_layout.addLayout(tables_layout, 1)

        self.status_label = QLabel(
            "Ready | Import a BPIC17 XES event log to begin."
        )
        self.status_label.setObjectName("Muted")
        overview_layout.addWidget(self.status_label)

        self.page_scrolls["overview"] = self._wrap_scroll(self.overview_page)
        self.pages.addWidget(self.page_scrolls["overview"])

        # PAGE 2: EXERCISE 11.7 (NAYLA, PySide6 adapter)
        self.panel_117 = Panel117()
        self.page_scrolls["11.7"] = self._wrap_scroll(self.panel_117)
        self.pages.addWidget(self.page_scrolls["11.7"])

        # PAGE 3: EXERCISE 11.15 (ANGGOTA 3)
        self.panel_1115 = Panel1115()
        self.page_scrolls["11.15"] = self._wrap_scroll(self.panel_1115)
        self.pages.addWidget(self.page_scrolls["11.15"])

        # PAGE 4: EXERCISE 11.18 (ANGGOTA 3)
        self.panel_1118 = Panel1118()
        self.page_scrolls["11.18"] = self._wrap_scroll(self.panel_1118)
        self.pages.addWidget(self.page_scrolls["11.18"])

        # PAGE 5: EXERCISE 11.22 (ANGGOTA 4)
        self.panel_1122 = Panel1122()
        self.page_scrolls["11.22"] = self._wrap_scroll(self.panel_1122)
        self.pages.addWidget(self.page_scrolls["11.22"])

        # PAGE 6: GLOBAL CASE EXPLORER
        self.case_explorer = CaseExplorerWidget()
        self.case_explorer.set_cases(
            pd.DataFrame(columns=["Case ID", "Events", "Start", "End", "Duration (days)"]),
            {}
        )
        self.page_scrolls["cases"] = self._wrap_scroll(self.case_explorer)
        self.pages.addWidget(self.page_scrolls["cases"])

        # PAGE 7: EXPORT CSV
        self.export_page = self._build_export_page()
        self.page_scrolls["export"] = self._wrap_scroll(self.export_page)
        self.pages.addWidget(self.page_scrolls["export"])

        self.pages.setCurrentWidget(self.page_scrolls["overview"])
        content_layout.addWidget(self.pages, 1)

        root.addWidget(content, 1)

    @staticmethod
    def _wrap_scroll(widget: QWidget) -> QScrollArea:
        """Wrap a page widget in a single vertical QScrollArea with widgetResizable=True."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        return scroll

    # --------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 25, 18, 20)
        layout.setSpacing(10)

        brand = QLabel("BPIC17\nPROCESS MINING")
        brand.setObjectName("Brand")

        brand_subtitle = QLabel("PROCESS INTELLIGENCE")
        brand_subtitle.setObjectName("BrandSubtitle")

        layout.addWidget(brand)
        layout.addWidget(brand_subtitle)
        layout.addSpacing(25)

        section = QLabel("WORKSPACE")
        section.setObjectName("SidebarSection")
        layout.addWidget(section)

        self._add_nav(
            layout, "Overview", True, True,
            lambda: self.show_page("overview")
        )
        self._add_nav(
            layout, "Import Data", True, False,
            self.open_file, checkable=False
        )

        layout.addSpacing(15)

        analysis_section = QLabel("ANALYSIS MODULES")
        analysis_section.setObjectName("SidebarSection")
        layout.addWidget(analysis_section)

        self._add_nav(
            layout, "Exercise 11.7", True, False,
            lambda: self.show_page("11.7")
        )
        self._add_nav(
            layout, "Exercise 11.15", True, False,
            lambda: self.show_page("11.15")
        )
        self._add_nav(
            layout, "Exercise 11.18", True, False,
            lambda: self.show_page("11.18")
        )
        self._add_nav(
            layout, "Exercise 11.22", True, False,
            lambda: self.show_page("11.22")
        )

        layout.addSpacing(15)

        tools_section = QLabel("TOOLS")
        tools_section.setObjectName("SidebarSection")
        layout.addWidget(tools_section)

        self._add_nav(
            layout, "Case Explorer", True, False,
            lambda: self.show_page("cases")
        )
        self._add_nav(
            layout, "Export CSV", True, False,
            lambda: self.show_page("export")
        )

        layout.addStretch()

        version = QLabel("BPIC17 PROJECT\nVersion 1.0")
        version.setObjectName("SidebarFooter")
        layout.addWidget(version)

        return sidebar

    def _add_nav(
        self, layout, text, enabled=True,
        selected=False, callback=None, checkable=True
    ):
        button = QPushButton(text)
        button.setObjectName("NavButton")
        button.setEnabled(enabled)
        button.setCheckable(checkable)
        button.setChecked(selected)

        if callback:
            button.clicked.connect(callback)

        if checkable:
            self.nav_buttons[text] = button

        if not enabled:
            button.setToolTip(
                "Menunggu integrasi modul anggota kelompok."
            )

        layout.addWidget(button)
        return button

    def show_page(self, page):
        pages = {
            "overview": (
                self.page_scrolls["overview"],
                "Overview Dashboard",
                "Business Process Intelligence | BPI Challenge 2017",
                "Overview",
            ),
            "11.7": (
                self.page_scrolls["11.7"],
                "Exercise 11.7",
                "Case Analysis | Case Count and Cycle Time",
                "Exercise 11.7",
            ),
            "11.15": (
                self.page_scrolls["11.15"],
                "Exercise 11.15",
                "Repeated Complete | W_Assess Potential Fraud",
                "Exercise 11.15",
            ),
            "11.18": (
                self.page_scrolls["11.18"],
                "Exercise 11.18",
                "Same Resource | W_Assess Potential Fraud",
                "Exercise 11.18",
            ),
            "11.22": (
                self.page_scrolls["11.22"],
                "Exercise 11.22",
                "Ordering Analysis | O_Cancelled before O_Accepted",
                "Exercise 11.22",
            ),
            "cases": (
                self.page_scrolls["cases"],
                "Case Explorer",
                "Browse all cases and inspect their event timelines",
                "Case Explorer",
            ),
            "export": (
                self.page_scrolls["export"],
                "Export CSV",
                "Ekspor hasil analisis dan Case Register ke file CSV (UTF-8 BOM)",
                "Export CSV",
            ),
        }

        config = pages.get(page)
        if config is None:
            return

        widget, title, subtitle, selected = config
        if page == "export":
            self._refresh_export_cards()
        self.pages.setCurrentWidget(widget)
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

        for name, button in self.nav_buttons.items():
            button.setChecked(name == selected)

    # --------------------------------------------------
    # STATISTIC CARDS
    # --------------------------------------------------

    def _add_metric(self, grid, row, col, title, value, desc):
        card = QFrame()
        card.setObjectName("MetricCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")

        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")

        desc_label = QLabel(desc)
        desc_label.setObjectName("Muted")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)

        grid.addWidget(card, row, col)

        self.metric_values[title] = value_label

    # --------------------------------------------------
    # TABLES
    # --------------------------------------------------

    def _build_table_card(self, title, headers):
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)

        table = QTableWidget(0, len(headers))
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels(headers)
        configure_table(table, min_rows=5, row_height=38, header_height=42)

        layout.addWidget(table, 1)

        return card

    # --------------------------------------------------
    # IMPORT XES
    # --------------------------------------------------

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select BPIC17 Event Log",
            "",
            "XES Files (*.xes *.xes.gz);;All Files (*)"
        )

        if file_path:
            self.load_dataset(file_path)

    def load_dataset(self, file_path):
        if self.worker and self.worker.isRunning():
            return

        self.import_button.setEnabled(False)
        self.progress.show()

        self.file_label.setText(
            f"Loading: {Path(file_path).name}"
        )
        self.status_label.setText(
            "Reading XES and calculating overview..."
        )

        self.worker = DatasetWorker(file_path)

        self.worker.succeeded.connect(self._on_loaded)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_worker_finished)

        self.worker.start()

    # --------------------------------------------------
    # UPDATE DASHBOARD
    # --------------------------------------------------

    def _on_loaded(self, imported, overview):
        self.active_import = imported
        self.active_log = imported.dataframe
        self.active_overview = overview

        # Satu event log aktif dibagikan ke seluruh modul.
        self.panel_117.set_log(self.active_log)
        self.panel_1115.set_log(self.active_log)
        self.panel_1118.set_log(self.active_log)
        self.panel_1122.set_log(self.active_log)

        # Case Explorer global menampilkan seluruh case, bukan hanya case
        # yang lolos salah satu filter exercise.
        self.case_explorer.set_log(self.active_log)
        self.case_explorer.set_cases(self._build_case_register(), {})

        self.file_label.setText(
            f"Loaded dataset: {Path(imported.source_path).name}"
        )

        self.metric_values["TOTAL CASES"].setText(
            f"{overview.total_cases:,}"
        )

        self.metric_values["TOTAL EVENTS"].setText(
            f"{overview.total_events:,}"
        )

        self.metric_values["CYCLE TIME"].setText(
            f"{overview.average_cycle_time_days:.2f} days"
        )

        self.metric_values["ACTIVITIES"].setText(
            str(len(overview.activity_frequency))
        )

        start = overview.start_time.strftime(
            "%d %b %Y, %H:%M UTC"
        )
        end = overview.end_time.strftime(
            "%d %b %Y, %H:%M UTC"
        )

        self.range_label.setText(
            f"{start}   →   {end}"
        )

        self._populate_activity_table(overview)
        self._populate_case_table(overview)

        self.status_label.setText(
            f"Successfully loaded | "
            f"{overview.total_cases:,} cases | "
            f"{overview.total_events:,} events"
        )
        self._refresh_export_cards()

    def _populate_activity_table(self, overview):
        data = overview.activity_frequency.head(10)

        self.activity_table.setRowCount(len(data))

        for row, (_, item) in enumerate(data.iterrows()):
            values = [
                str(item["activity"]),
                f'{int(item["event_count"]):,}',
                f'{int(item["case_count"]):,}'
            ]

            for col, value in enumerate(values):
                self.activity_table.setItem(
                    row, col, QTableWidgetItem(value)
                )

    def _populate_case_table(self, overview):
        data = overview.case_durations.head(10)

        self.case_table.setRowCount(len(data))

        for row, (_, item) in enumerate(data.iterrows()):
            start = item["first_event"].strftime(
                "%d %b %Y"
            )
            end = item["last_event"].strftime(
                "%d %b %Y"
            )

            values = [
                str(item["case_id"]),
                start,
                end,
                f'{item["duration_days"]:.2f}'
            ]

            for col, value in enumerate(values):
                self.case_table.setItem(
                    row, col, QTableWidgetItem(value)
                )

    def _open_overview_case(self, row: int, _column: int):
        """Double-click case di Overview untuk membuka detail di Case Explorer."""
        item = self.case_table.item(row, 0)
        if item is None:
            return
        case_id = item.text()
        self.show_page("cases")
        if not self.case_explorer.select_case(case_id):
            QMessageBox.information(
                self,
                "Case Explorer",
                f"Case {case_id} tidak ditemukan pada dataset aktif.",
            )

    # --------------------------------------------------
    # GLOBAL CASE REGISTER & CSV EXPORT
    # --------------------------------------------------

    def _build_case_register(self) -> pd.DataFrame:
        """Membuat daftar seluruh case dari dataset aktif untuk Case Explorer."""
        if self.active_log is None or self.active_log.empty:
            return pd.DataFrame(
                columns=["Case ID", "Events", "Start", "End", "Duration (days)"]
            )

        grouped = (
            self.active_log.groupby(CASE, sort=False, observed=True)
            .agg(
                Events=(ACT, "size"),
                Start=(TS, "min"),
                End=(TS, "max"),
            )
            .reset_index()
        )
        grouped["Duration (days)"] = (
            grouped["End"] - grouped["Start"]
        ).dt.total_seconds() / 86400

        grouped = grouped.rename(columns={CASE: "Case ID"})
        grouped["Case ID"] = grouped["Case ID"].astype(str)
        grouped["Start"] = grouped["Start"].dt.strftime("%Y-%m-%d %H:%M:%S")
        grouped["End"] = grouped["End"].dt.strftime("%Y-%m-%d %H:%M:%S")
        grouped["Duration (days)"] = grouped["Duration (days)"].round(4)
        return grouped.sort_values("Case ID", kind="mergesort").reset_index(drop=True)

    def _available_export_options(self):
        options = ["Case Register — seluruh case"]
        if self.panel_117.answers:
            options.append("Exercise 11.7 — seluruh butir A–E")
        if self.panel_1115.result is not None:
            options.append("Exercise 11.15 — Repeated Complete")
        if self.panel_1118.result is not None:
            options.append("Exercise 11.18 — Same Resource")
        if self.panel_1122.result is not None:
            options.append("Exercise 11.22 — Ordering Analysis")

        analysis_options = options[1:]
        if len(analysis_options) > 1:
            options.append("Semua hasil analisis — gabungan")
        return options

    @staticmethod
    def _summary_record(summary: dict) -> dict:
        row = {"record_type": "summary"}
        row.update(summary)
        return row

    def _export_frame_for(self, option: str) -> pd.DataFrame:
        """Mengubah hasil modul terpilih menjadi satu tabel CSV yang konsisten."""
        rows = []

        if option == "Case Register — seluruh case":
            register = self._build_case_register()
            if register.empty:
                return register
            return register.rename(columns={
                "Case ID": "case_id",
                "Events": "event_count",
                "Start": "start_time",
                "End": "end_time",
                "Duration (days)": "duration_days",
            })

        include_all = option == "Semua hasil analisis — gabungan"

        if include_all or option.startswith("Exercise 11.7"):
            for answer in self.panel_117.answers:
                summary = {
                    "exercise": "11.7",
                    "item": answer.code,
                    "question": answer.title,
                    "rule": answer.rule,
                    "case_count": answer.count,
                    "mean_cycle_time_days": (
                        round(answer.mean_days, 6)
                        if answer.mean_days is not None else None
                    ),
                }
                rows.append(self._summary_record(summary))
                for case in answer.cases:
                    rows.append({
                        "record_type": "case",
                        "exercise": "11.7",
                        "item": answer.code,
                        "case_id": case.case_id,
                        "duration_days": case.days,
                    })

        if include_all or option.startswith("Exercise 11.15"):
            result = self.panel_1115.result
            if result is not None:
                rows.append(self._summary_record(result.summary_dict()))
                case_df = result.summary_df.rename(columns={
                    CASE: "case_id",
                    "complete_count": "complete_count",
                })
                for record in case_df.to_dict("records"):
                    rows.append({
                        "record_type": "case",
                        "exercise": "11.15",
                        **record,
                    })

        if include_all or option.startswith("Exercise 11.18"):
            result = self.panel_1118.result
            if result is not None:
                rows.append(self._summary_record(result.summary_dict()))
                case_df = result.summary_df.rename(columns={
                    CASE: "case_id",
                    "resource_id": "resource_id",
                    "complete_count": "complete_count",
                })
                for record in case_df.to_dict("records"):
                    rows.append({
                        "record_type": "case",
                        "exercise": "11.18",
                        **record,
                    })

        if include_all or option.startswith("Exercise 11.22"):
            result = self.panel_1122.result
            if result is not None:
                rows.append(self._summary_record(result.summary_dict()))
                ev = result.evidence.copy().rename(columns={
                    CASE: "case_id",
                    "first_pos": "pos_O_Cancelled",
                    "second_pos": "pos_O_Accepted",
                    "first_ts": "ts_O_Cancelled",
                    "second_ts": "ts_O_Accepted",
                })
                if "pos_O_Cancelled" in ev:
                    ev["pos_O_Cancelled"] = ev["pos_O_Cancelled"] + 1
                if "pos_O_Accepted" in ev:
                    ev["pos_O_Accepted"] = ev["pos_O_Accepted"] + 1
                if "ts_O_Cancelled" in ev:
                    ev["ts_O_Cancelled"] = ev["ts_O_Cancelled"].dt.strftime("%Y-%m-%d %H:%M:%S")
                if "ts_O_Accepted" in ev:
                    ev["ts_O_Accepted"] = ev["ts_O_Accepted"].dt.strftime("%Y-%m-%d %H:%M:%S")
                for record in ev.to_dict("records"):
                    rows.append({
                        "record_type": "case",
                        "exercise": "11.22",
                        **record,
                    })

        return pd.DataFrame(rows)

    def _build_export_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.export_feedback = QLabel(
            "Pilih hasil analisis atau Case Register di bawah ini untuk diekspor ke CSV (UTF-8 BOM untuk Microsoft Excel)."
        )
        self.export_feedback.setObjectName("InfoText")
        self.export_feedback.setWordWrap(True)
        layout.addWidget(self.export_feedback)

        specs = [
            ("register", "Case Register — Seluruh Case", "Daftar seluruh case pada dataset aktif beserta jumlah event, waktu mulai/selesai, dan durasi.", "Case Register — seluruh case", "bpic17_case_register.csv"),
            ("11.7", "Exercise 11.7 — Case Count & Cycle Time", "Ringkasan dan daftar case untuk seluruh butir A–E.", "Exercise 11.7 — seluruh butir A–E", "bpic17_exercise_11_7.csv"),
            ("11.15", "Exercise 11.15 — Repeated Complete", "Case dengan aktivitas W_Assess Potential Fraud berstatus complete minimal 2 kali.", "Exercise 11.15 — Repeated Complete", "bpic17_exercise_11_15.csv"),
            ("11.18", "Exercise 11.18 — Same Resource", "Case dengan minimal 2 complete W_Assess Potential Fraud oleh resource yang sama.", "Exercise 11.18 — Same Resource", "bpic17_exercise_11_18.csv"),
            ("11.22", "Exercise 11.22 — Ordering Analysis", "Case dengan urutan O_Cancelled sebelum O_Accepted beserta posisi dan timestamp.", "Exercise 11.22 — Ordering Analysis", "bpic17_exercise_11_22.csv"),
            ("all", "Semua Hasil Analisis (Gabungan)", "Menggabungkan seluruh hasil Exercise yang sudah dijalankan ke dalam satu file CSV.", "Semua hasil analisis — gabungan", "bpic17_semua_hasil_analisis.csv"),
        ]

        for key, title, desc, option_name, default_file in specs:
            card = QFrame()
            card.setObjectName("Card")
            card_lay = QHBoxLayout(card)
            card_lay.setContentsMargins(18, 14, 18, 14)
            card_lay.setSpacing(14)

            text_col = QVBoxLayout()
            text_col.setSpacing(4)
            lbl_title = QLabel(title)
            lbl_title.setObjectName("SectionTitle")
            lbl_desc = QLabel(desc)
            lbl_desc.setObjectName("Muted")
            lbl_desc.setWordWrap(True)
            lbl_status = QLabel("Belum tersedia")
            lbl_status.setObjectName("Muted")

            text_col.addWidget(lbl_title)
            text_col.addWidget(lbl_desc)
            text_col.addWidget(lbl_status)

            btn = QPushButton("Export CSV")
            btn.setObjectName("PrimaryButton")
            btn.setEnabled(False)
            btn.clicked.connect(
                lambda _checked=False, opt=option_name, fn=default_file: self._export_option(opt, fn)
            )

            card_lay.addLayout(text_col, 1)
            card_lay.addWidget(btn)
            layout.addWidget(card)
            self.export_cards[key] = (lbl_status, btn)

        layout.addStretch()
        return page

    def _refresh_export_cards(self):
        if not self.export_cards:
            return
        has_log = self.active_log is not None
        dataset_name = (
            Path(self.active_import.source_path).name
            if self.active_import is not None
            else "—"
        )

        # Register
        reg_lbl, reg_btn = self.export_cards["register"]
        if has_log and self.active_overview is not None:
            reg_lbl.setText(f"Dataset: {dataset_name}  |  {self.active_overview.total_cases:,} case siap diekspor")
            reg_btn.setEnabled(True)
        else:
            reg_lbl.setText("Impor dataset XES terlebih dahulu.")
            reg_btn.setEnabled(False)

        # 11.7
        lbl_117, btn_117 = self.export_cards["11.7"]
        if has_log and self.panel_117.answers:
            total_117 = sum(a.count for a in self.panel_117.answers)
            lbl_117.setText(f"Dataset: {dataset_name}  |  5 butir (A–E) selesai dianalisis ({total_117:,} entri case)")
            btn_117.setEnabled(True)
        else:
            lbl_117.setText("Jalankan analisis Exercise 11.7 terlebih dahulu.")
            btn_117.setEnabled(False)

        # 11.15
        lbl_1115, btn_1115 = self.export_cards["11.15"]
        if has_log and self.panel_1115.result is not None:
            r15 = self.panel_1115.result
            lbl_1115.setText(f"Dataset: {dataset_name}  |  {r15.matched_count:,} dari {r15.total_cases:,} case ({r15.percentage:.2f}%)")
            btn_1115.setEnabled(True)
        else:
            lbl_1115.setText("Jalankan analisis Exercise 11.15 terlebih dahulu.")
            btn_1115.setEnabled(False)

        # 11.18
        lbl_1118, btn_1118 = self.export_cards["11.18"]
        if has_log and self.panel_1118.result is not None:
            r18 = self.panel_1118.result
            lbl_1118.setText(f"Dataset: {dataset_name}  |  {r18.matched_count:,} dari {r18.total_cases:,} case ({r18.percentage:.2f}%)")
            btn_1118.setEnabled(True)
        else:
            lbl_1118.setText("Jalankan analisis Exercise 11.18 terlebih dahulu.")
            btn_1118.setEnabled(False)

        # 11.22
        lbl_1122, btn_1122 = self.export_cards["11.22"]
        if has_log and self.panel_1122.result is not None:
            r22 = self.panel_1122.result
            lbl_1122.setText(f"Dataset: {dataset_name}  |  {r22.matched_count:,} dari {r22.total_cases:,} case ({r22.percentage:.2f}%)")
            btn_1122.setEnabled(True)
        else:
            lbl_1122.setText("Jalankan analisis Exercise 11.22 terlebih dahulu.")
            btn_1122.setEnabled(False)

        # Combined
        ready_count = sum(
            1 for flag in (
                bool(self.panel_117.answers),
                self.panel_1115.result is not None,
                self.panel_1118.result is not None,
                self.panel_1122.result is not None,
            ) if flag
        )
        lbl_all, btn_all = self.export_cards["all"]
        if has_log and ready_count > 1:
            lbl_all.setText(f"Dataset: {dataset_name}  |  {ready_count} modul analisis siap digabung")
            btn_all.setEnabled(True)
        else:
            lbl_all.setText("Jalankan minimal 2 modul analisis untuk mengekspor gabungan.")
            btn_all.setEnabled(False)

    def _export_option(self, option: str, default_name: str):
        if self.active_log is None:
            QMessageBox.information(
                self,
                "Export CSV",
                "Impor dataset XES terlebih dahulu sebelum melakukan ekspor.",
            )
            return
        frame = self._export_frame_for(option)
        if frame.empty:
            QMessageBox.warning(
                self,
                "Export CSV",
                "Belum ada data hasil analisis untuk pilihan tersebut.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan hasil CSV",
            default_name,
            "CSV Files (*.csv)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        try:
            frame.to_csv(file_path, index=False, encoding="utf-8-sig")
        except Exception as exc:
            if hasattr(self, "export_feedback"):
                self.export_feedback.setText(f"Gagal mengekspor CSV: {type(exc).__name__}: {exc}")
            QMessageBox.critical(
                self,
                "Export gagal",
                f"Gagal menyimpan CSV:\n{type(exc).__name__}: {exc}",
            )
            return

        if hasattr(self, "export_feedback"):
            self.export_feedback.setText(
                f"Berhasil diekspor: {file_path} ({len(frame):,} baris)"
            )
        QMessageBox.information(
            self,
            "Export berhasil",
            f"File CSV berhasil disimpan:\n{file_path}\n\nJumlah baris: {len(frame):,}",
        )

    def _active_module_export_target(self):
        """Return (option_name, default_filename, empty_warning) for the active page, or None to prompt."""
        current = self.pages.currentWidget()
        if current is self.page_scrolls.get("11.7"):
            if not self.panel_117.answers:
                return None, "bpic17_exercise_11_7.csv", "Belum ada hasil analisis Exercise 11.7. Jalankan analisis terlebih dahulu."
            return "Exercise 11.7 — seluruh butir A–E", "bpic17_exercise_11_7.csv", None
        if current is self.page_scrolls.get("11.15"):
            if self.panel_1115.export_payload() is None:
                return None, "bpic17_exercise_11_15.csv", "Belum ada hasil analisis Exercise 11.15. Jalankan analisis terlebih dahulu."
            return "Exercise 11.15 — Repeated Complete", "bpic17_exercise_11_15.csv", None
        if current is self.page_scrolls.get("11.18"):
            if self.panel_1118.export_payload() is None:
                return None, "bpic17_exercise_11_18.csv", "Belum ada hasil analisis Exercise 11.18. Jalankan analisis terlebih dahulu."
            return "Exercise 11.18 — Same Resource", "bpic17_exercise_11_18.csv", None
        if current is self.page_scrolls.get("11.22"):
            if self.panel_1122.export_payload() is None:
                return None, "bpic17_exercise_11_22.csv", "Belum ada hasil analisis Exercise 11.22. Jalankan analisis terlebih dahulu."
            return "Exercise 11.22 — Ordering Analysis", "bpic17_exercise_11_22.csv", None
        return None, None, None

    def export_csv(self):
        """Ekspor hasil modul aktif atau pilih dataset/analisis ke CSV."""
        if self.active_log is None:
            QMessageBox.information(
                self,
                "Export CSV",
                "Impor dataset XES terlebih dahulu sebelum melakukan ekspor.",
            )
            return

        selected, default_name, warning_msg = self._active_module_export_target()
        if warning_msg is not None:
            QMessageBox.warning(self, "Export CSV", warning_msg)
            return

        if selected is None:
            options = self._available_export_options()
            if len(options) == 1:
                selected = options[0]
            else:
                selected, accepted = QInputDialog.getItem(
                    self,
                    "Export CSV",
                    "Pilih data yang ingin diekspor:",
                    options,
                    0,
                    False,
                )
                if not accepted:
                    return

        frame = self._export_frame_for(selected)
        if frame.empty:
            QMessageBox.warning(
                self,
                "Export CSV",
                "Belum ada data hasil analisis untuk pilihan tersebut.",
            )
            return

        if not default_name:
            suggested = selected.lower().replace(" ", "_").replace("—", "-")
            suggested = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in suggested)
            default_name = f"{suggested}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan hasil CSV",
            default_name,
            "CSV Files (*.csv)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        try:
            frame.to_csv(file_path, index=False, encoding="utf-8-sig")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export gagal",
                f"Gagal menyimpan CSV:\\n{type(exc).__name__}: {exc}",
            )
            return

        QMessageBox.information(
            self,
            "Export berhasil",
            f"File CSV berhasil disimpan:\\n{file_path}\\n\\nJumlah baris: {len(frame):,}",
        )

    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------

    def _on_failed(self, error):
        self.status_label.setText("Dataset import failed.")

        QMessageBox.critical(
            self,
            "Import Error",
            error
        )

    def _on_worker_finished(self):
        self.progress.hide()
        self.import_button.setEnabled(True)
        self.worker = None

    def closeEvent(self, event):
        import_running = self.worker and self.worker.isRunning()

        analysis_worker = getattr(self.panel_1122, "_worker", None)
        analysis_running = (
            analysis_worker is not None and analysis_worker.isRunning()
        )

        worker_117 = getattr(self.panel_117, "_worker", None)
        analysis_117_running = (
            worker_117 is not None and worker_117.isRunning()
        )
        worker_1115 = getattr(self.panel_1115, "_worker", None)
        analysis_1115_running = (
            worker_1115 is not None and worker_1115.isRunning()
        )
        worker_1118 = getattr(self.panel_1118, "_worker", None)
        analysis_1118_running = (
            worker_1118 is not None and worker_1118.isRunning()
        )

        if (import_running or analysis_running or analysis_117_running
                or analysis_1115_running or analysis_1118_running):
            QMessageBox.warning(
                self,
                "Processing",
                "Tunggu proses import atau analisis selesai sebelum menutup aplikasi."
            )
            event.ignore()
        else:
            event.accept()

    # --------------------------------------------------
    # STYLING
    # --------------------------------------------------

    def _apply_style(self):
        self.setStyleSheet(build_stylesheet())
