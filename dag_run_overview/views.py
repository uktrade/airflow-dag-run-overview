from airflow.models import DagBag
from airflow.utils.db import provide_session
from airflow.utils.state import State

from flask import request
from flask_appbuilder import expose, BaseView


class DROView(BaseView):
    default_view = 'list'

    @expose("/")
    @provide_session
    def list(self, session=None):
        dags = [{
            'dag_id': dag.dag_id,
            'safe_dag_id': dag.safe_dag_id,
            'schedule_interval': dag.schedule_interval,
            'last_dag_run': dag.get_last_dagrun(include_externally_triggered=True),
        } for dag in DagBag(include_examples=False).dags.values()
            if not dag.is_paused and dag.get_last_dagrun() is not None
        ]

        state_filter = request.args.get('state')
        if state_filter:
            dags = filter(
                lambda x: x['last_dag_run'].get_state() == state_filter,
                dags
            )

        return self.render_template("main.html", dags=dags, State=State, filter=state_filter)
