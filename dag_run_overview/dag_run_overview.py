from airflow.plugins_manager import AirflowPlugin

from .blueprints import dro_blueprint
from .views import dro_view


class DagRunOverviewPlugin(AirflowPlugin):
    name = "dag_run_overview"

    admin_views = [dro_view]
    flask_blueprints = [dro_blueprint]
