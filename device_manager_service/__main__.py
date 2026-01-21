#!/usr/bin/env python3

from waitress import serve
from device_manager_service import connexionApp, app
from device_manager_service.accountEventConsumers import AccountEventConsumers

from device_manager_service.ssa.ssa_threads import SSAThreads


def main():
    # Register our API in connexion
    connexionApp.add_api('openapi.yaml',
                         arguments={'title': 'Device Manager Service'},
                         pythonic_params=True,
                         validate_responses=True)

    # Create the AccountEventConsumers object
    aec = AccountEventConsumers()
    # Start event threads
    aec.start()

    # Instantiate SSA threads
    ssa_threads = SSAThreads()
    ssa_threads.start()

    # Start web server to serve our REST API (the program waits until an exit signal is received)
    serve(app, host='0.0.0.0', port=8080)
    
    ssa_threads.stop()

    # After the web server exists, stop the event threads
    aec.stop()


if __name__ == '__main__':
    main()
