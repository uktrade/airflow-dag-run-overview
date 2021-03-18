from setuptools import find_packages, setup

setup(
    description="Airflow DAG Run Overview",
    install_requires=["apache-airflow>=1.10.4"],
    name="dag_run_overview",
    packages=find_packages(include=["dag_run_overview"]),
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    version="0.0.1",
    entry_points={
        "airflow.plugins": [
            "DagRunOverview = dag_run_overview.dag_run_overview:DagRunOverviewPlugin"
        ]
    },
)
