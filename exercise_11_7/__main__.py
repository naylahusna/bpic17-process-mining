import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Pratinjau mandiri Exercise 11.7 A–E dengan file XES lokal.")
    parser.add_argument("xes", type=Path, help="Jalur file .xes atau .xes.gz")
    parser.add_argument("--gui", action="store_true", help="Tampilkan panel latihan di jendela uji.")
    args = parser.parse_args()
    if not args.xes.is_file() or not args.xes.name.lower().endswith((".xes", ".xes.gz")):
        parser.error("Berikan jalur file .xes atau .xes.gz yang tersedia.")

    try:
        from pm4py import convert_to_dataframe
        from pm4py.objects.log.importer.xes import importer
    except ImportError:
        parser.exit(1, "PM4Py belum tersedia. Instal dengan python -m pip install pm4py==2.7.17.\n")

    from .analysis import TIMESTAMP, analyze_dataframe

    print(f"Membaca {args.xes.name} untuk pengujian 11.7…", flush=True)
    try:
        event_log = importer.apply(str(args.xes), parameters={"show_progress_bar": False, "timestamp_sort": False})
        log = convert_to_dataframe(event_log)
        del event_log
    except Exception as exc:
        parser.exit(1, f"Pratinjau gagal membaca XES: {exc}\n")

    # Urutan ini hanya untuk pratinjau mandiri. Aplikasi kelompok memasok prepare_log.
    def prepare_preview(df):
        return df.sort_values(TIMESTAMP, kind="stable")

    if args.gui:
        import tkinter as tk

        from .panel import Exercise117Panel

        window = tk.Tk()
        window.title(f"Pratinjau 11.7 | {args.xes.name}")
        window.geometry("820x640")
        window.minsize(720, 570)
        case_id = tk.StringVar(value="Pilih case untuk menguji pengiriman ID ke Case Explorer.")
        tk.Label(window, textvariable=case_id, anchor="w", padx=14).pack(side="bottom", fill="x", pady=8)
        panel = Exercise117Panel(
            window, lambda value: case_id.set(f"Case ID yang dikirim: {value}"),
            prepare_log=prepare_preview,
        )
        panel.pack(fill="both", expand=True)
        panel.set_log(log)
        window.mainloop()
        return

    try:
        answers = analyze_dataframe(log, prepare_preview)
    except ValueError as exc:
        parser.exit(1, f"Analisis gagal: {exc}\n")

    for answer in answers:
        parts = []
        if answer.code != "B":
            parts.append(f"{answer.count} case")
        if answer.code != "A":
            mean = answer.mean_days
            parts.append(f"{mean:.3f} hari" if mean is not None else "durasi tidak tersedia")
        print(f"11.7 {answer.code} | {answer.title} | {' · '.join(parts)}")


if __name__ == "__main__":
    main()
