#!/usr/bin/env python3
# Copyright 2021 Unicorn
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus-bind-exporter as charm the service."""
import logging
import socket
import subprocess
from ipaddress import IPv4Address

import jinja2
from ops.charm import CharmBase, RelationChangedEvent, RelationDepartedEvent, RelationJoinedEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus

logger = logging.getLogger(__name__)

DEFAULT_LISTEN_PORT = 9119
DEFAULT_STATS_GROUPS = "server,view,tasks"


class PrometheusBindExporterOperatorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        # hooks
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        # relation hooks
        self.framework.observe(self.on.bind_exporter_relation_joined,
                               self._on_bind_exporter_relation_changed)
        self.framework.observe(self.on.bind_exporter_relation_changed,
                               self._on_bind_exporter_relation_changed)
        self.framework.observe(self.on.bind_exporter_relation_departed,
                               self._on_prometheus_relation_departed)
        self.framework.observe(self.on.grafana_relation_joined,
                               self._on_grafana_relation_joined)
        # initialise stored data
        self._stored.set_default(listen_port=DEFAULT_LISTEN_PORT,
                                 stats_groups=DEFAULT_STATS_GROUPS,)

        self.unit.status = ActiveStatus("Unit is ready")

    def _manage_prometheus_bind_exporter_service(self):
        """Manage the prometheus-bind-exporter service."""
        logger.debug("prometheus-bind-exporter configuration [web.listen-address=%s:%s, "
                     "web.stats-groups=%s] in progress", self.private_address or "",
                     self._stored.listen_port, self._stored.stats_groups)
        subprocess.check_call([
            "snap", "set", "prometheus-bind-exporter",
            f"web.listen-address={self.private_address or ''}:{self._stored.listen_port}",
            f"web.stats-groups={self._stored.stats_groups}"
        ])
        logger.info("prometheus-bind-exporter has been reconfigured")

    def _render_grafana_dashboard(self) -> str:
        """Render jinja2 template for Grafana dashboard."""
        parent_app_name = self.model.get_relation("bind-stats").app.name
        prometheus_app_name = self.model.get_relation("bind-exporter").app.name

        context = {
            "datasource": f"{prometheus_app_name} - Juju generated source",
            "machine_name": socket.gethostname(),
            "app_name": self.app.name,
            "parent_app_name": parent_app_name,
            "prometheus_app_name": prometheus_app_name,
        }
        templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.charm_dir / "templates"),
            variable_start_string="<<",
            variable_end_string=" >>",
        )
        template = templates.get_template("bind-grafana-dashboard.json.j2")
        return template.render(context)

    @property
    def private_address(self) -> str:
        """Return the private address of unit."""
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
        if self.model.get_relation("bind-stats") is None:
            self.unit.status = BlockedStatus("Subordinate relation not available.")
            return

        logger.info("Shared relation data with %s", self.unit.name)
        event.relation.data[self.unit].update({
            "hostname": self.private_address, "port": str(self._stored.listen_port)
        })

    def _on_prometheus_relation_departed(self, event: RelationDepartedEvent):
        """Prometheus relation departed hook.

        This hook will ensure the deletion of the target in Prometheus.
        """
        logger.info("Removing %s target from Prometheus." % self.unit)
        event.relation.data[self.unit].clear()

    def _on_grafana_relation_joined(self, event: RelationJoinedEvent):
        """Grafana relation joined hook.

        This hook will ensure the creation of a new dashboard in Grafana.
        """
        if not self.unit.is_leader():
            logger.debug("Grafana relation must be run on the leader unit. Skipping Grafana "
                         "configuration.")
            return

        if self.model.get_relation("bind-stats") is None:
            logger.warning("Subordinate relation not available. Skipping Grafana configuration.")
            self.unit.status = BlockedStatus("Subordinate relation not available.")
            return

        if self.model.get_relation("bind-exporter") is None:
            logger.warning("Prometheus relation not available. Skipping Grafana configuration.")
            self.unit.status = BlockedStatus("Prometheus relation not available.")
            return

        event.relation.data[self.unit].update({"dashboard": self._render_grafana_dashboard()})


if __name__ == "__main__":
    main(PrometheusBindExporterOperatorCharm)
