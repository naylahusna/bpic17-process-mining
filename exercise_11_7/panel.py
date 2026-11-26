from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from pandas import DataFrame

from .analysis import CASE_ID, Answer, analyze_dataframe

PAGE_SIZE = 100


class Exercise117Panel(ttk.Frame):
    """Panel 11.7 yang menerima log aktif dari aplikasi induk."""

    def __init__(self, master, on_open_case: Callable[[str], None], *, prepare_log: Callable[[DataFrame], DataFrame]):
        super().__init__(master, padding=14)
        self.on_open_case = on_open_case
        self.prepare_log = prepare_log
        self.log: DataFrame | None = None
        self.answers: tuple[Answer, ...] = ()
        self.page = 0
        self.query = tk.StringVar()
        self.status = tk.StringVar(value="Muat log aktif untuk memulai.")
        ttk.Label(self, text="Exercise 11.7 · Case dan cycle time", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=8)
        self.run = ttk.Button(actions, text="Jalankan analisis", command=self._run, state="disabled")
        self.run.pack(side="left")
        ttk.Button(actions, text="Reset hasil", command=self._reset).pack(side="left", padx=6)
        ttk.Label(actions, textvariable=self.status).pack(side="left", padx=6)

        self.summary = self._table(self, ("Butir", "Jawaban", "Jumlah case", "Rata-rata (hari)"), (55, 305, 120, 145), 5)
        self.summary.bind("<<TreeviewSelect>>", self._select_answer)
        self.rule = tk.StringVar(value="Pilih baris A–E untuk melihat daftar case.")
        ttk.Label(self, textvariable=self.rule, wraplength=720).pack(fill="x", pady=(10, 6))

        search = ttk.Frame(self)
        search.pack(fill="x", pady=(0, 6))
        ttk.Label(search, text="Cari case ID").pack(side="left")
        field = ttk.Entry(search, textvariable=self.query, width=24)
        field.pack(side="left", padx=6)
        field.bind("<Return>", self._apply_search)
        ttk.Button(search, text="Cari", command=self._apply_search).pack(side="left")

        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", pady=(8, 0))
        self.page_label = tk.StringVar(value="0 case")
        ttk.Label(footer, textvariable=self.page_label).pack(side="left")
        self.open_button = ttk.Button(footer, text="Lihat rincian case", command=self._open_selected, state="disabled")
        self.open_button.pack(side="right")
        self.next_button = ttk.Button(footer, text="Berikutnya", command=lambda: self._turn(1), state="disabled")
        self.next_button.pack(side="right", padx=6)
        self.prev_button = ttk.Button(footer, text="Sebelumnya", command=lambda: self._turn(-1), state="disabled")
        self.prev_button.pack(side="right")
        self.cases = self._table(self, ("Case ID", "Durasi (hari)"), (400, 180), 9, expand=True)
        self.cases.bind("<<TreeviewSelect>>", self._sync_open_button)
        self.cases.bind("<Double-1>", lambda _: self._open_selected())

    @staticmethod
    def _table(parent, headings, widths, height, expand=False):
        frame = ttk.Frame(parent)
        frame.pack(fill="both" if expand else "x", expand=expand)
        table = ttk.Treeview(frame, columns=headings, show="headings", selectmode="browse", height=height)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        table.pack(fill="both", expand=True)
        for heading, width in zip(headings, widths):
            table.heading(heading, text=heading)
            table.column(heading, width=width)
        return table

    def set_log(self, log: DataFrame):
        """Terima DataFrame log aktif dari aplikasi induk dan reset hasil dataset lama."""
        self.log = log
        self.run.configure(state="normal")
        self._reset()

    def _reset(self):
        self.answers = ()
        self.summary.delete(*self.summary.get_children())
        self.query.set("")
        self.page = 0
        self.status.set("Siap dianalisis." if self.log is not None else "Muat log aktif untuk memulai.")
        self._render_cases()

    def _run(self):
        if self.log is None:
            return
        self._reset()
        try:
            self.answers = analyze_dataframe(self.log, self.prepare_log)
        except ValueError as exc:
            self.status.set(str(exc))
            return

        for answer in self.answers:
            mean = answer.mean_days
            self.summary.insert("", "end", iid=answer.code, values=(
                answer.code, answer.title, answer.count if answer.code != "B" else "—",
                f"{mean:.3f}" if answer.code != "A" and mean is not None else "—",
            ))
        self.status.set("Analisis selesai.")
        self.summary.selection_set("A")
        self._select_answer()

    def selected_answer(self) -> Answer | None:
        """Hasil aktif untuk dibaca oleh aplikasi induk."""
        selection = self.summary.selection()
        if selection:
            return next(answer for answer in self.answers if answer.code == selection[0])
        return None

    def export_payload(self) -> tuple[dict, DataFrame]:
        """Kembalikan ringkasan dan seluruh case untuk butir yang dipilih."""
        answer = self.selected_answer()
        if answer is None:
            return {}, DataFrame(columns=[CASE_ID, "cycle_time_days"])
        summary = {
            "exercise": "11.7",
            "question": answer.code,
            "rule": answer.rule,
            "case_count": answer.count,
            "mean_cycle_time_days": answer.mean_days,
        }
        cases = DataFrame.from_records(
            ((case.case_id, case.days) for case in answer.cases),
            columns=[CASE_ID, "cycle_time_days"],
        )
        return summary, cases


    def _select_answer(self, _event=None):
        self.query.set("")
        self._apply_search()

    def _apply_search(self, _event=None):
        self.page = 0
        self._render_cases()

    def _turn(self, step):
        self.page += step
        self._render_cases()

    def _render_cases(self):
        self.cases.delete(*self.cases.get_children())
        answer = self.selected_answer()
        self.rule.set(answer.rule if answer else "Pilih baris A–E untuk melihat daftar case.")
        query = self.query.get().strip().casefold()
        matches = [case for case in answer.cases if query in case.case_id.casefold()] if answer else []
        start = self.page * PAGE_SIZE
        end = min(start + PAGE_SIZE, len(matches))
        for case in matches[start:end]:
            self.cases.insert("", "end", iid=case.case_id, values=(case.case_id, f"{case.days:.3f}"))
        self.cases.yview_moveto(0)
        self.page_label.set(f"{start + 1}–{end} dari {len(matches)} case" if end else "0 case")
        self.prev_button.configure(state="normal" if start else "disabled")
        self.next_button.configure(state="normal" if end < len(matches) else "disabled")
        self._sync_open_button()

    def _sync_open_button(self, _event=None):
        self.open_button.configure(state="normal" if self.cases.selection() else "disabled")

    def _open_selected(self):
        selection = self.cases.selection()
        if selection:
            self.on_open_case(selection[0])
