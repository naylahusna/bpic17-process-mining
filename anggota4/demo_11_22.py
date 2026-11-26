"""Tes panel sendiri tanpa menunggu GUI Anggota 1:
    python demo_11_22.py ..\\data\\BPIC17.xes.gz

Kalau pm4py tidak bisa di-import (mis. scipy diblokir kebijakan laptop),
otomatis pakai parser XES cadangan HANYA untuk pengujian lokal.
Aplikasi final tim tetap wajib memakai PM4Py (jalankan di laptop yang tidak diblokir).
"""
import gzip
import sys
import xml.etree.ElementTree as ET

import pandas as pd
from PySide6.QtWidgets import QApplication, QFileDialog

from .columns import ACT, CASE, LIFE, RES, TS
from panel_11_22 import Panel1122


def load_xes_fallback(path: str) -> pd.DataFrame:
    keys = {ACT, TS, LIFE, RES}
    opener = gzip.open if str(path).endswith(".gz") else open
    rows, buf = [], []
    with opener(path, "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            tag = el.tag.rsplit("}", 1)[-1]
            if tag == "event":
                buf.append({c.get("key"): c.get("value") for c in el if c.get("key") in keys})
            elif tag == "trace":
                cid = None
                for c in el:
                    if c.tag.rsplit("}", 1)[-1] != "event" and c.get("key") == ACT:
                        cid = c.get("value")
                for d in buf:
                    d[CASE] = cid
                rows.extend(buf)
                buf = []
                el.clear()
    df = pd.DataFrame(rows)
    for c in (CASE, ACT, TS, LIFE, RES):
        if c not in df.columns:
            df[c] = None
    df[TS] = pd.to_datetime(df[TS], utc=True)
    return df


def load_log(path: str) -> pd.DataFrame:
    try:
        import pm4py
        log = pm4py.read_xes(path)
        print("Dibaca dengan PM4Py.")
        return log if isinstance(log, pd.DataFrame) else pm4py.convert_to_dataframe(log)
    except (ImportError, OSError) as e:
        print(f"PM4Py tidak bisa dipakai di mesin ini ({e}). Pakai parser cadangan (hanya untuk tes).")
        return load_xes_fallback(path)


app = QApplication(sys.argv)
path = sys.argv[1] if len(sys.argv) > 1 else QFileDialog.getOpenFileName(None, "Pilih XES", "", "XES (*.xes *.gz)")[0]
df = load_log(path)
print(f"Terbaca: {df[CASE].nunique():,} case, {len(df):,} event")
panel = Panel1122()
panel.resize(1100, 800)
panel.set_log(df)
panel.show()
sys.exit(app.exec())
