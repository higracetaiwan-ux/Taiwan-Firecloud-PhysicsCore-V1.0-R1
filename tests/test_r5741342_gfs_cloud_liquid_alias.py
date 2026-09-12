from firecloud.providers import gfs_aws_range as a
from firecloud.providers import gfs_native as g


def test_cloud_liquid_alias_is_transport_only_and_canonical():
    assert a.expand_index_variable_aliases(["CLWMR"]) == {"CLWMR", "CLMR"}
    assert a.canonical_index_variable("CLMR") == "CLWMR"
    assert a.canonical_index_variable("CLWMR") == "CLWMR"
    assert g._shortname("CLMR") == "CLWMR"

def test_alias_does_not_infer_unrelated_fields():
    assert a.expand_index_variable_aliases(["ICMR"]) == {"ICMR"}
    assert a.canonical_index_variable("ICMR") == "ICMR"
