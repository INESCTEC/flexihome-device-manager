import os

from ssa_utilities.ssa import SSA, KiTypeShort
from energy_manager_service.ssa.cybergrid.config import CybergridConfig


class PTPilotProactiveCybergridSSA(SSA):

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
            service_hash (str): Service Store given service hash
            kb_name (str): Knowledge Base name (for convenience only)
            kb_description (str): Knowledge Base description (for convenience only)
            asset_id (str): Knowledge Base ID (for identifying the KB in the KE)
        """

        communicative_act = {
            "requiredPurposes": [
                "https://w3id.org/knowledge-engine/InformPurpose"
            ],
            "satisfiedPurposes": [
                "https://w3id.org/knowledge-engine/InformPurpose"
            ]
        }

        # This function performs:
            # Login to Service Store
            # Register adapter in service store
            # Register smart connector in KE
        self.pt_pilot_proactive_kb_id = self.register_ssa_smart_connect_flow(
            ss_email=ss_email,
            ss_password=ss_password,
            service_id=CybergridConfig.CYBERGRID_SERVICE_ID,  # NOTE: Cybergrid service has "localhost" as primary KE URL
            kb_name=kb_name,
            kb_description=kb_description,
            asset_id=asset_id,
            primary_url=CybergridConfig.CYBERGRID_SERVICE_PRIMARY_URL
        )

        # ACTIVE POWER
        dirname = os.path.join(os.path.dirname(os.path.dirname(__file__)), "graph_patterns")
        arg_gp_path = os.path.join(dirname, "active_power.gp")

        self.active_power_ki_id = self.register_post_react_ki(
            kb_id=self.pt_pilot_proactive_kb_id,
            ki_type=KiTypeShort.POST.value,
            ki_name=CybergridConfig.ACTIVE_POWER_KI_NAME,
            arg_gp_path=arg_gp_path,
            res_gp_path=None,
            communicative_act=communicative_act
        )
        
        # BASELINE
        arg_gp_path = os.path.join(dirname, "baseline.gp")

        self.baseline_ki_id = self.register_post_react_ki(
            kb_id=self.pt_pilot_proactive_kb_id,
            ki_type=KiTypeShort.POST.value,
            ki_name=CybergridConfig.BASELINE_KI_NAME,
            arg_gp_path=arg_gp_path,
            res_gp_path=None,
            communicative_act=communicative_act
            )
        
        # UPPER LIMIT
        arg_gp_path = os.path.join(dirname, "upper_limit.gp")

        self.upper_limit_ki_id = self.register_post_react_ki(
            kb_id=self.pt_pilot_proactive_kb_id,
            ki_type=KiTypeShort.POST.value,
            ki_name=CybergridConfig.UPPER_LIMIT_KI_NAME,
            arg_gp_path=arg_gp_path,
            res_gp_path=None,
            communicative_act=communicative_act
            )

        # LOWER LIMIT
        arg_gp_path = os.path.join(dirname, "lower_limit.gp")
        self.lower_limit_ki_id = self.register_post_react_ki(
            kb_id=self.pt_pilot_proactive_kb_id,
            ki_type=KiTypeShort.POST.value,
            ki_name=CybergridConfig.LOWER_LIMIT_KI_NAME,
            arg_gp_path=arg_gp_path,
            res_gp_path=None,
            communicative_act=communicative_act
            )

        # SETPOINT POST
        arg_gp_path = os.path.join(dirname, "setpoint_post.gp")

        self.setpoint_post_ki_id = self.register_post_react_ki(
            kb_id=self.pt_pilot_proactive_kb_id,
            ki_type=KiTypeShort.POST.value,
            ki_name=CybergridConfig.SETPOINT_POST_KI_NAME,
            arg_gp_path=arg_gp_path,
            communicative_act=communicative_act
            )


        return
