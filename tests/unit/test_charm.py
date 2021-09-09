# Copyright 2021 Unicorn
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing
import unittest
from unittest import mock

import charm
from ops.testing import Harness

from build.venv.ops.model import ActiveStatus


class TestInitCharm(unittest.TestCase):
    def test_init(self):
        """Test initialization of charm."""
        harness = Harness(charm.PrometheusBindExporterOperatorCharm)
        harness.begin()

        self.assertNotEqual(harness.charm.unit.status, ActiveStatus("Unit is ready"))


class TestCharm(unittest.TestCase):

    def patch(self, obj, method):
        """Mock the method."""
        _patch = mock.patch.object(obj, method)
        mock_method = _patch.start()
        self.addCleanup(_patch.stop)
        return mock_method

    def setUp(self):
        self.harness = Harness(charm.PrometheusBindExporterOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        # mock subprocess
        self.mock_subprocess = self.patch(charm, "subprocess")
        # mock getting private address
        mock_get_binding = self.patch(self.harness.model, "get_binding")
        mock_get_binding.return_value = self.mock_binding = mock.MagicMock()
        self.mock_binding.network.bind_address = "127.0.0.1"
        # mock fetch resource
        self.mock_fetch = self.patch(self.harness.model.resources, "fetch")
        self.mock_fetch.return_value = "prometheus-bind-exporter.snap"

    def test_manage_prometheus_bind_exporter_service(self):
        """Test manage the prometheus-bind-exporter snap."""
        self.harness.charm._manage_prometheus_bind_exporter_service()

        self.mock_subprocess.check_call.assert_called_once_with(
            ["snap", "set", "prometheus-bind-exporter",
             "web.listen-address=127.0.0.1:9119",
             "web.stats-groups=server,view,tasks"])

    def test_on_install(self):
        """Test install hook."""
        exp_call = mock.call(["snap", "install", "--dangerous",
                              "prometheus-bind-exporter.snap"])
        self.harness.charm.on.install.emit()

        self.mock_fetch.assert_called_once_with("prometheus-bind-exporter")
        self.assertIn(exp_call, self.mock_subprocess.check_call.mock_calls)
        self.assertNotEqual(self.harness.charm.unit.status,
                            ActiveStatus("Unit is ready"))

    def test_on_config_changed(self):
        """Test config-changed hook."""
        # this will trigger self.harness.charm.on.config_changed.emit()
        self.harness.update_config({"exporter-listen-port": "9120",
                                    "exporter-stats-groups": "server"})

        self.assertEqual(self.harness.charm._stored.listen_port, "9120")
        self.assertEqual(self.harness.charm._stored.stats_groups, "server")
        self.mock_subprocess.check_call.assert_called_once_with(
            ["snap", "set", "prometheus-bind-exporter",
             "web.listen-address=127.0.0.1:9120",
             "web.stats-groups=server"])
        self.assertNotEqual(self.harness.charm.unit.status,
                            ActiveStatus("Unit is ready"))
