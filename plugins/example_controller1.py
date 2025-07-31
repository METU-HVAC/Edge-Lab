#this file is used as an example controllers so others can adjust their controllers to fit this schema
def run_controller(timestamp,t_in, t_out, fan_mode):
     print(f"Hello from controller 1 Timestamp: {timestamp}, Indoor: {t_in}, Outdoor: {t_out}, Fan mode: {fan_mode}")
     return "CLOSED"
