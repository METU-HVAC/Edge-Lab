#this is a wrapper for all controllers to be handled properly
import importlib
import importlib.util
import os
from plugins.drivers import set_fan_mode, get_temps


def handle_controller(timestamp: str, file: str, fan_mode: str):
   
    print(f"***At time {timestamp} running {file} with fan speed in mode {fan_mode}***")
    try:
        file_path = os.path.join("plugins", file)
        module_name = file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Controller file '{file_path}' not found")
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'run_controller'):
            # Call the function and get the action
            t_in,t_out = get_temps()
            action = module.run_controller(timestamp,t_in, t_out, fan_mode)
            print(f"Controller returned action: {action}")
            set_fan_mode(action)
            return action
        else:
            raise AttributeError(f"Function 'run_controller' not found in {file}")
            
    except Exception as e:
        print(f"Error loading or executing controller '{file}': {str(e)}")
        return "error"


