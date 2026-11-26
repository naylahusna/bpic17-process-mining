"""Definisi nama kolom standar DataFrame Event Log BPIC17.
Kompatibel dengan modul Anggota 1, Anggota 2, dan Anggota 4.
"""
CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
LIFE = "lifecycle:transition"
RES = "org:resource"
POS = "_pos"      # Posisi event dalam trace (0-based)
ORIG = "_orig"    # Indeks baris asli di file XES
