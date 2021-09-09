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
    def setUp(self):
        self.harness = Harness(charm.PrometheusBindExporterOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    @mock.patch.object(charm, "subprocess")
    def test_on_install(self, mock_subprocess):
        """Test install hook."""
        with mock.patch.object(self.harness.model.resources, "fetch") as mock_fetch:
            mock_fetch.return_value = "test"
            self.harness.charm.on.install.emit()

            mock_fetch.assert_called_once_with("prometheus-bind-exporter")
            mock_subprocess.check_call.assert_called_once_with(["snap", "install",
                                                                "--dangerous", "test"])
            self.assertNotEqual(self.harness.charm.unit.status,
                                ActiveStatus("Unit is ready"))
