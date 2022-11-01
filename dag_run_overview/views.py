import os

from airflow.models import clear_task_instances
from airflow.utils.db import provide_session
from airflow.utils.state import State

from flask import abort, jsonify, make_response, request
from flask_appbuilder import expose, BaseView

from dag_run_overview.utils import get_dag_state, get_enabled_dags, get_latest_dag_runs


class DROView(BaseView):
    default_view = 'list'

    @expose("/")
    @provide_session
    def list(self, session=None):
        state_filter = request.args.get('state')

        return self.render_template(
            "main.html",
            dags=get_latest_dag_runs(session, state_filter),
            State=State,
            filter=state_filter,
        )

    @expose("/v2/")
    @provide_session
    def list_v2(self, session=None):
        state_filter = request.args.get('state')
        priority = request.args.get('priority')
        return self.render_template(
            "main-v2.html",
            dags=get_latest_dag_runs(session),
            State=State,
            state_filter=state_filter,
            priority_filter=priority,
            docs_link=os.environ.get("DAG_RUN_OVERVIEW_DOCS_LINK")
        )

    @expose("/api/latest-dag-runs", ["GET"])
    @provide_session
    def list_latest_dag_runs(self, session=None):
        """
        Returns the last run information for all enabled DAGs. Optionally filtered
        by state and tag.
        """
        state_filter = request.args.get('state')
        tag_filter = request.args.get('tag')
        return jsonify(get_latest_dag_runs(session, state_filter, tag_filter))

    @expose('/api/clear-failed-dags', ['POST'])
    @provide_session
    def clear_failed_dag_runs(self, session=None):
        """
        Clear all tasks for all failed DAGs (that are enabled). Optionally filtering by tag.
        """
        tag_filter = request.args.get('tag')
        cleared_count = 0
        for dag in get_enabled_dags(session, request.args.get('tag')):
            last_run = dag.get_last_dagrun(
                session=session, include_externally_triggered=True
            )
            if last_run is None or get_dag_state(last_run) != State.FAILED:
                continue

            if tag_filter and tag_filter not in [x.name for x in dag.tags]:
                continue

            clear_task_instances(last_run.get_task_instances(), session)
            cleared_count += 1
        return jsonify(status=f"Cleared tasks for {cleared_count} failed DAGs")

    @expose('/api/clear-dags', ['POST'])
    @provide_session
    def clear_dag_runs(self, session=None):
        """
        Given a json object containing a `dag_igs` list, clear all tasks for
        the specified ids. If the DAG ID does not exist or the DAG is disabled
        it will be skipped.
        """
        if "dag_ids" not in request.json:
            return abort(
                make_response(jsonify(status="Please provide a list of dag_ids"), 400)
            )
        cleared_count = 0
        dags = [x for x in get_enabled_dags(session) if x.dag_id in request.json["dag_ids"]]
        for dag in dags:
            last_run = dag.get_last_dagrun(
                session=session, include_externally_triggered=True
            )
            if last_run is None:
                continue

            clear_task_instances(last_run.get_task_instances(), session)
            cleared_count += 1
        return jsonify(
            status=f"Cleared tasks for {cleared_count} DAG{'s' if cleared_count != 1 else ''}"
        )
