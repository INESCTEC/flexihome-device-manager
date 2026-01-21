# Energy Manager Code Structure

``` text

.
|
└──energy_manager_service       (Python module)
    └───controllers                 (API controllers)
        |   energy_manager_service_controller.py
    
    └── models                      (OO Classes)
        └──database                     (ORM database models)
            |   energy_manager_db.py
        |   cycle_model_vars.py     (Cycle as input variables for the optimizer)

    └──optimizers                   (Optimizer classes and logic)
        │   scheduler.py            (SCIP optimizer)
        |   optimizer_pipeline.py   (input-output pipeline)
        |   save_recommendation.py

    └──jobs
        |   task_reminder.py
    
    └── clients                     (API clients)
        └── common
            |   get.py                  (Processes GET requests)
            |   post.py                 (Processes POST requests)
            |   process_response.py     (Handles responses from the services)
        └── hems_services
            |   account_manager.py
            |   device_manager.py
            |   energy_prices.py
            |   forecast.py
        └── sentinel
            |   eco_signal.py
    
    └── events                      (Kafka consumers/producers)
        |   events.py                   (Events modulation)
        |   notification_events.py
    
    └── utils                       (General utilities)
        └── date                        (Process dates)
            |   datetime.py
        └── type_conversion             (Convert data to certain types)
            |   data_to_array.py

    └── test
        |   setup_test_env.py
        |   clear_database.py

    |   __init__.py             (High level module configurations)
    |   __main__.py             (Web server)
    |   config.py               (Environment variables)


└──Docker-compose (Setup for local tests)
    └──connectors
        |   account_manager.json
    |   docker-compose.yml
    |   cassandra_start.cql
    |   gunicorn.conf

└──docs
|
|   energy-manager-openapi.yaml
|   Dockerfile
|   gitlab-ci.yml
|   requirements.txt
|   test-requirements.txt
|   tox.ini
```
