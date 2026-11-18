import math
import pytest
from models import calculate_correlations, calculate_from_percent


def test_all_five_at_seventy_percent_and_hydraulic_eighty():
    p = calculate_correlations(0.7, 0.8)
    assert [r.method for r in p] == ["Stepanoff", "Childs", "Sharma", "Alatorre-Frenk", "Schmiedl"]
    assert p[0].h == pytest.approx(1/0.7)
    assert p[0].q == pytest.approx(1/math.sqrt(.7))
    assert p[1].h == pytest.approx(1/.7)
    assert p[1].q == pytest.approx(1/.7)
    assert p[2].h == pytest.approx(1/.7**1.2)
    assert p[2].q == pytest.approx(1/.7**.8)
    a = .85*.7**5 + .385
    assert p[3].h == pytest.approx(1/a)
    assert p[3].q == pytest.approx(a/(2*.7**9.5+.205))
    assert p[4].h == pytest.approx(-1.4 + 2.5/.8)
    assert p[4].q == pytest.approx(-1.5 + 2.4/.8**2)


def test_percent_converted_once_and_bep_scaling():
    rows = calculate_from_percent(70, 80, qp_bep_m3h=35, hp_bep_m=18)
    raw = calculate_correlations(.7, .8, qp_bep_m3h=35, hp_bep_m=18)
    assert rows == raw
    for row in rows:
        assert row.ht_m == pytest.approx(18 * row.h)
        assert row.qt_m3h == pytest.approx(35 * row.q)


def test_no_hydraulic_efficiency_means_no_schmiedl():
    rows = calculate_from_percent(70)
    assert len(rows) == 5
    assert all(r.h is not None for r in rows[:4])
    assert rows[-1].h is None
    assert rows[-1].q is None
    assert rows[-1].ht_m is None
    assert "ηh" in rows[-1].observation


def test_independent_optional_bep_scaling():
    a = calculate_correlations(.7, qp_bep_m3h=42)
    assert a[0].qt_m3h == pytest.approx(a[0].q*42)
    assert a[0].ht_m is None
    b = calculate_correlations(.7, hp_bep_m=20)
    assert b[0].ht_m == pytest.approx(b[0].h*20)
    assert b[0].qt_m3h is None


@pytest.mark.parametrize("eta", [0, -1, 1.0001, float('nan'), float('inf')])
def test_invalid_efficiencies(eta):
    with pytest.raises(ValueError):
        calculate_correlations(eta)
    with pytest.raises(ValueError):
        calculate_correlations(.8, eta)


@pytest.mark.parametrize("q,h", [(0,None), (-1,None), (None, 0), (None,-3), (float('inf'),None)])
def test_invalid_bep(q,h):
    with pytest.raises(ValueError):
        calculate_correlations(.8, qp_bep_m3h=q, hp_bep_m=h)


def test_does_not_claim_eta_t_or_power_t():
    p = calculate_correlations(.7, .7)[0]
    assert not hasattr(p, "eta_t")
    assert not hasattr(p, "pt_kw")
