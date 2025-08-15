
import asyncio
import json
import paho.mqtt.client as mqtt

MQTT_HOST = "31.207.86.251"
MQTT_PORT = 1886
TOPIC_CFG = "A403-RM"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("---MQTT connected---")
        client.subscribe(TOPIC_CFG)
        print(f"----Subscribed: {TOPIC_CFG}-----")
    else:
        print(f"****MQTT connect failed rc={rc}****")

def on_message(client, userdata, msg):
    app = userdata["app"]
    loop = userdata["loop"]
    topic = msg.topic
    text = msg.payload.decode("utf-8", errors="replace")

    async def handle():
        try:
            handler = getattr(app.state, "on_mqtt_message", None)
            if handler is None:
                print("⚠️ app.state.on_mqtt_message is not set; ignoring message")
                return
            await handler(topic, text)
        except Exception as e:
            print(f"Error in MQTT async handler: {e}")

    loop.call_soon_threadsafe(asyncio.create_task, handle())

def make_mqtt_client(app, loop):

    client = mqtt.Client()
    client.user_data_set({"app": app, "loop": loop})
    client.on_connect = on_connect
    client.on_message = on_message
    return client

def start_mqtt(client):
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    print("MQTT loop started (threaded)")

def stop_mqtt(client):
    try:
        client.disconnect()
    except Exception:
        pass
    try:
        client.loop_stop()
    except Exception:
        pass
    print("MQTT loop stopped")
