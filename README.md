Arbeidsflytmodell for Helse og Mestring — Bo og Miljøtjenester
Automatisert databehandling, semantisk Power BI-modellering (PBIP) og prediktiv økonomistyring for Kristiansand kommune.

Om prosjektet
Dette prosjektet etablerer en helhetlig, automatisert og regelbasert arbeidsflytmodell for økonomistyring i Kristiansand kommune, spesifikt tilpasset Bo og Miljøtjenester under virksomhetsområdet Helse og mestring. Modellen kobler kildedata fra kommunens ERP- og fagsystemer (Visma ERP, Framsikt EPM, GAT) med en lokal SQLite-database, automatiserte Python ETL-skripter, og et versjonskontrollert Power BI Project (PBIP) med semantiske TMDL-målinger.

Systemarkitektur & Datastruktur
Kildedata & Staging: BoMiljø.csv (Måned 1–8 Bokført, Måned 9–12 Gjenstående) og KOSTRA Kontoplan.
ETL & Tallvask (Python & SQLite): 03*Scripts/prep_bomiljo.py vasker data inn i SQLite-databasen 02_Data_Processed/helse_mestring_sqlite.db som faktatabellen fact_bomiljo.
Semantisk Datamodellering (Power BI Project / PBIP & TMDL): Plassert under pbi/BoMiljo-project.pbip med målingstabellen \_Measures.tmdl.
Prognose & Versjonskontroll: Helårsprognose via 03_Scripts/forecast_bomiljo.py og versjonskontroll i Git.
Mappe- og Filstruktur
Arbeidsflytmodell for Helse og Mestring/
│
├── 01_Data_Raw/ # Rådata fra kildedata
│ ├── BoMiljø.csv # Transaksjons/periodedata for Bo og Miljø
│ ├── Komskole.csv # Transaksjonsdata for kommunal skole
│ └── dim_kostra_kontoplan_framsikt.csv # Framsikt/KOSTRA-artskontoplan
│
├── 02_Data_Processed/ # SQLite-datamodell
│ └── helse_mestring_sqlite.db # Inneholder fact_bomiljo, stg*_, dim\__
│
├── 03_Scripts/ # Python-skripter for ETL og prognose
│ ├── prep_bomiljo.py # Vasker stg_bomiljo -> fact_bomiljo
│ ├── forecast_bomiljo.py # EOY run-rate helårsprognose
│ └── create_sql_views.py # SQL Views for SQLite
│
├── pbi/ # Power BI Project (.pbip)
│ ├── BoMiljo-project.pbip # Hovedfil for Power BI Project
│ ├── BoMiljo-project.Report/ # Rapportsider og layout
│ └── BoMiljo-project.SemanticModel/ # Semantisk modell (TMDL-format)
│ └── definition/tables/\_Measures.tmdl # Alle DAX-målinger
│
├── .gitignore # Git ekskluderingsregler
└── README.md # Prosjektdokumentasjon
DAX-målingsarkitektur (\_Measures.tmdl)
Målingene i Power BI forvaltes i TMDL-format med kappet YTD-budsjettlogikk for å sikre at 12 måneders budsjett ikke sammenlignes med 8 måneders bokført regnskap.

Kjernemålinger:
Regnskap YTD: SUM(fact_bomiljo[belop_regnskap_ytd])
Budsjett YTD: Dynamisk kappet til siste bokførte måned (Måned 8).
Avvik YTD: [Budsjett YTD] - [Regnskap YTD] (Positivt = ubenyttet ramme / mindreforbruk).
Avvik YTD %: DIVIDE([Avvik YTD], [Budsjett YTD], 0)
Status Avvik %: Relativ KPI-status (🔴 Betydelig merforbruk, 🟡 Mindre merforbruk, 🟢 Mindreforbruk).
Kom i gang

1. Klargjør datatabellen i SQLite
   python 03_Scripts/prep_bomiljo.py
2. Åpne Power BI Project
   Åpne pbi/BoMiljo-project.pbip i Power BI Desktop. Tabellen fact_bomiljo kobles mot dim_kostra_kontoplan_framsikt på art_3siffer.

3. Versjonskontroll
   git add .
   git commit -m "feat: oppdatert semantisk datamodell, TMDL-målinger og README"
   git push -u origin main
   Juridisk forankring og rammeverk
   Kommuneloven § 14-5: Krav om rapportering, kontroll og iverksetting av tiltak ved budsjettavvik.
   KOSTRA-kontoplan: Standardisert arts- og funksjonskontoplan fra Kommunal- og distriktsdepartementet (KDD) / SSB.
   Framsikt EPM & Visma ERP: Integrasjon mot kommunens vedtatte økonomiplan og driftssystemer.
