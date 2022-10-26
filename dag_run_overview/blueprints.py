from flask import Blueprint

dro_blueprint = Blueprint(
    "dag_run_overview_plugin",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/droview/static/",
)
