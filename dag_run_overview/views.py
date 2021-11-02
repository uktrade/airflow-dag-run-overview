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
        state_filter = request.args.get('state')

        dags = []

        for dag in (
            session.query(DagModel)
            .filter(DagModel.is_paused == False)
            .order_by(DagModel.dag_id)
        ):
            last_run = dag.get_last_dagrun(
                session=session, include_externally_triggered=True
            )
            if last_run is not None:
                current_state = last_run.get_state()
                if state_filter and current_state != state_filter:
                    continue
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
                                for task in last_run.get_task_instances(
                                    session=session, state=current_state
                                )
                                if task.start_date is not None
                            ],
                            key=lambda x: x.start_date,
                        )
                        if current_state in [State.RUNNING, State.FAILED]
                        else [],
                    }
                )

        return self.render_template(
            "main.html", dags=dags, State=State, filter=state_filter
        )
