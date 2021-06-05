from airflow.models import DagBag
from airflow.utils.db import provide_session
from airflow.utils.state import State

from flask import request

from flask_admin import BaseView, expose

from flask_login import login_required


class DROView(BaseView):
    @expose("/")
    @provide_session
    @login_required
    def test(self, session=None):
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

        return self.render("main.html", dags=dags, State=State, filter=state_filter)


dro_view = DROView(category="Dag Runs", name="Dag Run Overview")
