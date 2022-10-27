from airflow.models import DagModel, DagRun, DagTag
from airflow.utils.state import State
from sqlalchemy.orm import joinedload


def get_dag_state(dag_run):
    if dag_run.get_state() == "success":
        # We determine if a dag was successful or not based on the swap tables task.
        # This is because airflow marks a dag as success based on whether the last
        # task succeeded, which for us is always the case
        swap_task = dag_run.get_task_instance("swap-dataset-table-datasets_db")
        if swap_task is not None:
            return swap_task.current_state()
    return dag_run.get_state()


def get_enabled_dags(session, tag=None):
    dags_query = session.query(
        DagModel
    ).filter(
        DagModel.is_paused == False
    ).options(
        joinedload(DagModel.tags)
    )
    if tag is not None:
        return dags_query.filter(DagModel.tags.any(DagTag.name == tag))
    return dags_query


def get_latest_dag_runs(session, state=None, tag=None):
    dags = []

    for dag in get_enabled_dags(session, tag):
        last_run = dag.get_last_dagrun(
            session=session, include_externally_triggered=True
        )
        if last_run is not None:
            current_state = get_dag_state(last_run)
            if state and current_state != state:
                continue
            dags.append(
                {
                    'dag_id': dag.dag_id,
                    'safe_dag_id': dag.safe_dag_id,
                    'schedule_interval': str(dag.schedule_interval),
                    'last_dag_run': {
                        'start_date': last_run.start_date,
                        'end_date': last_run.end_date,
                    },
                    'tags': [tag.name for tag in dag.tags],
                    'state': current_state,
                    'label_style': {
                        'background': State.color(current_state),
                        'foreground': State.color_fg(current_state),
                    },
                    'tasks': sorted(
                        [
                            {
                                'task_id': task.task_id,
                                'start_date': task.start_date,
                            }
                            for task in last_run.get_task_instances(
                                session=session, state=current_state
                            )
                            if task.start_date is not None
                        ],
                        key=lambda x: x['start_date'],
                    )
                    if current_state in [State.RUNNING, State.FAILED]
                    else [],
                }
            )
    return sorted(dags, key=lambda x: x["dag_id"])
