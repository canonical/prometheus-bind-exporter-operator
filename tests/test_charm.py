# Copyright 2021 Unicorn
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from charm import PrometheusBindExporterOperatorCharm
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(PrometheusBindExporterOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
