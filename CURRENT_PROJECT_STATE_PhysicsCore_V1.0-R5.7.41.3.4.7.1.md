# Taiwan Firecloud PhysicsCore — Current Project State

Current deployable candidate: **V1.0-R5.7.41.3.4.7.1**.

Science baseline remains **`R5.7.41.2_SHADOW_COT_AB_FROZEN`**.

## What changed from R5.7.41.3.4.7

A Streamlit Cloud startup failure exposed a deployment synchronization weakness: `app.py` imported `firecloud.case_archive_stream.write_csv_member_stream` at top level, so a missing or stale newly-added helper file caused the whole app to fail before UI startup.

R5.7.41.3.4.7.1 adds a guarded import plus exact-contract app-local fallback for that engineering-only CASE export helper. This does not alter Formation, Viewing, Twilight Glow, Photography Decision, cloud optics, spectral RT, Earth Shadow, or Missing semantics.

## Current development objective

Continue the R5.7.41.3.4.7 objective:

1. Run **2026-09-12 Sunset / TWS106 高美濕地** with warm provider caches.
2. Read the nine Viewing / Photography component timers.
3. Identify the actual largest component.
4. Optimize only that confirmed hotspot with science exact-equivalence.

Do not pre-assume `build_viewing_spectral_extinction()` is the hotspot.
