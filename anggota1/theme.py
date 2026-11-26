"""Centralized Ivory Burgundy theme and table UX helpers for BPIC17 Process Mining."""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QSizePolicy, QTableView, QTableWidget

# Core Ivory Burgundy palette
IVORY = "#F8F5F0"
WARM_BEIGE = "#EDE6DD"
DEEP_CHARCOAL = "#1B1416"
BURGUNDY = "#6E1F2F"
WARM_GRAY = "#9A8F89"

# Derived harmonious tones
WARM_WHITE = "#FDFBF8"
BORDER_WARM = "#DDD3C8"
BORDER_SUBTLE = "#E6DDD3"
BEIGE_HOVER = "#E3D9CD"
BEIGE_PRESSED = "#D8CCC0"
BURGUNDY_HOVER = "#571724"
BURGUNDY_PRESSED = "#44111B"
BURGUNDY_NAV_HOVER = "#4E1B26"
BURGUNDY_SELECTED_ROW = "#F2E1E4"
BURGUNDY_EVIDENCE_BG = QColor("#F3DCE0")
BURGUNDY_EVIDENCE_FG = QColor("#4A121D")

TIMELINE_PALETTE = [
    QColor("#6E1F2F"),  # Burgundy
    QColor("#9A5B25"),  # Warm amber/bronze
    QColor("#4E3548"),  # Deep plum
    QColor("#2F5A4F"),  # Muted sage-forest
]

ROW_HEIGHT = 40
HEADER_HEIGHT = 44


def configure_table(
    table: QTableView | QTableWidget,
    *,
    min_rows: int = 5,
    row_height: int = ROW_HEIGHT,
    header_height: int = HEADER_HEIGHT,
    resize_mode: QHeaderView.ResizeMode = QHeaderView.ResizeMode.Stretch,
) -> None:
    """Apply consistent row height, header height, minimum visible rows, and sizing policy."""
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.setShowGrid(True)

    v_header = table.verticalHeader()
    v_header.setVisible(False)
    v_header.setDefaultSectionSize(row_height)
    v_header.setMinimumSectionSize(row_height)

    h_header = table.horizontalHeader()
    h_header.setMinimumHeight(header_height)
    h_header.setDefaultAlignment(
        h_header.defaultAlignment()
    )
    h_header.setSectionResizeMode(resize_mode)
    h_header.setStretchLastSection(False)

    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    if min_rows > 0:
        table.setMinimumHeight(header_height + min_rows * row_height + 6)


def fit_table_height(
    table: QTableView | QTableWidget,
    row_count: int,
    *,
    min_rows: int = 5,
    max_rows: int = 7,
    row_height: int = ROW_HEIGHT,
    header_height: int = HEADER_HEIGHT,
) -> None:
    """Adjust table height cleanly to row_count (exact for small results, scrollable for large)."""
    if row_count <= 0:
        visible_rows = 3
    elif row_count < min_rows:
        visible_rows = row_count
    else:
        visible_rows = min(row_count, max_rows)

    target_h = header_height + visible_rows * row_height + 6
    table.setMinimumHeight(target_h)
    if row_count <= max_rows:
        table.setMaximumHeight(target_h)
    else:
        table.setMaximumHeight(16777215)


