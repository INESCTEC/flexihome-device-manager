import threading, traceback
from time import sleep

from energy_manager_service.ssa.cybergrid.ssa_classes.pt_pilot_reactive import PTPilotReactiveCybergridSSA
from energy_manager_service.ssa.cybergrid.config import CybergridConfig

from energy_manager_service.ssa.cybergrid.setpoint_handle_interaction import setpoint_handle

from energy_manager_service import Config, generalLogger, db


class SSAThreads:
    def __init__(self):
        self.exitEvent = threading.Event()

        self.threads = {}

        if Config.CYBERGRID_THREAD and Config.MAINTENANCE_MODE == False:
            name = 'CybergridHandleThread'
            self.threads[name] = threading.Thread(name=name, target=cybergrid_thread_main, args=(self.exitEvent,))
        else:
            generalLogger.warning("Cybergrid thread is disabled or Maintenance Mode is enabled.")

    # Start threads
    def start(self):
        for thread in self.threads.values():
            thread.start()

    # Stop threads and wait for them to exit
    def stop(self):
        self.exitEvent.set()

        # Join all threads
        for thread in self.threads.values():
            thread.join()


def cybergrid_thread_main(exitEvent):
    setup_complete = False
    while not setup_complete:
        try:
            cybergrid_ssa = PTPilotReactiveCybergridSSA(
                ga_url=CybergridConfig.PT_PILOT_GENERIC_ADAPTER_URL,
                ss_email=CybergridConfig.USER_EMAIL,
                ss_password=CybergridConfig.USER_PASSWORD,
                kb_name=CybergridConfig.REACTIVE_KB_NAME,
                kb_description=CybergridConfig.REACTIVE_KB_DESCRIPTION,
                asset_id=CybergridConfig.REACTIVE_KB_ASSET_ID,
                logger=generalLogger
            )
            setup_complete = True
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))

            # Wait x seconds before trying again
            generalLogger.warning(
                f"Waiting {CybergridConfig.REACTIVE_SECONDS_UNTIL_RECONNECT_TRY} seconds " \
                "before trying the SSA setup again..."
            )
            sleep(CybergridConfig.REACTIVE_SECONDS_UNTIL_RECONNECT_TRY)

    # RECONNECT IF CONNECTION IS LOST
    while True:
        try:
            setpoint_handle(exitEvent, cybergrid_ssa)
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))

            db.session.close()

            # Wait x seconds before trying again
            generalLogger.warning(
                f"Waiting {CybergridConfig.REACTIVE_SECONDS_UNTIL_RECONNECT_TRY} seconds " \
                "before trying the SSA setup again..."
            )
            sleep(CybergridConfig.REACTIVE_SECONDS_UNTIL_RECONNECT_TRY)
