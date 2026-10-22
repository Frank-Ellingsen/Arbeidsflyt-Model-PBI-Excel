import os
import sqlite3
import pandas as pd

BASE_DIR = r"C:\Users\frank\Desktop\Arbeidsflytmodell for Helse og Mestring"
PROC_DIR = os.path.join(BASE_DIR, "02_Data_Processed")
SQLITE_DB = os.path.join(PROC_DIR, "helse_mestring_sqlite.db")

conn = sqlite3.connect(SQLITE_DB)

print("📊 Beregner helårsprognose på artsnivå (art_3siffer) og lagrer til SQLite...")

# 1. Les fact_bomiljo
df = pd.read_sql_query("SELECT * FROM fact_bomiljo", conn)

# 2. Filtrer bokførte måneder (M1-M8)
bokfort_df = df[df['status'].str.lower() == 'bokført']
mnd_passert = int(bokfort_df['maned_nr'].max())

# 3. Aggreger per art_3siffer (og beholder opprinnelig hovedgruppe som referanse)
group_cols = ['art_3siffer', 'hovedgruppe'] if 'hovedgruppe' in df.columns else ['art_3siffer']

df_grp = bokfort_df.groupby(group_cols)[['belop_budsjett_ytd', 'belop_regnskap_ytd']].sum().reset_index()

# Hent årsbudsjett per art
arsbudsjett_grp = df.groupby(group_cols)['belop_budsjett_ytd'].sum().reset_index()
arsbudsjett_grp.rename(columns={'belop_budsjett_ytd': 'belop_arsbudsjett'}, inplace=True)

forecast_df = pd.merge(df_grp, arsbudsjett_grp, on=group_cols)

# 4. Beregn Run-rate fremskriving (12 måneder)
forecast_df['mnd_passert'] = mnd_passert
forecast_df['belop_eoy_regnskap_est'] = (forecast_df['belop_regnskap_ytd'] / mnd_passert) * 12
forecast_df['belop_eoy_avvik_est'] = forecast_df['belop_arsbudsjett'] - forecast_df['belop_eoy_regnskap_est']

# 5. Lagre oppdatert tabell i SQLite
forecast_df.to_sql("fact_bomiljo_forecast", conn, if_exists="replace", index=False)

cursor = conn.cursor()
cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecast_art ON fact_bomiljo_forecast(art_3siffer);")
conn.commit()

conn.close()

print("✨ Tabellen 'fact_bomiljo_forecast' er nå oppdatert på artsnivå (art_3siffer)!")