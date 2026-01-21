import json

from device_manager_service import generalLogger


def process_whirlpool_binding_set(binding_set):

    processed_binding_set = []
    if len(binding_set) != 0:
        
        for binding in binding_set:
            binding_object = {}

            for key, value in binding.items():
                value_schema = value.split("^^")
                
                if len(value_schema) > 1:
                    binding_object[key] = value_schema[0].replace("\"", "")
            
            processed_binding_set.append(binding_object)

        generalLogger.debug(
            f"Converted answer binding set to:\n" \
            f"{processed_binding_set}\n"
            )
    
    return processed_binding_set


def process_bsh_binding_set(binding_set):
    
    processed_binding_set = []
    if len(binding_set) != 0:

        for binding in binding_set:
            binding_object = {}

            for key, value in binding.items():
                binding_object[key] = value.replace("\"", "")
            
            processed_binding_set.append(binding_object)

        # generalLogger.debug(
        #         f"Converted answer binding set to (first binding in array):\n" \
        #         f"{json.dumps(processed_binding_set[0], indent=4)}\n"
        #         )
    
    else:
        generalLogger.info("Binding set empty...")
    
    return processed_binding_set