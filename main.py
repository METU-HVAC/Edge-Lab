
import asyncio
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from pathlib import Path
import uvicorn
from datetime import datetime
#wrapper function call
from controller_wrapper import handle_controller

app = FastAPI()
BASE_DIR = Path(__file__).parent
csv_file = BASE_DIR / "DB" / "Configs.CSV"


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

                # Removing empty rows
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
                file_name = last['file']
                mode_var = last['fan_mode']
                handle_controller(file_name, mode_var)

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
    app.state.bg_task = asyncio.create_task(background_loop())
    print("Background task started at startup")



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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
