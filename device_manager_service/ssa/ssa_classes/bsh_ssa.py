import os

from ssa_utilities.ssa import SSA, KiTypeShort

from device_manager_service.ssa.ssa_config.bsh_config import BSHConfig


class BSHSSA(SSA):

    def __init__(self, ga_url, ss_email, ss_password, kb_name, kb_description, asset_id, logger):
        """SSA class initialization function.

        Args:
            ga_url (str): Generic Adapter URL
            ss_email (str): Service Store Email
            ss_password (str): Service Store Password (Use ENV VAR)
            kb_name (str): Knowledge Base name (for convenience only)
            kb_description (str): Knowledge Base description (for convenience only)
            asset_id (str): Knowledge Base ID (for identifying the KB in the KE)
        """
        super().__init__(ga_url, ss_email, ss_password, kb_name, kb_description, asset_id, logger=logger)

    
    def setup(self, ss_email: str, ss_password: str, kb_name: str, kb_description: str, asset_id: str):
        """Sequential procedures defined by the SSA implementer to fully setup the SSA (KB and KIs)

        NOTE: This function will be reused by the SSA class 
        to re-run the setup for specific scenarios, namely self-healing.
        Make sure the function only uses "register" functions.

        Args:
            ss_email (str): Service Store Email
            ss_password (str): Service Store Password (Use ENV VAR)
            kb_name (str): Knowledge Base name (for convenience only)
            kb_description (str): Knowledge Base description (for convenience only)
            asset_id (str): Knowledge Base ID (for identifying the KB in the KE)
        """

        # communicative_act_tno = {
        #     "requiredPurposes": [
        #         "https://www.tno.nl/energy/ontology/interconnect#InformPurpose"
        #     ],
        #     "satisfiedPurposes": [
        #         "https://www.tno.nl/energy/ontology/interconnect#InformPurpose"
        #     ]
        # }

        communicative_act_tno = {
            "requiredPurposes": [
                "https://w3id.org/knowledge-engine/InformPurpose"
            ],
            "satisfiedPurposes": [
                "https://w3id.org/knowledge-engine/InformPurpose"
            ]
        }

        dirname = os.path.dirname(os.path.dirname(__file__))


        # ---------------------- Register Proactive Interactions KB ---------------------- #

        # This function performs:
            # Login to Service Store
            # Register adapter in service store
            # Register smart connector in KE
        self.proactive_kb_id = self.register_ssa_smart_connect_flow(
            ss_email=ss_email,
            ss_password=ss_password,
            service_id=BSHConfig.BSH_SERVICE_ID,
            kb_name=kb_name,
            kb_description=kb_description,
            asset_id=asset_id,
            primary_url=BSHConfig.BSH_SERVICE_PRIMARY_URL
        )

        # DEVICE METADATA
        bsh_device_metadata_gp_path = os.path.join(
            dirname, "graph_patterns", "bsh", "spine_ask_device_metadata.gp"
            )
        
        self.bsh_device_metadata_ask_ki_id = self.register_ask_answer_ki(
            kb_id=self.proactive_kb_id,
            ki_type=KiTypeShort.ASK.value,
            ki_name=BSHConfig.DEVICE_METADATA_ASK_KI_NAME,
            gp_path=bsh_device_metadata_gp_path,
            communicative_act=communicative_act_tno
        )
        
        # DELAYED START
        bsh_delay_arg_gp_path = os.path.join(
            dirname, "graph_patterns", "bsh", "bsh_delay_post_arg.gp"
        )
        bsh_delay_res_gp_path = os.path.join(
            dirname, "graph_patterns", "bsh", "bsh_delay_post_res.gp"
        )

        self.bsh_delay_post_ki_id = self.register_post_react_ki(
            kb_id=self.proactive_kb_id,
            ki_type=KiTypeShort.POST.value,
            ki_name=BSHConfig.DELAY_POST_KI_NAME,
            arg_gp_path=bsh_delay_arg_gp_path,
            res_gp_path=bsh_delay_res_gp_path,
            communicative_act=communicative_act_tno
        )
        
        return
