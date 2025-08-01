# Edge Wrapper

A lightweight Python edge-system wrapper that receives configuration over HTTPS (FastAPI), persists it to disk, and exposes your sensors & actuators to dynamically-loaded controller plugins.

---

## Features

- **HTTPS FastAPI server**  
  Hosts a `/config` endpoint to receive full JSON documents.

- **Config persistence**  
  Saves each incoming JSON payload as a line-delimited file for auditing.

- **Dynamic plugin architecture**  
  Drop your controller logic into the `plugins/` folder—no need to modify core code.

- **Driver abstraction**  
  A single `drivers.py` file to unify all low-level sensor & actuator calls.

---

## Project Structure
**Requirements**
1. **Create a virtual environment**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt


