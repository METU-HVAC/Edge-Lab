#this is a wrapper for all controllers to be handled properly
import importlib
import importlib.util
import os
from plugins.drivers import set_fan_mode, get_temps
 === Provide the "other JSON" here ===
 fan_mode_global = "CLOSED"

def get_runtime_json() -> dict:
    """
    Your function that fetches/creates the additional JSON
    (from sensors, a cache, filesystem, DB, wherever).
    Must return a dict. Replace this stub with your logic.
    """
    global fan_mode_global
    t_in,t_out = get_temps()

    return {
        "tin": t_in,
        "tout": t_out,
        "fan_mode": fan_mode_global,
        "ts": datetime.now().isoformat(timespec="seconds")
    }

def merge_dicts(a: dict, b: dict, prefer="mqtt") -> dict:

    if prefer == "mqtt":
        return {**b, **a}  # a overwrites b on same keys
    else:
        return {**a, **b}  # b overwrites a on same keys


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
            global fan_mode_global 
            fan_mode_global = fan_mode
            return action
        else:
            raise AttributeError(f"Function 'run_controller' not found in {file}")
            
    except Exception as e:
        print(f"Error loading or executing controller '{file}': {str(e)}")
        return "error"


