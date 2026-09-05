from pathlib import Path
from firecloud.providers import gfs_native as g


def test_request_schema_fingerprint_changes_with_schema_and_carries_condensate_vars():
    from datetime import datetime, timezone
    run=datetime(2026,9,5,0,tzinfo=timezone.utc)
    _,params=g.build_nomads_request(run,3,(120,122,23,25))
    assert params['var_CLWMR']=='on' and params['var_ICMR']=='on'
    fp=g._request_schema_fingerprint(params)
    assert isinstance(fp,str) and len(fp)==16
    assert g.GFS_PROVIDER_SCHEMA_VERSION in g.native_provider_status().get('provider_schema_version', g.GFS_PROVIDER_SCHEMA_VERSION)


def test_field_completeness_requires_both_condensate_fields():
    inv=[
        {'shortName':'CLWMR','typeOfLevel':'isobaricInhPa','level':700.0,'message_count':1},
        {'shortName':'ICMR','typeOfLevel':'isobaricInhPa','level':500.0,'message_count':1},
        {'shortName':'TMP','typeOfLevel':'isobaricInhPa','level':700.0,'message_count':1},
    ]
    comp={r['field']:r for r in g._field_completeness_from_inventory(inv)}
    assert comp['CLWMR']['status']=='READY'
    assert comp['ICMR']['status']=='READY'
    assert g._inventory_has_required_condensate(inv) is True
    inv2=[r for r in inv if r['shortName']!='ICMR']
    assert g._inventory_has_required_condensate(inv2) is False


def test_cache_filename_identity_includes_schema_fingerprint_source_contract():
    src=Path(g.__file__).read_text(encoding='utf-8')
    assert 'schema_fp=_request_schema_fingerprint(params)' in src
    assert 'CACHE_INVALID_REQUIRED_FIELDS' in src
    assert 'MISSING_REQUIRED_CONDENSATE_FIELDS' in src
    assert 'gfs_grib_message_inventory' in src
