# Required Import
from rcl_interfaces.msg import SetParametersResult

# 1. Registration (Place inside your __init__ method)
self.add_on_set_parameters_callback(self.parameter_callback)

# 2. Generic Callback Method (Place inside your Node class)
def parameter_callback(self, params):
    result = SetParametersResult()
    result.successful = True
    result.reason = "Success"

    for param in params:
        # Dynamically updates self.<parameter_name>_ with the new value
        attr_name = f"{param.name}_"
        setattr(self, attr_name, param.value)
        
        self.get_logger().info(f"Parameter '{param.name}' updated to: {param.value}")
                
    return result