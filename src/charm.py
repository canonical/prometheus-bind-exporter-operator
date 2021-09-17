#!/usr/bin/env python3
# Copyright 2021 Unicorn
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus-bind-exporter as charm the service.
"""

import logging
import subprocess
from ipaddress import IPv4Address

from ops.charm import CharmBase, RelationChangedEvent, RelationDepartedEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus

logger = logging.getLogger(__name__)

DEFAULT_LISTEN_PORT = 9119
DEFAULT_STATS_GROUPS = "server,view,tasks"


class PrometheusBindExporterOperatorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        # relation
        self.framework.observe(self.on.bind_exporter_relation_joined,
                               self._on_bind_exporter_relation_changed)
        self.framework.observe(self.on.bind_exporter_relation_changed,
                               self._on_bind_exporter_relation_changed)
        self.framework.observe(self.on.bind_exporter_relation_departed,
                               self._on_prometheus_relation_departed)
        # initialise stored data
        self._stored.set_default(listen_port=DEFAULT_LISTEN_PORT,
                                 stats_groups=DEFAULT_STATS_GROUPS,)

        self.unit.status = ActiveStatus("Unit is ready")

    def _manage_prometheus_bind_exporter_service(self):
        """Manage the prometheus-bind-exporter service."""
        logger.debug("prometheus-bind-exporter configuration in progress")
        subprocess.check_call([
            "snap", "set", "prometheus-bind-exporter",
            f"web.listen-address={self.private_address or ''}:{self._stored.listen_port}",
            f"web.stats-groups={self._stored.stats_groups}"
        ])
        logger.info("prometheus-bind-exporter has been reconfigured")

    @property
    def private_address(self) -> str:
        """Returning the private address of unit."""
        address: IPv4Address = self.model.get_binding("bind-stats").network.bind_address
        return str(address)

    def _on_install(self, _):
        """Installation hook that installs prometheus-bind-exporter daemon."""
        self.unit.status = MaintenanceStatus("Installing prometheus-bind-exporter")
        snap_file = self.model.resources.fetch("prometheus-bind-exporter")
        subprocess.check_call(["snap", "install", "--dangerous", snap_file])
        self._manage_prometheus_bind_exporter_service()
        self.unit.status = ActiveStatus("Unit is ready")

    def _on_config_changed(self, _):
        """Config change hook."""
        self.unit.status = MaintenanceStatus("prometheus-bind-exporter configuration")
        self._stored.listen_port = self.config.get("exporter-listen-port")
        self._stored.stats_groups = self.config.get("exporter-stats-groups")
        self._manage_prometheus_bind_exporter_service()

        # update relation data
        bind_exporter_relation = self.model.get_relation("bind-exporter")
        if bind_exporter_relation:
            logger.info("Updating `bind-exporter` relation data.")
            bind_exporter_relation.data[self.unit].update({
                "hostname": self.private_address, "port": str(self._stored.listen_port)
            })

        self.unit.status = ActiveStatus("Unit is ready")

    def _on_bind_exporter_relation_changed(self, event: RelationChangedEvent):
        """Prometheus relation changed hook.

        This hook will ensure the creation of a new target in Prometheus.
        """
        logger.info("Registering new `%s` target in Prometheus.", self.unit.name)
        event.relation.data[self.unit].update({
            "hostname": self.private_address, "port": str(self._stored.listen_port)
        })

    def _on_prometheus_relation_departed(self, event: RelationDepartedEvent):
        """Prometheus relation departed hook.

        This hook will ensure the deletion of the target in Prometheus.
        """
        logger.info("Removing `%s` target from Prometheus.")
        event.relation.data[self.unit].clear()


if __name__ == "__main__":
    main(PrometheusBindExporterOperatorCharm)
