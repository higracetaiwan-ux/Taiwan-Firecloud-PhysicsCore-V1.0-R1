import pandas as pd
from firecloud.target_canvas_optics import classify_target_optical_truth, annotate_target_optical_truth, summarize_target_canvas_optical_evidence


def test_explicit_zero_condensate_conflict_is_not_zero_cot():
    t,s,e = classify_target_optical_truth({
        'resolver_state':'CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED',
        'target_optics_ready':False,
        'target_optics_bounded':False,
    })
    assert t == 'DIRECT_EVIDENCE_CONFLICT'
    assert s == 'UNRESOLVED_CONFLICT'
    assert e == 'NO_EXACT_RESPONSE'


def test_secondary_exact_and_bounded_are_distinct():
    t1,s1,e1 = classify_target_optical_truth({
        'resolver_state':'SECONDARY_FORECAST_NATIVE_OPTICS_EXACT',
        'target_optics_ready':True,
        'target_optics_bounded':False,
    })
    t2,s2,e2 = classify_target_optical_truth({
        'resolver_state':'ADJACENT_NATIVE_COT_BRACKET_BOUNDED',
        'target_optics_ready':False,
        'target_optics_bounded':True,
    })
    assert (t1,s1,e1) == ('EXACT_SECONDARY_NATIVE','EXACT_VALUE','EXACT_RESPONSE_ELIGIBLE')
    assert (t2,s2,e2) == ('BOUNDED_NATIVE_BRACKET','BOUNDED_INTERVAL','BOUNDED_ONLY_NOT_EXACT')


def test_annotation_never_claims_cf_rh_to_cot():
    df = pd.DataFrame([
        {'resolver_state':'DIRECT_NATIVE_CONDENSATE_COT','target_optics_ready':True,'target_optics_bounded':False},
        {'resolver_state':'CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED','target_optics_ready':False,'target_optics_bounded':False},
    ])
    out = annotate_target_optical_truth(df)
    assert not out['cf_or_rh_used_to_infer_cot'].any()
    assert list(out['target_cot_semantics']) == ['EXACT_VALUE','UNRESOLVED_CONFLICT']


def test_summary_reports_conflict_closure_without_inventing_cot():
    df = pd.DataFrame([
        {'solar_altitude_deg':-1.0,'resolver_state':'DIRECT_NATIVE_CONDENSATE_COT','target_optics_ready':True,'target_optics_bounded':False,'target_optical_truth_state':'EXACT_PRIMARY_NATIVE'},
        {'solar_altitude_deg':-1.0,'resolver_state':'MULTISOURCE_DIRECT_CONFLICT_UNRESOLVED','target_optics_ready':False,'target_optics_bounded':False,'target_optical_truth_state':'DIRECT_EVIDENCE_CONFLICT'},
    ])
    s = summarize_target_canvas_optical_evidence(df).iloc[0]
    assert s['optical_truth_exact_count'] == 1
    assert s['optical_truth_conflict_count'] == 1
    assert s['closure_state'] == 'CONFLICT_UNRESOLVED'
    assert abs(float(s['exact_fraction']) - 0.5) < 1e-12
