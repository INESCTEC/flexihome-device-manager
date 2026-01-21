#!/usr/bin/env python3

from waitress import serve

from energy_manager_service import connexionApp, app
from energy_manager_service.ssa.ssa_threads import SSAThreads


def main():
    connexionApp.add_api(
        'openapi.yaml',
        arguments={'title': 'Energy Manager Service'},
        pythonic_params=True,
        validate_responses=True
    )

    ssa_threads = SSAThreads()
    ssa_threads.start()
    
    serve(app, host='0.0.0.0', port=8080)

    ssa_threads.stop()

if __name__ == '__main__':
    main()
