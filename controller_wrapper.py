#this is a wrapper for all controllers to be handled properly
def handle_controller(timestamp : str,file : str, fan_mode : str):
    print(f"at time {timestamp}running {file} with fan speed in mode {fan_mode}")

