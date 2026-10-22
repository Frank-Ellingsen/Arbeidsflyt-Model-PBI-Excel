import os
import sqlite3
import pandas as pd
import hashlib

BASE_DIR = r"C:\Users\frank\Desktop\Arbeidsflytmodell for Helse og Mestring"
RAW_DIR = os.path.join(BASE_DIR, "01_Data_Raw")
PROC_DIR = os.path.join(BASE_DIR, "02_Data_Processed")
os.makedirs(PROC_DIR, exist_ok=True)

SQLITE_DB = os.path.join(PROC_DIR, "helse_mestring_sqlite.db")

print("🔍 Starter skanning og smart-import av CSV-filer...\n")

def vask_navn(tekst):
    return (str(tekst).strip()
            .replace('ø', 'o').replace('Ø', 'O')
            .replace('å', 'a').replace('Å', 'A')
            .replace('æ', 'ae').replace('Æ', 'AE')
            .replace(' ', '_').replace('-', '_')
            .replace('/', '_').replace('(', '').replace(')', '').replace('.', '')
            .lower())

def beregn_fil_hash(filsti):
    hasher = hashlib.md5()
    with open(filsti, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def les_csv_smart(filsti):
    encoding = 'utf-8'
    try:
        with open(filsti, 'r', encoding='utf-8') as f:
            lines = [f.readline() for _ in range(15)]
    except UnicodeDecodeError:
        encoding = 'cp1252'
        with open(filsti, 'r', encoding='cp1252') as f:
            lines = [f.readline() for _ in range(15)]

    skiprows = 0
    keywords = ['art', 'lokasjon', 'konto', 'regnskap', 'budsjett', 'periode', 'funksjon', 'ansvar', 'post', 'kontonavn']

    for idx, line in enumerate(lines):
        line_lower = line.lower()
        matches = sum(1 for kw in keywords if kw in line_lower)
        if matches >= 2:
            skiprows = idx
            break

    df = pd.read_csv(filsti, skiprows=skiprows, dtype=str, encoding=encoding)
    
    # Rens kolonnenavn og fjern innrykkskolonner (unnamed)
    df.columns = [vask_navn(col) for col in df.columns]
    df = df.loc[:, ~df.columns.str.startswith('unnamed')]
    
    return df

conn = sqlite3.connect(SQLITE_DB)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

# 1. Opprett sporingstabell
cursor.execute("""
    CREATE TABLE IF NOT EXISTS _ingested_files (
        filnavn TEXT PRIMARY KEY,
        tabellnavn TEXT,
        fil_hash TEXT,
        antall_rader INTEGER,
        importert_dato TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

# 2. Hent eksisterende tabeller som RENE STRENGER (row[0])
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
eksisterende_tabeller = {row[0] for row in cursor.fetchall()}

# 3. Hent sporingslogg
sporingslogg = pd.read_sql_query("SELECT filnavn, tabellnavn, fil_hash FROM _ingested_files", conn)
importerte_filer = {row['filnavn']: (row['tabellnavn'], row['fil_hash']) for _, row in sporingslogg.iterrows()}

csv_filer = [f for f in os.listdir(RAW_DIR) if f.endswith('.csv')]

for csv_fil in csv_filer:
    filsti = os.path.join(RAW_DIR, csv_fil)
    nuvaerende_hash = beregn_fil_hash(filsti)

    # Korrekt strengekstraktering av filnavn med [0]
    fil_ren_navn = os.path.splitext(csv_fil)[0]
    tabell_navn = vask_navn(fil_ren_navn)

    if not tabell_navn.startswith('dim_') and not tabell_navn.startswith('stg_'):
        tabell_navn = f"stg_{tabell_navn}"

    skal_hoppe_over = False
    if csv_fil in importerte_filer and tabell_navn in eksisterende_tabeller:
        lagret_tabell, lagret_hash = importerte_filer[csv_fil]
        if lagret_hash == nuvaerende_hash:
            skal_hoppe_over = True

    if skal_hoppe_over:
        print(f"⏩ Hopper over '{csv_fil}' (Allerede importert i tabell '{tabell_navn}')")
        continue

    print(f"📦 Importerer '{csv_fil}' ➔ Tabell '{tabell_navn}'...")
    df = les_csv_smart(filsti)

    df.to_sql(tabell_navn, conn, if_exists="replace", index=False)
    eksisterende_tabeller.add(tabell_navn)
    print(f"  ✨ Skrevet {len(df)} rader og {len(df.columns)} kolonner til '{tabell_navn}'")

    cursor.execute("""
        INSERT OR REPLACE INTO _ingested_files (filnavn, tabellnavn, fil_hash, antall_rader)
        VALUES (?, ?, ?, ?);
    """, (csv_fil, tabell_navn, nuvaerende_hash, len(df)))
    conn.commit()

conn.close()
print("\n✨ Importering fullført!")