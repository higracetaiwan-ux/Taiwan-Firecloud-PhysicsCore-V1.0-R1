#!/usr/bin/env python3
"""Taiwan Firecloud V8.4.5.1 HITRAN local spectroscopy bootstrap.

This helper NEVER bundles or fabricates HITRAN spectroscopy.  It can:
  1. create/audit the Firecloud local HITRAN directory;
  2. use official HAPI 1.3 line-by-line fetch_by_ids() as the primary downloader
     for H2O/O2 560-765 nm transitions; HAPI2 is retained only as an
     optional legacy fallback because its transitions header endpoint may 404;
  3. print the next command that builds Firecloud's diagnostic-band T/P LUT.

Official HITRAN access requires a personal API key.  Keep the key in environment
or Streamlit Secrets and never commit it to the repository.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from firecloud.hitran_readiness import hitran_backend_status, inspect_hitran_coefficient_table

NUMIN = 1e7 / 765.0
NUMAX = 1e7 / 560.0
TABLES = {"H2O": "H2O_560_765", "O3": "O3_560_765", "O2": "O2_560_765"}
MIN_SOURCE_COVERAGE_MARGIN_CM = 100.0
DIAGNOSTIC_BANDS_NM = (575.0, 600.0, 650.0, 700.0, 750.0)
# Official HITRAN global isotopologue IDs (natural isotopologues used by Firecloud).
# H2O: 1-6 + 129; O3: 16-20; O2: 36-38.
HAPI1_ISO_IDS = {"H2O": [1, 2, 3, 4, 5, 6, 129], "O3": [16, 17, 18, 19, 20], "O2": [36, 37, 38]}


def _print_status(db: Path) -> dict:
    os.environ["FIRECLOUD_HITRAN_DB"] = str(db)
    # The command-line --db is authoritative for this build audit. Do not let
    # the packaged four-band Runtime LUT hide a newly built 360-state table.
    status = hitran_backend_status(db_path=db)
    safe = dict(status)
    print(json.dumps(safe, ensure_ascii=False, indent=2))
    return status


def _copy_hapi_table(search_root: Path, table: str, db: Path) -> None:
    found = {}
    for suffix in (".data", ".header"):
        candidates = list(search_root.rglob(table + suffix))
        if candidates:
            src = max(candidates, key=lambda p: p.stat().st_mtime)
            dst = db / (table + suffix)
            shutil.copy2(src, dst)
            found[suffix] = str(src)
    if ".data" not in found or ".header" not in found:
        raise RuntimeError(f"HAPI2 fetch returned but local table {table} (.data/.header) was not found under {search_root}")



def _download_with_hapi1(db: Path, api_key: str, gases: list[str] | None = None) -> None:
    """Primary line-list downloader using official HAPI 1.3.

    HAPI 1.x writes its native ``.data``/``.header`` tables directly into the
    database selected by ``db_begin``.  Firecloud therefore avoids the HAPI2
    transitions metadata/header route that returned HTTP 404 in the deployed
    Python 3.14 environment.

    The personal HITRAN key remains in the process environment for current
    HITRAN authentication compatibility, but is never printed or persisted.
    """
    requested = list(gases or TABLES.keys())
    invalid = [g for g in requested if g not in TABLES]
    if invalid:
        raise RuntimeError(f"Unsupported gas selection: {invalid}")
    if not api_key.strip():
        raise RuntimeError("HITRAN_API_KEY is not configured")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            import hapi  # type: ignore
    except Exception as exc:
        raise RuntimeError("HAPI 1.x is not installed. Install hitran-api>=1.3.0.0.") from exc

    # Prefer HTTPS for current HITRANonline.  Different HAPI releases expose
    # this through VARIABLES and/or GLOBAL_HOST; set both when available.
    try:
        if isinstance(getattr(hapi, "VARIABLES", None), dict):
            hapi.VARIABLES["GLOBAL_HOST"] = "https://hitran.org"
    except Exception:
        pass
    try:
        if hasattr(hapi, "GLOBAL_HOST"):
            hapi.GLOBAL_HOST = "https://hitran.org"
    except Exception:
        pass

    # Keep credentials available to any authentication bridge in current HAPI.
    os.environ["HITRAN_API_KEY"] = api_key.strip()
    hapi.db_begin(str(db))
    version = str(getattr(hapi, "HAPI_VERSION", getattr(hapi, "__version__", "unknown")))
    print(f"HAPI1 version: {version}", flush=True)
    for gas in requested:
        table = TABLES[gas]
        if (db / f"{table}.data").is_file() and (db / f"{table}.header").is_file():
            print(f"CACHE_HIT {gas}: {table} provider=HAPI1_LOCAL", flush=True)
            continue
        ids = HAPI1_ISO_IDS[gas]
        print(
            f"DOWNLOADING {gas}: {table} provider=HAPI1 fetch_by_ids iso_ids={ids} "
            f"[{NUMIN:.2f}, {NUMAX:.2f}] cm^-1",
            flush=True,
        )
        try:
            hapi.fetch_by_ids(table, ids, NUMIN, NUMAX)
        except Exception as exc:
            raise RuntimeError(f"HAPI1_DOWNLOAD_FAILED {gas}: {type(exc).__name__}: {exc}") from exc
        if not (db / f"{table}.data").is_file() or not (db / f"{table}.header").is_file():
            raise RuntimeError(f"HAPI1 fetch returned without complete local table {table}")
        print(f"READY {gas}: {table} provider=HAPI1 [{NUMIN:.2f}, {NUMAX:.2f}] cm^-1", flush=True)

def _download_with_hapi2(db: Path, api_key: str, gases: list[str] | None = None) -> None:
    """Use official HAPI2 API contract when hapi2 is available.

    HAPI2 reads config.json from the current working directory at import time.
    The fetched transition helper emits HAPI-compatible .data/.header files;
    those are copied into FIRECLOUD_HITRAN_DB for the existing Voigt builder.
    """
    if not api_key.strip():
        raise RuntimeError("HITRAN_API_KEY is not configured")

    requested = list(gases or TABLES.keys())
    invalid = [g for g in requested if g not in TABLES]
    if invalid:
        raise RuntimeError(f"Unsupported gas selection: {invalid}")

    with tempfile.TemporaryDirectory(prefix="firecloud_hitran_hapi2_") as td:
        work = Path(td)
        tmp = work / "tmp"
        data = work / "db"
        tmp.mkdir(); data.mkdir()
        cfg = {
            "engine": "sqlite",
            "database": "local",
            "user": "root",
            "pass": None,
            "database_dir": str(data),
            "echo": False,
            "debug": False,
            "display_fetch_url": False,
            "proxy": None,
            "host": "https://hitran.org",
            "api_version": "v2",
            "tmpdir": str(tmp),
            "api_key": api_key.strip(),
        }
        (work / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        old_cwd = Path.cwd()
        try:
            os.chdir(work)
            try:
                import hapi2  # type: ignore
            except Exception as exc:
                raise RuntimeError(
                    "HAPI2 is not installed. Install the optional builder dependency from "
                    "requirements-hitran-builder.txt in a one-time builder environment."
                ) from exc

            # Populate local HAPI2 metadata first, then fetch all natural
            # isotopologues of the three required molecules over the narrow
            # Firecloud spectral interval.
            hapi2.SETTINGS["api_key"] = api_key.strip()
            hapi2.fetch_molecules()
            molecule_aliases = {"H2O": "H2O", "O3": "O3", "O2": "O2"}
            for gas in requested:
                table = TABLES[gas]
                # Existing complete local line table means this gas is already cached.
                if (db / f"{table}.data").is_file() and (db / f"{table}.header").is_file():
                    print(f"CACHE_HIT {gas}: {table}", flush=True)
                    continue
                print(f"DOWNLOADING {gas}: {table} [{NUMIN:.2f}, {NUMAX:.2f}] cm^-1", flush=True)
                mol = hapi2.Molecule(molecule_aliases[gas])
                hapi2.fetch_isotopologues([mol])
                hapi2.fetch_transitions(mol.isotopologues, NUMIN, NUMAX, table)
                _copy_hapi_table(work, table, db)
                print(f"READY {gas}: {table} [{NUMIN:.2f}, {NUMAX:.2f}] cm^-1", flush=True)
        finally:
            os.chdir(old_cwd)



def _validate_and_import_par(db: Path, gas: str, source_path: Path) -> None:
    """Import a user-downloaded standard HITRAN .par line list into the HAPI local DB.

    This is an explicit fallback for deployments where HITRAN's remote HAPI/HAPI2
    transition endpoints return HTTP 404.  It does not fabricate spectroscopy.
    The input must be a standard 160-character HITRAN line-by-line file for the
    selected molecule, and lines outside Firecloud's 600-750 nm interval are
    discarded before the HAPI-native .data/.header table is written.
    """
    if gas not in TABLES:
        raise RuntimeError(f"Unsupported gas selection: {gas}")
    if not source_path.is_file():
        raise RuntimeError(f"Manual HITRAN file not found: {source_path}")
    molecule_ids = {"H2O": 1, "O3": 3, "O2": 7}
    expected_mol = molecule_ids[gas]
    raw = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
    kept = []
    bad = 0
    wrong_molecule = 0
    for line in raw:
        if not line.strip():
            continue
        if len(line) < 15:
            bad += 1
            continue
        try:
            mol = int(line[0:2])
            nu = float(line[3:15])
        except Exception:
            bad += 1
            continue
        if mol != expected_mol:
            wrong_molecule += 1
            continue
        if NUMIN <= nu <= NUMAX:
            kept.append(line.rstrip('\r\n'))
    if not kept:
        raise RuntimeError(
            f"MANUAL_PAR_IMPORT_EMPTY {gas}: no valid molecule {expected_mol} lines in "
            f"{NUMIN:.2f}-{NUMAX:.2f} cm^-1; bad={bad}, wrong_molecule={wrong_molecule}"
        )
    kept_nu = [float(line[3:15]) for line in kept]
    # HITRAN line lists are sparse: a molecule need not have transitions at
    # either edge of the requested wavelength interval.  The former global
    # min/max endpoint test incorrectly rejected valid O2 data whose 575-nm
    # band is real but whose 560-nm edge has no O2 transition. Validate the
    # diagnostic bands instead, while keeping molecule-specific physical gaps
    # distinguishable from an absent source band.
    band_counts = {}
    for center in DIAGNOSTIC_BANDS_NM:
        lo_cm = 1e7 / (center + 12.5)
        hi_cm = 1e7 / (center - 12.5)
        band_counts[int(center)] = sum(lo_cm <= nu <= hi_cm for nu in kept_nu)
    required_bands = DIAGNOSTIC_BANDS_NM if gas == "H2O" else (575.0, 650.0, 700.0, 750.0)
    missing_bands = [int(center) for center in required_bands if band_counts[int(center)] < 1]
    if missing_bands:
        raise RuntimeError(
            f"MANUAL_PAR_TARGET_BAND_INSUFFICIENT {gas}: missing real HITRAN line(s) "
            f"in diagnostic band(s) {missing_bands}; counts={band_counts}; "
            f"kept_range={min(kept_nu):.2f}-{max(kept_nu):.2f} cm^-1"
        )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            import hapi  # type: ignore
    except Exception as exc:
        raise RuntimeError("HAPI 1.x is required to import standard HITRAN .par files") from exc
    table = TABLES[gas]
    par_path = db / f"{table}.par"
    # Remove prior generated storage only for this table so db_begin reads the new par.
    for suffix in ('.data', '.header'):
        try:
            (db / f"{table}{suffix}").unlink(missing_ok=True)
        except Exception:
            pass
    par_path.write_text('\n'.join(kept) + '\n', encoding='utf-8')
    hapi.db_begin(str(db))
    # db_begin creates a standard header for .par files and parses them into cache.
    if table not in getattr(hapi, 'LOCAL_TABLE_CACHE', {}):
        raise RuntimeError(f"MANUAL_PAR_HAPI_PARSE_FAILED {gas}: table {table} not loaded")
    hapi.cache2storage(table)
    try:
        par_path.unlink(missing_ok=True)
    except Exception:
        pass
    if not (db / f"{table}.data").is_file() or not (db / f"{table}.header").is_file():
        raise RuntimeError(f"MANUAL_PAR_IMPORT_FAILED {gas}: HAPI storage files were not created")
    print(
        f"READY {gas}: {table} provider=MANUAL_HITRAN_PAR lines={len(kept)} "
        f"range=[{NUMIN:.2f},{NUMAX:.2f}]cm^-1 bands={band_counts} bad={bad} wrong_molecule={wrong_molecule}",
        flush=True,
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.environ.get("FIRECLOUD_HITRAN_DB", "hitran_db"))
    parser.add_argument("--download", action="store_true", help="Fetch H2O/O3/O2 transitions using official HAPI 1.3 + HITRAN_API_KEY")
    parser.add_argument("--download-gas", choices=tuple(TABLES.keys()), default="", help="Fetch only one gas; used by the Streamlit staged bootstrap")
    parser.add_argument("--status-json", default="", help="Optional path to write safe readiness metadata")
    parser.add_argument("--import-par-gas", choices=tuple(TABLES.keys()), default="", help="Import a manually downloaded standard HITRAN .par file for one gas")
    parser.add_argument("--import-par-file", default="", help="Path to the manually downloaded .par/.txt line-list file")
    args = parser.parse_args()

    db = Path(args.db).expanduser().resolve()
    db.mkdir(parents=True, exist_ok=True)
    os.environ["FIRECLOUD_HITRAN_DB"] = str(db)
    print(f"FIRECLOUD_HITRAN_DB={db}")
    print(f"Required source interval: 560-765 nm = {NUMIN:.2f}-{NUMAX:.2f} cm^-1")
    print("Required gases: H2O, O3, O2")

    if args.import_par_gas:
        if not args.import_par_file:
            raise RuntimeError("--import-par-file is required with --import-par-gas")
        _validate_and_import_par(db, args.import_par_gas, Path(args.import_par_file).expanduser().resolve())

    if args.download or args.download_gas:
        api_key = os.environ.get("HITRAN_API_KEY", "").strip()
        gases = [args.download_gas] if args.download_gas else list(TABLES.keys())
        try:
            _download_with_hapi1(db, api_key, gases=gases)
        except Exception as hapi1_exc:
            # Optional legacy fallback.  Keep the HAPI1 failure visible; if the
            # known HAPI2 transitions endpoint also fails, report both causes.
            allow_hapi2 = os.environ.get("FIRECLOUD_HITRAN_ALLOW_HAPI2_FALLBACK", "0").strip().lower() in {"1", "true", "yes", "on"}
            if not allow_hapi2:
                raise
            print(f"HAPI1 FAILED; trying optional HAPI2 fallback: {hapi1_exc}", flush=True)
            try:
                _download_with_hapi2(db, api_key, gases=gases)
            except Exception as hapi2_exc:
                raise RuntimeError(f"HAPI1_AND_HAPI2_FAILED: HAPI1={hapi1_exc}; HAPI2={hapi2_exc}") from hapi2_exc

    status = _print_status(db)
    if args.status_json:
        Path(args.status_json).write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {args.status_json}")

    if not status.get("coefficient_table_complete", False):
        print("\nNext step after local line tables exist:")
        print(f"  python build_hitran_band_coefficients.py --db {db}")
        print("Then rerun this helper to verify coefficient_table_complete=true.")
    else:
        if status.get("extended_575nm_ready", False):
            print("\nHITRAN runtime spectroscopy: READY_LOCAL_HITRAN_LUT_575NM")
        else:
            print("\nHITRAN runtime spectroscopy: READY_LOCAL_HITRAN_LUT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
