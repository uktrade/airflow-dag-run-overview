from airflow.plugins_manager import AirflowPlugin

from .blueprints import dro_blueprint
from .views import DROView


class DagRunOverviewPlugin(AirflowPlugin):
    name = "dag_run_overview"
    flask_blueprints = [dro_blueprint]
    appbuilder_views = [
        {
            "name": "DAG Runs",
            "category": "Dag Run Overview",
            "view": DROView()
        }
    ]