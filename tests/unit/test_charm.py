# Copyright 2021 Unicorn
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest import mock

import charm
from ops.testing import Harness
from ops.model import ActiveStatus


class TestInitCharm(unittest.TestCase):
    def test_init(self):
        """Test initialization of charm."""
        harness = Harness(charm.PrometheusBindExporterOperatorCharm)
        harness.begin()

        self.assertEqual(harness.charm.unit.status, ActiveStatus("Unit is ready"))


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

    def test_on_install(self):
        """Test install hook."""
        exp_call = mock.call(["snap", "install", "--dangerous",
                              "prometheus-bind-exporter.snap"])
        self.harness.charm.on.install.emit()

        self.mock_fetch.assert_called_once_with("prometheus-bind-exporter")
        self.assertIn(exp_call, self.mock_subprocess.check_call.mock_calls)
        self.assertEqual(self.harness.charm.unit.status, ActiveStatus("Unit is ready"))
