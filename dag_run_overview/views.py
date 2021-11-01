from airflow.models import DagModel
from airflow.utils.db import provide_session
from airflow.utils.state import State

from flask import request
from flask_appbuilder import expose, BaseView


class DROView(BaseView):
    default_view = 'list'

    @expose("/")
    @provide_session
    def list(self, session=None):
        dags = []
        for dag in session.query(DagModel).filter(DagModel.is_paused == False):
            last_run = dag.get_last_dagrun(include_externally_triggered=True)
            if last_run is not None:
                current_state = last_run.get_state()
                dags.append(
                    {
                        'dag_id': dag.dag_id,
                        'safe_dag_id': dag.safe_dag_id,
                        'schedule_interval': dag.schedule_interval,
                        'last_dag_run': last_run,
                        'state': current_state,
                        'tasks': sorted(
                            [
                                task
                                for task in last_run.get_task_instances()
                                if task.current_state() == current_state
                                and task.start_date is not None
                            ],
                            key=lambda x: x.start_date,
                        ),
                    }
                )

        state_filter = request.args.get('state')
        if state_filter:
            dags = filter(lambda x: x['state'] == state_filter, dags)

        return self.render_template(
            "main.html", dags=dags, State=State, filter=state_filter
        )
