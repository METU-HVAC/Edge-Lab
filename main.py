

import asyncio
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from pathlib import Path
import uvicorn

app = FastAPI()
BASE_DIR = Path(__file__).parent
csv_file = BASE_DIR / "DB" / "Configs.CSV"


async def background_loop():
# I have setup this code routine so we dont need to restart pi whenever we update params
    try:
        while True:
            if not os.path.exists(csv_file):
                print("⚠️CSV not found, waiting...")
                await asyncio.sleep(1)
                continue

            df = pd.read_csv(csv_file)
            if df.empty:
                print("⚠️CSV is empty, waiting...")
                await asyncio.sleep(1)
                continue

            last = df.iloc[-1].to_dict()
            print("Background loop running with config:", last)
            # --- I will put python controller wrapper here ---
            await asyncio.sleep(5)  # temporary for now 
    except asyncio.CancelledError:
        print("----Background loop cancelled----")
        raise


@app.on_event("startup")
async def on_startup():
    app.state.bg_task = asyncio.create_task(background_loop())
    print("Background task started at startup")


@app.post("/receive-json")
async def receive_json(data: dict):
    """
    1) Append incoming JSON to CSV
    2) Cancel & restart the background_loop so it picks up new params
    """
    # handling local db save below
    header = not os.path.exists(csv_file)
    df = pd.DataFrame([data])
    df.to_csv(csv_file, mode="a", header=header, index=False)
    print("Saved payload to CSV:", data)

    # cancel current wrapper function and restarting with new params
    task = app.state.bg_task
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    app.state.bg_task = asyncio.create_task(background_loop())
    print("!Background task restarted with new config")

    return {"status": "saved and background restarted"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
