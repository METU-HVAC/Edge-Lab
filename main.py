
from fastapi import FastAPI, HTTPException
from pathlib import Path
import uvicorn
import RPi.GPIO as GPIO
from datetime import datetime
import asyncio, os, json, pandas as pd, zmq, zmq.asyncio

#custom fucntion imports from my onw files
from controller_wrapper import handle_controller
from mqtt_src.mqtt_handler import make_mqtt_client, start_mqtt, stop_mqtt, TOPIC_CFG

# --- ZMQ settings ---
ZMQ_ENDPOINT = "tcp://127.0.0.1:5555"  # change if needed
ZMQ_TOPIC    = "edge/out"               # the topic you want to publish on

#Handling GPIOs to prevent switching on multiple relays and damaging fan
# Röle Pinleri
RELAY1_PIN = 23  # Fan yön kontrol
RELAY2_PIN = 24  # Panjur kontrol
RELAY3_PIN = 25  # Fan Kademe 1 (MOD1)
RELAY4_PIN = 27  # Fan Kademe 2 (MOD2)

# GPIO Ayarları
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RELAY1_PIN, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(RELAY2_PIN, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(RELAY3_PIN, GPIO.OUT, initial = GPIO.HIGH)
GPIO.setup(RELAY4_PIN, GPIO.OUT, initial = GPIO.HIGH)


app = FastAPI()
BASE_DIR = Path(__file__).parent
csv_file = BASE_DIR / "DB" / "Configs.CSV"
#-------------ASYNC hanndeler for my mqtt-------------
async def on_mqtt_message(topic: str, text: str):
    print(f"[MQTT] {topic}: {text}")

    if topic == "A403-RM":
        try:
            mqtt_data = json.loads(text)
        except json.JSONDecodeError:
            print("*********Invalid JSON on MQTT; ignoring*********"); return
        if not isinstance(mqtt_data, dict):
            print("*********8MQTT payload not an object; ignoring"********); return

        try:
            extra = get_runtime_json() #will declare later
            if not isinstance(extra, dict):
                print("********get_runtime_json() did not return dict; ignoring*******"); return
        except Exception as e:
            print(f"*********get_runtime_json() failed: {e}"***********); return

        merged = merge_dicts(mqtt_data, extra, prefer="mqtt")
        merged.setdefault("merged_at", datetime.now().isoformat(timespec="seconds"))
        merged.setdefault("source", "mqtt+runtime")

        # 4) Publish via ZeroMQ PUB )
        try:
            msg = json.dumps(merged, ensure_ascii=False).encode("utf-8")
            # Send as multipart: topic frame then payload frame
            await app.state.zmq_pub.send_multipart([ZMQ_TOPIC.encode(), msg])
            print(f"[ZMQ PUB] topic={ZMQ_TOPIC} bytes={len(msg)}")
        except Exception as e:
            print(f"********ZMQ publish failed: {e}*********")
        return


def write_new_entry(timestamp, new_data_dict, csv_file):
    try:
        new_data_dict['timestamp'] = timestamp
        new_row = pd.DataFrame([new_data_dict])

        if os.path.exists(csv_file):
            existing_df = pd.read_csv(csv_file)
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        else:
            updated_df = new_row

        #Write back 
        updated_df.to_csv(csv_file, index=False)
        print(f"Entry saved to {csv_file}")

    except Exception as e:
        print(f"Error writing to CSV: {e}")

async def background_loop():
    """
    Background loop that monitors CSV file and processes the latest configuration
    """
    try:
        while True:
            if not os.path.exists(csv_file):
                print("⚠️ CSV not found, waiting...")
                await asyncio.sleep(1)
                continue

            try:
                df = pd.read_csv(csv_file)
                print(f"CSV loaded. Shape: {df.shape}, Columns: {list(df.columns)}")

                # Check for empty
                if df.empty or len(df) == 0:
                    print("⚠️ CSV is empty, waiting...")
                    await asyncio.sleep(1)
                    continue

                
                df = df.dropna(how='all')

                if df.empty:
                    print("⚠️ CSV contains only empty rows, waiting...")
                    await asyncio.sleep(1)
                    continue

                # Get the last row
                last = df.iloc[-1].to_dict()

                # Remove NaN values from the dictionary
                last = {k: v for k, v in last.items() if pd.notna(v)}

                print("Background loop running with config:", last)
                timestamps = last['timestamp']
                file_name = last['file']
                mode_var = last['fan_mode']
                handle_controller(timestamps,file_name, mode_var)

            except pd.errors.EmptyDataError:
                print("⚠️ CSV file is empty or has no data, waiting...")
                await asyncio.sleep(1)
                continue

            # Pause before the next iteration
            await asyncio.sleep(5)

    except asyncio.CancelledError:
        print("---- Background loop cancelled ----")
        raise

@app.on_event("startup")
async def on_startup():
    #----this for config handling
    app.state.bg_task = asyncio.create_task(background_loop())
    print("Background config task started at startup")

    # Make ZMQ PUB socket (async)
    app.state.zmq_ctx = zmq.asyncio.Context.instance()
    app.state.zmq_pub = app.state.zmq_ctx.socket(zmq.PUB)
    # For PUB, a tiny sleep after bind/connect can help subscribers attach before first send
    app.state.zmq_pub.bind(ZMQ_ENDPOINT)   # or .connect(...) depending on your topology
    print(f"ZMQ PUB bound at {ZMQ_ENDPOINT}")

    # Expose async hook for mqtt_task.py
    app.state.on_mqtt_message = on_mqtt_message

    # Create and start the Paho client (from your mqtt_task.py)
    loop = asyncio.get_running_loop()
    from mqtt_src.mqtt_handler import make_mqtt_client, start_mqtt
    client = make_mqtt_client(app, loop)
    app.state.mqtt_client = client
    start_mqtt(client)



@app.post("/receive-json")
async def receive_json(data: dict):

    try:
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        write_new_entry(timestamp, data, csv_file)
        print("!Saved payload to CSV:", data)
        
        task = getattr(app.state, 'bg_task', None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        app.state.bg_task = asyncio.create_task(background_loop())
        print("Background task restarted with new config")
        
        return {"status": "saved and background restarted"}
        
    except Exception as e:
        print(f"----Error in receive_json: {e}----")
        return {"status": "error", "message": str(e)}

@app.on_event("shutdown")
async def on_shutdown():
    # Stop MQTT thread
    from mqtt_src.mqtt_handler import stop_mqtt
    client = getattr(app.state, "mqtt_client", None)
    if client: stop_mqtt(client)

    # Close ZMQ
    pub = getattr(app.state, "zmq_pub", None)
    if pub:
        try: pub.close(0)
        except Exception: pass
    ctx = getattr(app.state, "zmq_ctx", None)
    if ctx:
        try: ctx.term()
        except Exception: pass

    # Stop background task if you want
    t = getattr(app.state, "bg_task", None)
    if t:
        t.cancel()
        try: await t
        except asyncio.CancelledError: pass

    print("Shutdown complete.")
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
