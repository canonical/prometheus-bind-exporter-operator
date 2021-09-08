# prometheus-bind-exporter-operator

## Description

The subordinate charm for the designate-bind charm, which provides the
prometheus-bind-exporter snap to collect metrics about BIND v9+. At the same
time, it provides an opportunity to create a relation with prometheus2 and
grafana charm.
For more information about prometheus-bind-exporter visit 
[prometheus-community/bind-export].

## Usage

Deploy along with the [cs:designate-bind] charm.

    juju deploy prometheus-bind-exporter-operator bind-exporter
    juju relate designate-bind:prometheus-bind-exporter bind-exporter:prometheus-bind-exporter

Relate with [cs:prometheus2] charm creates a new target in prometheus.

    juju relate prometheus2:target bind-exporter:bind-exporter

Relate with [cs:grafana] charm creates a new dashboard, which requires
prometheus as a source. 

    juju relate prometheus2:grafana-source grafana:grafana-source  
    juju relate grafana:dashboard bind-exporter:grafana


## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests

---
[prometheus-community/bind-exporter]: https://github.com/prometheus-community/bind_exporter
[cs:designate-bind]: https://jaas.ai/designate-bind
[cs:prometheus2]: https://jaas.ai/prometheus2
[cs:grafana]: https://jaas.ai/grafana