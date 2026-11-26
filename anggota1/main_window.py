from pathlib import Path
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QMessageBox,
    QProgressBar, QStackedWidget
)

from anggota1.importer import load_xes
from anggota1.overview import build_overview
from anggota4.panel_11_22 import Panel1122
from exercise_11_7.panel_qt import Panel117


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

        case_card = self._build_table_card(
            "LONGEST CASE DURATIONS",
            ["Case ID", "Start", "End", "Days"]
        )
        self.case_table = case_card.findChild(
            QTableWidget, "DataTable"
        )

        tables_layout.addWidget(activity_card, 1)
        tables_layout.addWidget(case_card, 1)
        overview_layout.addLayout(tables_layout, 1)

        self.status_label = QLabel(
            "Ready | Import a BPIC17 XES event log to begin."
        )
        self.status_label.setObjectName("Muted")
        overview_layout.addWidget(self.status_label)

        self.pages.addWidget(self.overview_page)

        # PAGE 2: EXERCISE 11.7 (NAYLA, PySide6 adapter)
        self.panel_117 = Panel117()
        self.pages.addWidget(self.panel_117)

        # PAGE 3: EXERCISE 11.22 (GALANG)
        self.panel_1122 = Panel1122()
        self.panel_1122.btn_run.setObjectName("PrimaryButton")
        self.panel_1122.btn_reset.setObjectName("SecondaryButton")
        self.pages.addWidget(self.panel_1122)

        self.pages.setCurrentWidget(self.overview_page)
        content_layout.addWidget(self.pages, 1)

        root.addWidget(content, 1)

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
        self._add_nav(layout, "Exercise 11.15", False)
        self._add_nav(layout, "Exercise 11.18", False)
        self._add_nav(
            layout, "Exercise 11.22", True, False,
            lambda: self.show_page("11.22")
        )

        layout.addSpacing(15)

        tools_section = QLabel("TOOLS")
        tools_section.setObjectName("SidebarSection")
        layout.addWidget(tools_section)

        self._add_nav(layout, "Case Explorer", False)
        self._add_nav(layout, "Export CSV", False)

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
        if page == "overview":
            self.pages.setCurrentWidget(self.overview_page)
            self.page_title.setText("Overview Dashboard")
            self.page_subtitle.setText(
                "Business Process Intelligence | BPI Challenge 2017"
            )
            selected = "Overview"

        elif page == "11.7":
            self.pages.setCurrentWidget(self.panel_117)
            self.page_title.setText("Exercise 11.7")
            self.page_subtitle.setText(
                "Case Analysis | Case Count and Cycle Time"
            )
            selected = "Exercise 11.7"

        elif page == "11.22":
            self.pages.setCurrentWidget(self.panel_1122)
            self.page_title.setText("Exercise 11.22")
            self.page_subtitle.setText(
                "Ordering Analysis | O_Cancelled before O_Accepted"
            )
            selected = "Exercise 11.22"

        else:
            return

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

        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        table.setMinimumHeight(270)

        layout.addWidget(table)

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

        # Teruskan DataFrame aktif ke panel Exercise 11.22.
        self.panel_117.set_log(self.active_log)
        self.panel_1122.set_log(self.active_log)

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

        if import_running or analysis_running or analysis_117_running:
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
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F4F7FB;
                color: #17243A;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QLabel {
                background-color: transparent;
                color: #17243A;
            }

            QFrame#Sidebar {
                background-color: #142238;
                border: none;
            }

            QLabel#Brand {
                background-color: transparent;
                color: #FFFFFF;
                font-size: 16pt;
                font-weight: 800;
                padding: 2px 0;
            }

            QLabel#BrandSubtitle {
                background-color: transparent;
                color: #8FA8C5;
                font-size: 8pt;
                font-weight: 600;
                letter-spacing: 2px;
            }

            QLabel#SidebarSection {
                background-color: transparent;
                color: #8FA8C5;
                font-size: 8pt;
                font-weight: 700;
                padding: 8px 4px 5px 4px;
            }

            QLabel#SidebarFooter {
                background-color: transparent;
                color: #8298B3;
                font-size: 8pt;
                padding-top: 12px;
            }

            QPushButton {
                background-color: #E7EDF5;
                color: #263A52;
                border: 1px solid #D4DEEA;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
                min-height: 18px;
            }

            QPushButton:hover:enabled {
                background-color: #DCE7F3;
                border-color: #B8C9DC;
            }

            QPushButton:pressed:enabled {
                background-color: #CFDDED;
            }

            QPushButton:disabled {
                background-color: #E9EDF2;
                color: #9AA8B8;
                border-color: #E1E6EC;
            }

            QPushButton#NavButton {
                background-color: transparent;
                color: #C7D3E2;
                border: 1px solid transparent;
                border-radius: 7px;
                text-align: left;
                padding: 10px 12px;
                font-weight: 500;
            }

            QPushButton#NavButton:checked {
                background-color: #2D5B89;
                color: #FFFFFF;
                border: 1px solid #416F9D;
                font-weight: 700;
            }

            QPushButton#NavButton:hover:enabled:!checked {
                background-color: #21364F;
                color: #FFFFFF;
            }

            QPushButton#NavButton:disabled {
                background-color: transparent;
                color: #71849D;
                border-color: transparent;
            }

            QPushButton#PrimaryButton {
                background-color: #2867B2;
                color: #FFFFFF;
                border: 1px solid #2867B2;
                border-radius: 8px;
                padding: 11px 19px;
                font-weight: 700;
            }

            QPushButton#PrimaryButton:hover:enabled {
                background-color: #1F5596;
                border-color: #1F5596;
            }

            QPushButton#PrimaryButton:pressed:enabled {
                background-color: #19477E;
            }

            QPushButton#PrimaryButton:disabled {
                background-color: #A9BDD3;
                color: #F5F8FC;
                border-color: #A9BDD3;
            }

            QPushButton#SecondaryButton {
                background-color: #FFFFFF;
                color: #2B4B6C;
                border: 1px solid #C9D6E4;
            }

            QPushButton#SecondaryButton:hover:enabled {
                background-color: #EEF4FA;
                border-color: #9FB5CC;
            }

            QLabel#PageTitle {
                background-color: transparent;
                color: #17243A;
                font-size: 23pt;
                font-weight: 800;
            }

            QLabel#Muted {
                background-color: transparent;
                color: #74839A;
                font-size: 9pt;
            }

            QLabel#FileInfo {
                background-color: #E6EDF6;
                color: #36577F;
                border: 1px solid #D9E4F0;
                border-radius: 8px;
                padding: 10px 12px;
            }

            QFrame#MetricCard, QFrame#Card {
                background-color: #FFFFFF;
                border: 1px solid #E1E8F0;
                border-radius: 10px;
            }

            QLabel#MetricTitle {
                background-color: transparent;
                color: #74839A;
                font-size: 9pt;
                font-weight: 700;
            }

            QLabel#MetricValue {
                background-color: transparent;
                color: #17243A;
                font-size: 22pt;
                font-weight: 800;
            }

            QLabel#SectionTitle {
                background-color: transparent;
                color: #34465F;
                font-size: 10pt;
                font-weight: 700;
            }

            QLabel#RangeValue {
                background-color: transparent;
                color: #2867B2;
                font-size: 12pt;
                font-weight: 700;
            }

            QLabel#InfoText {
                background-color: #EEF4FA;
                color: #334B66;
                border: 1px solid #DCE6F0;
                border-radius: 8px;
                padding: 10px;
            }

            QLineEdit {
                background-color: #FFFFFF;
                color: #17243A;
                border: 1px solid #CFD9E5;
                border-radius: 8px;
                padding: 9px 11px;
                selection-background-color: #2867B2;
                selection-color: #FFFFFF;
            }

            QLineEdit:focus {
                border: 1px solid #2867B2;
            }

            QTableWidget#DataTable, QTableView {
                background-color: #FFFFFF;
                alternate-background-color: #F6F9FC;
                color: #263A52;
                border: 1px solid #E1E8F0;
                border-radius: 7px;
                gridline-color: #E8EDF3;
                selection-background-color: #DCEAFE;
                selection-color: #17243A;
                outline: 0;
            }

            QTableWidget#DataTable::item, QTableView::item {
                padding: 6px;
            }

            QHeaderView::section {
                background-color: #EDF2F7;
                color: #435873;
                padding: 9px 7px;
                border: none;
                border-bottom: 1px solid #DCE4ED;
                font-weight: 700;
            }

            QProgressBar {
                background-color: #E0E8F2;
                color: #24415F;
                border: 1px solid #D4DFEA;
                border-radius: 5px;
                text-align: center;
                min-height: 12px;
                max-height: 18px;
            }

            QProgressBar::chunk {
                background-color: #2867B2;
                border-radius: 4px;
            }

            QScrollBar:vertical {
                background: #F1F4F8;
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #B7C5D5;
                min-height: 25px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #8FA5BD;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background: #F1F4F8;
                height: 10px;
                margin: 2px;
                border-radius: 5px;
            }

            QScrollBar::handle:horizontal {
                background: #B7C5D5;
                min-width: 25px;
                border-radius: 5px;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)
