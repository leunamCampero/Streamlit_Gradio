"""Checks that the model reproduces numbers published in the papers."""
import numpy as np
import pytest

from core.cycling import SOLUTIONS, load_network, traffic_factor


@pytest.fixture(scope="module")
def net():
    return load_network()


def test_network_size(net):
    assert (net.N, net.E) == (3452, 4993)
    assert net.length.sum() / 1000 == pytest.approx(308, abs=1)


def test_b_max_matches_paper(net):
    assert net.max_budget() / 1e6 == pytest.approx(126.08, abs=0.01)


def test_ecc_km_dos6(net):
    assert net.km_per_dos(net.dos("ecc2025_gab"))[6] == pytest.approx(127.28, abs=0.01)
    assert net.km_per_dos(net.dos("ecc2025_mlcc"))[6] == pytest.approx(189.05, abs=0.01)


@pytest.mark.parametrize("solution", list(SOLUTIONS))
def test_solutions_only_upgrade(net, solution):
    assert (net.dos(solution) >= net.dos0).all()


def test_traffic_factor_extremes():
    assert traffic_factor([6])[0] == pytest.approx(0.84)
    assert traffic_factor([1])[0] == pytest.approx(0.84 * np.exp(8.448))


def test_safest_route_avoids_traffic(net):
    o, d = net.zone_node(48), net.zone_node(80)
    safe, short = net.route(o, d, weight="cyclist"), net.route(o, d, weight="length")
    assert short.length_m <= safe.length_m
    assert safe.exposure <= short.exposure
