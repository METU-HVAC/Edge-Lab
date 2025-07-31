from fastapi import FastAPI
import pandas as pd
import uvicorn



app = FastAPI()
csv_file = "data.csv"

@app.post("/receive-json")
def receive_json(data: dict):
    print("Received payload:", data)
    df = pd.DataFrame([data])
    df.to_csv(csv_file, mode='a', header=not pd.io.common.file_exists(csv_file), index=False)
    print("Write complete")
    return {"status": "saved"}

def process_last_row():
    df = pd.read_csv(csv_file)
    last_row = df.iloc[-1].to_dict()
    print("Last row data:", last_row)
    
    
    # result = controller_wrapper(**last_row)
    
    return last_row

@app.on_event("startup")
def process_last():
    return process_last_row()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)