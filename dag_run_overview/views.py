from airflow.models import DagModel
from airflow.utils.db import provide_session
from airflow.utils.state import State

from flask import request
from flask_appbuilder import expose, BaseView


def _get_dag_state(dag_run):
    if dag_run.get_state() == "success":
        # We determine if a dag was successful or not based on the swap tables task.
        # This is because airflow marks a dag as success based on whether the last
        # task succeeded, which for us is always the case
        swap_task = dag_run.get_task_instance("swap-dataset-table-datasets_db")
        if swap_task is not None:
            return swap_task.current_state()
    return dag_run.get_state()


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
                current_state = _get_dag_state(last_run)
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
