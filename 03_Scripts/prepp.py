import os
import sqlite3
import pandas as pd

BASE_DIR = r"C:\Users\frank\Desktop\Arbeidsflytmodell for Helse og Mestring"
PROC_DIR = os.path.join(BASE_DIR, "02_Data_Processed")
SQLITE_DB = os.path.join(PROC_DIR, "helse_mestring_sqlite.db")

conn = sqlite3.connect(SQLITE_DB)

print("🧹 Vasker og klargjør 'stg_bomiljo' ➔ 'fact_bomiljo'...\n")

# 1. Les rådatatabellen
df = pd.read_sql_query("SELECT * FROM stg_bomiljo", conn)

# Hjjelpefunksjon for å finne kolonnenavn uavhengig av tegnvask
def finn_col(df, kandidater):
    for cand in kandidater:
        for col in df.columns:
            if cand in col.lower():
                return col
    return None

art_col = finn_col(df, ['kostra_art', 'art'])
periode_col = finn_col(df, ['periode'])
ansvar_col = finn_col(df, ['ansvar', 'enhet'])
regnskap_col = finn_col(df, ['regnskap_hia', 'regnskap'])
budsjett_col = finn_col(df, ['budsjett_hia', 'budsjett'])
avvik_col = finn_col(df, ['avvik_i_kr', 'avvik'])
arsbudsjett_col = finn_col(df, ['arsbudsjett'])
fjor_col = finn_col(df, ['fjor'])

print(f"📌 Identifiserte nøkkelkolonner:")
print(f"   • Art/Kostra-art: '{art_col}'")
print(f"   • Regnskap YTD:   '{regnskap_col}'")
print(f"   • Budsjett YTD:   '{budsjett_col}'\n")

if not art_col:
    raise KeyError(f"Fant ingen matchende art-kolonne i tabellen. Tilgjengelige kolonner: {list(df.columns)}")

# 2. Formater art til 3 siffer (f.eks. '202' eller 202 -> '202')
df['art_3siffer'] = (
    df[art_col]
    .astype(str)
    .str.strip()
    .str.replace(r'\.0$', '', regex=True)
    .str.zfill(3)
)

# 3. Konverter beløpskolonner fra tekst til rene flyttall (float)
belop_map = {
    regnskap_col: 'belop_regnskap_ytd',
    budsjett_col: 'belop_budsjett_ytd',
    avvik_col: 'belop_avvik_ytd',
    arsbudsjett_col: 'belop_arsbudsjett',
    fjor_col: 'belop_regnskap_fjor'
}

for src_col, target_col in belop_map.items():
    if src_col and src_col in df.columns:
        df[target_col] = (
            df[src_col]
            .astype(str)
            .str.replace(' ', '')
            .str.replace(',', '.')
        )
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0.0)
    else:
        df[target_col] = 0.0

# 4. Lagre som ren og indeksert fact_bomiljo i SQLite
df.to_sql("fact_bomiljo", conn, if_exists="replace", index=False)

cursor = conn.cursor()
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_bomiljo_art ON fact_bomiljo(art_3siffer);")
conn.commit()

print(f"✨ 'fact_bomiljo' opprettet feilfritt med {len(df)} rader og rene tallverdier!")
conn.close()