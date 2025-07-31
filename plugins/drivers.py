#this file is used to handle hardware drivers for fan and temp sensors for now
import RPi.GPIO as GPIO
from w1thermsensor import W1ThermSensor


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RELAY1_PIN, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(RELAY2_PIN, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(RELAY3_PIN, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(RELAY4_PIN, GPIO.OUT, initial = GPIO.HIGH)

# Fan kontrol fonksiyonu
def set_fan_mode(mode):
    RELAY1_PIN = 23  # Fan yön kontrol
    RELAY2_PIN = 24  # Panjur kontrol
    RELAY3_PIN = 25  # Fan Kademe 1 (MOD1)
    RELAY4_PIN = 27  # Fan Kademe 2 (MOD2)

    current_fan_mode = mode
    print(f"Yeni fan modu: {mode}")

    GPIO.output(RELAY1_PIN, GPIO.HIGH)  # Yönn hep aynı kabul edildi

    if mode == "MOD1":
        GPIO.output(RELAY2_PIN, GPIO.LOW)
        GPIO.output(RELAY3_PIN, GPIO.LOW)
        GPIO.output(RELAY4_PIN, GPIO.HIGH)
    elif mode == "MOD2":
        GPIO.output(RELAY2_PIN, GPIO.LOW)
        GPIO.output(RELAY3_PIN, GPIO.HIGH)
        GPIO.output(RELAY4_PIN, GPIO.LOW)
    elif mode == "NAT_FLOW":
        GPIO.output(RELAY2_PIN, GPIO.LOW)
        GPIO.output(RELAY3_PIN, GPIO.HIGH)
        GPIO.output(RELAY4_PIN, GPIO.HIGH)
    elif mode == "CLOSED":
        GPIO.output(RELAY2_PIN, GPIO.HIGH)
        GPIO.output(RELAY3_PIN, GPIO.HIGH)
        GPIO.output(RELAY4_PIN, GPIO.HIGH)
    else :
        GPIO.output(RELAY2_PIN, GPIO.HIGH)
        GPIO.output(RELAY3_PIN, GPIO.HIGH)
        GPIO.output(RELAY4_PIN, GPIO.HIGH)

def get_temps():
    tin = sensor_indoor.get_temperature()
    tout = sensor_outdoor.get_temperature() + 2            
    print(f"from drivers.py İÇ VE DIŞ sıcaklık:",tin, tout)
    return tin, tout