def build_stylesheet() -> str:
    """Return the centralized Ivory Burgundy QSS stylesheet for the entire application."""
    return f"""
        QMainWindow, QWidget {{
            background-color: {IVORY};
            color: {DEEP_CHARCOAL};
            font-family: "Segoe UI", sans-serif;
            font-size: 10pt;
        }}

        QDialog {{
            background-color: {IVORY};
            color: {DEEP_CHARCOAL};
        }}

        QLabel {{
            background-color: transparent;
            color: {DEEP_CHARCOAL};
        }}

        /* ---------------- SIDEBAR ---------------- */
        QFrame#Sidebar {{
            background-color: {DEEP_CHARCOAL};
            border: none;
        }}

        QLabel#Brand {{
            background-color: transparent;
            color: {IVORY};
            font-size: 16pt;
            font-weight: 800;
            padding: 2px 0;
        }}

        QLabel#BrandSubtitle {{
            background-color: transparent;
            color: {WARM_GRAY};
            font-size: 8pt;
            font-weight: 600;
            letter-spacing: 2px;
        }}

        QLabel#SidebarSection {{
            background-color: transparent;
            color: {WARM_GRAY};
            font-size: 8pt;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 10px 4px 4px 4px;
        }}

        QLabel#SidebarFooter {{
            background-color: transparent;
            color: {WARM_GRAY};
            font-size: 8pt;
            padding-top: 12px;
        }}

        QPushButton#NavButton {{
            background-color: transparent;
            color: rgba(248, 245, 240, 0.78);
            border: 1px solid transparent;
            border-radius: 8px;
            text-align: left;
            padding: 10px 12px;
            font-weight: 500;
        }}

        QPushButton#NavButton:checked {{
            background-color: {BURGUNDY};
            color: {IVORY};
            border: 1px solid {BURGUNDY};
            font-weight: 700;
        }}

        QPushButton#NavButton:hover:enabled:!checked {{
            background-color: {BURGUNDY_NAV_HOVER};
            color: {IVORY};
        }}

        QPushButton#NavButton:disabled {{
            background-color: transparent;
            color: rgba(154, 143, 137, 0.55);
            border-color: transparent;
        }}

        /* ---------------- BUTTONS ---------------- */
        QPushButton {{
            background-color: {WARM_BEIGE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 9px;
            padding: 8px 16px;
            font-weight: 600;
            min-height: 20px;
        }}

        QPushButton:hover:enabled {{
            background-color: {BEIGE_HOVER};
            border-color: {WARM_GRAY};
        }}

        QPushButton:pressed:enabled {{
            background-color: {BEIGE_PRESSED};
        }}

        QPushButton:disabled {{
            background-color: #E8E2DA;
            color: {WARM_GRAY};
            border-color: {BORDER_SUBTLE};
        }}

        QPushButton#PrimaryButton {{
            background-color: {BURGUNDY};
            color: {IVORY};
            border: 1px solid {BURGUNDY};
            border-radius: 9px;
            padding: 9px 18px;
            font-weight: 700;
        }}

        QPushButton#PrimaryButton:hover:enabled {{
            background-color: {BURGUNDY_HOVER};
            border-color: {BURGUNDY_HOVER};
        }}

        QPushButton#PrimaryButton:pressed:enabled {{
            background-color: {BURGUNDY_PRESSED};
        }}

        QPushButton#PrimaryButton:disabled {{
            background-color: {WARM_GRAY};
            color: {IVORY};
            border-color: {WARM_GRAY};
        }}

        QPushButton#SecondaryButton {{
            background-color: {WARM_BEIGE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 9px;
            padding: 8px 16px;
            font-weight: 600;
        }}

        QPushButton#SecondaryButton:hover:enabled {{
            background-color: {BEIGE_HOVER};
            border-color: {WARM_GRAY};
        }}

        QPushButton#SecondaryButton:pressed:enabled {{
            background-color: {BEIGE_PRESSED};
        }}

        QPushButton#SecondaryButton:disabled {{
            background-color: #EFEAE3;
            color: {WARM_GRAY};
            border-color: {BORDER_SUBTLE};
        }}

        /* ---------------- TYPOGRAPHY & HEADERS ---------------- */
        QLabel#PageTitle {{
            background-color: transparent;
            color: {DEEP_CHARCOAL};
            font-size: 22pt;
            font-weight: 800;
        }}

        QLabel#Muted {{
            background-color: transparent;
            color: {WARM_GRAY};
            font-size: 9pt;
        }}

        QLabel#FileInfo {{
            background-color: {WARM_BEIGE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 500;
        }}

        QLabel#MetricTitle {{
            background-color: transparent;
            color: {WARM_GRAY};
            font-size: 8.5pt;
            font-weight: 700;
            letter-spacing: 0.8px;
        }}

        QLabel#MetricValue {{
            background-color: transparent;
            color: {DEEP_CHARCOAL};
            font-size: 21pt;
            font-weight: 800;
        }}

        QLabel#SectionTitle {{
            background-color: transparent;
            color: {DEEP_CHARCOAL};
            font-size: 10.5pt;
            font-weight: 700;
            letter-spacing: 0.4px;
        }}

        QLabel#RangeValue {{
            background-color: transparent;
            color: {BURGUNDY};
            font-size: 11.5pt;
            font-weight: 700;
        }}

        QLabel#AnswerBanner {{
            background-color: transparent;
            color: {BURGUNDY};
            font-size: 12pt;
            font-weight: 700;
            padding: 2px 0;
        }}

        QLabel#InfoText, QFrame#InfoCard {{
            background-color: {WARM_BEIGE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 10px;
            padding: 10px 14px;
        }}

        /* ---------------- CARDS ---------------- */
        QFrame#MetricCard, QFrame#Card {{
            background-color: {WARM_WHITE};
            border: 1px solid {BORDER_WARM};
            border-radius: 12px;
        }}

        QFrame#EmptyState {{
            background-color: {IVORY};
            border: 1px dashed {BORDER_WARM};
            border-radius: 10px;
        }}

        QLabel#EmptyTitle {{
            background-color: transparent;
            color: {DEEP_CHARCOAL};
            font-size: 11.5pt;
            font-weight: 700;
        }}

        QLabel#EmptyDesc {{
            background-color: transparent;
            color: {WARM_GRAY};
            font-size: 9.5pt;
        }}

        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}

        /* ---------------- INPUTS ---------------- */
        QLineEdit {{
            background-color: {WARM_WHITE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 8px;
            padding: 8px 12px;
            selection-background-color: {BURGUNDY};
            selection-color: {IVORY};
        }}

        QLineEdit:focus {{
            border: 1.5px solid {BURGUNDY};
        }}

        /* ---------------- TABLES ---------------- */
        QTableWidget, QTableView {{
            background-color: {IVORY};
            alternate-background-color: {WARM_WHITE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 10px;
            gridline-color: {BORDER_SUBTLE};
            selection-background-color: {BURGUNDY_SELECTED_ROW};
            selection-color: {DEEP_CHARCOAL};
            outline: 0;
        }}

        QTableWidget::item, QTableView::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {BORDER_SUBTLE};
        }}

        QTableWidget::item:hover, QTableView::item:hover {{
            background-color: {WARM_BEIGE};
        }}

        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {BURGUNDY_SELECTED_ROW};
            color: {DEEP_CHARCOAL};
        }}

        QHeaderView::section {{
            background-color: {WARM_BEIGE};
            color: {DEEP_CHARCOAL};
            padding: 10px 10px;
            border: none;
            border-bottom: 1px solid {BORDER_WARM};
            border-right: 1px solid {BORDER_SUBTLE};
            font-weight: 700;
        }}

        QHeaderView::section:last {{
            border-right: none;
        }}

        /* ---------------- SPLITTER ---------------- */
        QSplitter::handle {{
            background-color: {BORDER_WARM};
            height: 4px;
            margin: 4px 0;
            border-radius: 2px;
        }}

        QSplitter::handle:hover {{
            background-color: {BURGUNDY};
        }}

        /* ---------------- PROGRESS BAR ---------------- */
        QProgressBar {{
            background-color: {WARM_BEIGE};
            color: {DEEP_CHARCOAL};
            border: 1px solid {BORDER_WARM};
            border-radius: 6px;
            text-align: center;
            min-height: 12px;
            max-height: 16px;
        }}

        QProgressBar::chunk {{
            background-color: {BURGUNDY};
            border-radius: 5px;
        }}

        /* ---------------- SCROLLBARS ---------------- */
        QScrollBar:vertical {{
            background: {WARM_BEIGE};
            width: 12px;
            margin: 2px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background: {WARM_GRAY};
            min-height: 36px;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {BURGUNDY};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background: {WARM_BEIGE};
            height: 12px;
            margin: 2px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background: {WARM_GRAY};
            min-width: 36px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {BURGUNDY};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """
