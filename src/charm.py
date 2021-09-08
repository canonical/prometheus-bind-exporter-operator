#!/usr/bin/env python3
# Copyright 2021 Unicorn
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus-bind-exporter as charm the service.
"""

import logging
import subprocess

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus

logger = logging.getLogger(__name__)


class PrometheusBindExporterOperatorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self._stored.set_default()
        self.unit.status = ActiveStatus("Unit is ready")

    def _on_install(self, _):
        """installation hook that installs prometheus-bind-exporter daemon."""
        self.unit.status = MaintenanceStatus("Installing prometheus-bind-exporter")
        snap_file = self.model.resources.fetch("prometheus-bind-exporter")
        subprocess.check_call(["snap", "install", "--dangerous", snap_file])
        self.unit.status = ActiveStatus("Unit is ready")


if __name__ == "__main__":
    main(PrometheusBindExporterOperatorCharm)
