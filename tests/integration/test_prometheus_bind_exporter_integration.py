import logging
import urllib.request

import pytest

log = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test):
    """Build and deploy openstack-integrator in bundle"""
    charm = await ops_test.build_charm(".")
    bundle = ops_test.render_bundle(
        "tests/data/bundle.yaml", main_charm=charm, series="focal"
    )
    await ops_test.model.deploy(bundle)
    await ops_test.model.wait_for_idle(status="active", timeout=20 * 60)


async def test_prometheus_targets(ops_test):
    """Test if prometheus have all targets."""
    prometheus2_app = ops_test.model.applications["prometheus2"]
    prometheus2_app_config = await prometheus2_app.get_config()
    prometheus_address = prometheus2_app.units[0].private_address
    prometheus_port = prometheus2_app_config.get("web-listen-port", {}).get("value")
    assert prometheus2_app.units[0].workload_status == "active"
    targets_url = f"http://{prometheus_address}:{prometheus_port}/api/v1/targets"

    # check default configuration
    with urllib.request.urlopen(targets_url) as response:
        unit = ops_test.model.applications["prometheus-bind-exporter"].units[0]
        assert f"http://{unit.private_address}:9119" in response.read().decode()

    # test changing configuration
    await ops_test.model.applications["prometheus-bind-exporter"].set_config(
        {"exporter-listen-port": "9120"})
    await ops_test.model.wait_for_idle(status="active", timeout=5 * 60)
    with urllib.request.urlopen(targets_url) as response:
        unit = ops_test.model.applications["prometheus-bind-exporter"].units[0]
        assert f"http://{unit.private_address}:9120" in response.read().decode()
