import threading, traceback
from time import sleep

from device_manager_service.ssa.ssa_classes.bsh_ssa_react import BSHSSAReact
from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig
from device_manager_service.ssa.ssa_classes.whirlpool_ssa_react import WhirlpoolSSAReact
from device_manager_service.ssa.ssa_config.wp_config import WPConfig

from device_manager_service.ssa.whirlpool.wp_pp_handle import wp_power_profile_handle
from device_manager_service.ssa.bosch_miele.bsh_pp_handle import bsh_pp_handle

from device_manager_service import Config, generalLogger

from sqlalchemy.exc import OperationalError, DatabaseError


# BSH SSA
# bsh_ssa = BSHSSA(
#     ga_url=BSHConfig.GENERIC_ADAPTER_URL,
#     ss_email=BSHConfig.USER_EMAIL,
#     ss_password=BSHConfig.USER_PASSWORD,
#     kb_name=BSHConfig.KB_NAME,
#     kb_description=BSHConfig.KB_DESCRIPTION,
#     asset_id=BSHConfig.KB_ASSET_ID,
#     logger=generalLogger
# )


class SSAThreads:
    def __init__(self):
        self.exitEvent = threading.Event()

        self.threads = {}

        if Config.WP_THREAD:
            # name = 'WPPowerProfileHandleThread'
            # self.threads[name] = threading.Thread(name=name, target=wp_thread_main, args=(self.exitEvent,))
            name = 'WPPowerProfileHandleReactThread'
            self.threads[name] = threading.Thread(name=name, target=wp_react_thread_main, args=(self.exitEvent,))
        
        if Config.BSH_THREAD:
            # name = 'BSHPowerProfileHandleThread'
            # self.threads[name] = threading.Thread(name=name, target=bsh_thread_main, args=(self.exitEvent,))
            name = 'BSHPowerProfileHandleReactThread'
            self.threads[name] = threading.Thread(name=name, target=bsh_react_thread_main, args=(self.exitEvent,))

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


# def bsh_thread_main(exitEvent):
#     setup_complete = False
#     while not setup_complete:
#         try:
#             bsh_ssa = BSHSSA(
#                 ga_url=BSHConfig.GENERIC_ADAPTER_URL,
#                 ss_email=BSHConfig.USER_EMAIL,
#                 ss_password=BSHConfig.USER_PASSWORD,
#                 kb_name=BSHConfig.KB_NAME,
#                 kb_description=BSHConfig.KB_DESCRIPTION,
#                 asset_id=BSHConfig.KB_ASSET_ID,
#                 logger=generalLogger
#             )
#             setup_complete = True
#         except Exception as e:
#             traceback.print_exc()
#             generalLogger.error(repr(e))

#             # Wait x seconds before trying again
#             generalLogger.warning(
#                 f"Waiting {BSHConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
#                 "before trying the SSA setup again..."
#             )
#             sleep(BSHConfig.SECONDS_UNTIL_RECONNECT_TRY)


#     # RECONNECT IF CONNECTION IS LOST
#     while True:
#         try:
#             bsh_pp_handle(exitEvent, bsh_ssa)
#         except Exception as e:
#             traceback.print_exc()
#             generalLogger.error(repr(e))

#             # Wait x seconds before trying again
#             generalLogger.warning(
#                 f"Waiting {BSHConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
#                 "before trying the SSA setup again..."
#             )
#             sleep(BSHConfig.SECONDS_UNTIL_RECONNECT_TRY)

def bsh_react_thread_main(exitEvent):
    setup_complete = False
    while not setup_complete:
        try:
            bsh_ssa = BSHSSAReact(
                ga_url=BSHConfig.GENERIC_ADAPTER_URL,
                ss_email=BSHConfig.USER_EMAIL,
                ss_password=BSHConfig.USER_PASSWORD,
                kb_name=BSHConfig.KB_NAME,
                kb_description=BSHConfig.KB_DESCRIPTION,
                asset_id=BSHConfig.KB_REACT_ASSET_ID,
                logger=generalLogger
            )
            setup_complete = True
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))

            # Wait x seconds before trying again
            generalLogger.warning(
                f"Waiting {BSHConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
                "before trying the SSA setup again..."
            )
            sleep(BSHConfig.SECONDS_UNTIL_RECONNECT_TRY)


    # RECONNECT IF CONNECTION IS LOST
    while True:
        try:
            bsh_pp_handle(exitEvent, bsh_ssa)
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))

            # Wait x seconds before trying again
            generalLogger.warning(
                f"Waiting {BSHConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
                "before trying the SSA setup again..."
            )
            sleep(BSHConfig.SECONDS_UNTIL_RECONNECT_TRY)

# def wp_thread_main(exitEvent):
#     setup_complete = False
#     while not setup_complete:
#         try:
#             whirlpool_ssa = WhirlpoolSSA(
#                 ga_url=WPConfig.GENERIC_ADAPTER_GLOBAL_URL,
#                 ss_email=WPConfig.USER_EMAIL,
#                 ss_password=WPConfig.USER_PASSWORD,
#                 kb_name=WPConfig.KB_NAME,
#                 kb_description=WPConfig.KB_DESCRIPTION,
#                 asset_id=WPConfig.KB_ASSET_ID,
#                 logger=generalLogger
#             )
#             setup_complete = True
#         except Exception as e:
#             traceback.print_exc()
#             generalLogger.error(repr(e))

#             # Wait x seconds before trying again
#             generalLogger.warning(
#                 f"Waiting {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
#                 "before trying the SSA setup again..."
#             )
#             sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)


#     # RECONNECT IF CONNECTION IS LOST
#     while True:
#         try:
#             wp_power_profile_handle(exitEvent, whirlpool_ssa)
#         except Exception as e:
#             traceback.print_exc()
#             generalLogger.error(repr(e))
        
#             # Wait x seconds before trying again
#             generalLogger.warning(
#                 f"Waiting {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
#                 "before trying the SSA setup again..."
#             )
#             sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)

def wp_react_thread_main(exitEvent):
    setup_complete = False
    while not setup_complete:
        try:
            whirlpool_ssa = WhirlpoolSSAReact(
                ga_url=WPConfig.GENERIC_ADAPTER_PT_URL,
                ss_email=WPConfig.USER_EMAIL,
                ss_password=WPConfig.USER_PASSWORD,
                kb_name=WPConfig.KB_NAME,
                kb_description=WPConfig.KB_DESCRIPTION,
                asset_id=WPConfig.KB_REACT_ASSET_ID,
                logger=generalLogger
            )
            setup_complete = True
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))

            # Wait x seconds before trying again
            generalLogger.warning(
                f"Waiting {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
                "before trying the SSA setup again..."
            )
            sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)


    # RECONNECT IF CONNECTION IS LOST
    while True:
        try:
            wp_power_profile_handle(exitEvent, whirlpool_ssa)
        except Exception as e:
            traceback.print_exc()
            generalLogger.error(repr(e))
        
            # Wait x seconds before trying again
            generalLogger.warning(
                f"Waiting {WPConfig.SECONDS_UNTIL_RECONNECT_TRY} seconds " \
                "before trying the SSA setup again..."
            )
            sleep(WPConfig.SECONDS_UNTIL_RECONNECT_TRY)
