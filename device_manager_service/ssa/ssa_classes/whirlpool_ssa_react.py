import os

from ssa_utilities.ssa import SSA, KiTypeShort

from device_manager_service.ssa.ssa_config.wp_config import WPConfig


class WhirlpoolSSAReact(SSA):

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

        # ---------------------- Register INESC TEC SIDE SERVICE (INESC TEC as server) ---------------------- #

        self.reactive_kb_id = self.register_ssa_smart_connect_flow(
            ss_email=ss_email,
            ss_password=ss_password,
            service_id=WPConfig.INESCTEC_WP_SERVICE_ID,
            kb_name=kb_name,
            kb_description=kb_description,
            asset_id=asset_id,
            primary_url=WPConfig.INESCTEC_WP_SERVICE_PRIMARY_URL
        )

         # Access parent directory
        dirname = os.path.dirname(os.path.dirname(__file__))

        communicative_act = {
            "requiredPurposes": [
                "https://w3id.org/knowledge-engine/InformPurpose"
            ],
            "satisfiedPurposes": [
                "https://w3id.org/knowledge-engine/InformPurpose"
            ]
        }
        
        # POWER PROFILE
        wp_pp_arg_gp_path = os.path.join(
            dirname, "graph_patterns", "whirlpool", "wp_pp_argument.gp"
            )
        wp_pp_res_gp_path = os.path.join(
            dirname, "graph_patterns", "whirlpool", "wp_pp_result.gp"
            )
        
        self.wp_react_pp_ki_id = self.register_post_react_ki(
            kb_id=self.reactive_kb_id,
            ki_type=KiTypeShort.REACT.value, 
            ki_name=WPConfig.PP_REACT_KI_NAME,
            arg_gp_path=wp_pp_arg_gp_path,
            res_gp_path=wp_pp_res_gp_path,
            communicative_act=communicative_act
            )
        
        return
