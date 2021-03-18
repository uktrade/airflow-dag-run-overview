from airflow.models import DagBag
from airflow.utils.db import provide_session
from airflow.utils.state import State

from flask_admin import BaseView, expose

from flask_login import login_required


class DROView(BaseView):
    @expose("/")
    @provide_session
    @login_required
    def test(self, session=None):

        dags = [
            dag
            for dag in DagBag(include_examples=False).dags.values()
            if not dag.is_paused and dag.get_last_dagrun() is not None
        ]
        return self.render("main.html", dags=dags, State=State)


dro_view = DROView(category="Dag Runs", name="Dag Run Overview")
