# Taiwan Firecloud PhysicsCore — Current Project State

Current candidate: **V1.0-R5.7.41.3.4.1**.

- Historical GFS pgrb2/pgrb2b: NOMADS -> NOAA AWS `.idx` + HTTP Range fallback.
- Historical empty cloud-volume guard preserved from R5.7.41.3.3.
- Glow explicit cloud Missing state is now recognized by Analysis Integrity without converting Missing to Clear/Zero.
- Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.


## Release Gate
- Working-tree nodeid coverage: **605/605 PASS**
- Trial fresh-extract nodeid coverage: **605/605 PASS**
- Existing pandas FutureWarning: 1 (non-failure)
- Release Gate: CLOSED
