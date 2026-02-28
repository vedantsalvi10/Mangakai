import argparse
import websocket
import uuid
import json
import urllib.request
import urllib.parse
import urllib.error
import os
import requests
import time as _time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _dbglog(loc, msg, data=None):
    lp = os.path.join(BASE_DIR, "debug-3238e9.log")
    with open(lp, "a") as f:
        f.write(json.dumps({
            "sessionId": "3238e9", "location": loc, "message": msg,
            "data": data or {}, "timestamp": int(_time.time() * 1000)
        }) + "\n")

# ---- STEP 1: Parse CLI Arguments ----
parser = argparse.ArgumentParser()
parser.add_argument('--prompt', type=str, required=True, help="Visual prompt for the group/scene")
parser.add_argument('--output', type=str, required=True, help="Path to save the final panel")
args = parser.parse_args()

output_image_path = args.output
_dbglog("run_group_workflow.py:start", "Script started", {"output": output_image_path})

# ---- STEP 2: Setup Server and Client ID ----
server_address = os.getenv("COMFYUI_URL")
_dbglog("run_group_workflow.py:env", "COMFYUI_URL value", {"COMFYUI_URL": server_address or "NOT SET"})

if not server_address:
    raise RuntimeError("COMFYUI_URL environment variable is not set.")
if not server_address.startswith(("http://", "https://")):
    raise ValueError(f"Invalid COMFYUI_URL '{server_address}'. Must start with http:// or https://")
server_address = server_address.rstrip("/")

_runpod_key = (os.getenv("RUNPOD_API_KEY") or "").strip()
_comfy_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}
if _runpod_key:
    _comfy_headers["Authorization"] = f"Bearer {_runpod_key}"
    _dbglog("run_group_workflow.py:runpod", "RunPod API key set", {})

try:
    resp = requests.get(f"{server_address}/system_stats", timeout=5, headers=_comfy_headers)
    if resp.status_code != 200:
        raise RuntimeError(f"ComfyUI server returned status {resp.status_code}")
except requests.exceptions.RequestException as e:
    raise RuntimeError(f"Cannot connect to ComfyUI at {server_address}: {e}")

client_id = str(uuid.uuid4())

# ---- STEP 3: ComfyUI API Helper Functions ----
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    headers = {**_comfy_headers, "Content-Type": "application/json"}
    req = urllib.request.Request(
        f"{server_address}/prompt",
        data=data,
        headers=headers,
    )
    try:
        resp = urllib.request.urlopen(req)
        body = resp.read()
        _dbglog("run_group_workflow.py:queue_prompt:ok", "Prompt queued", {"status": resp.status, "body": body.decode()[:300]})
        return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:2000]
        _dbglog("run_group_workflow.py:queue_prompt:FAIL", "ComfyUI rejected prompt", {"status": e.code, "body": err_body})
        raise

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    req = urllib.request.Request(f"{server_address}/view?{url_values}", headers=_comfy_headers)
    with urllib.request.urlopen(req) as response:
        return response.read()

def get_history(prompt_id):
    req = urllib.request.Request(f"{server_address}/history/{prompt_id}", headers=_comfy_headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    _dbglog("run_group_workflow.py:get_images:start", "Waiting for WS messages", {"prompt_id": prompt_id})

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    _dbglog("run_group_workflow.py:get_images:done", "Workflow execution complete", {})
                    break

    history = get_history(prompt_id)[prompt_id]
    output_images = {}
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                if image.get('type') == 'temp':
                    continue
                _dbglog("run_group_workflow.py:get_images:downloading", "Downloading output image", {"node_id": node_id, "filename": image['filename']})
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        if images_output:
            output_images[node_id] = images_output

    return output_images

# ---- STEP 4: Load Workflow JSON and Inject Prompt ----
workflow_path = os.path.join(BASE_DIR, "group_character.json")
_dbglog("run_group_workflow.py:workflow_json", "Loading workflow", {"path": workflow_path, "exists": os.path.exists(workflow_path)})
with open(workflow_path, "r", encoding="utf-8") as f:
    workflow = json.load(f)

workflow["1"]["inputs"]["text"] = args.prompt

# ---- STEP 5: Connect WebSocket, Run Workflow ----
ws_address = server_address.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
_dbglog("run_group_workflow.py:connecting_ws", "Connecting WebSocket", {"ws_address": ws_address})
ws = websocket.WebSocket()
ws.connect(f"{ws_address}/ws?clientId={client_id}")
_dbglog("run_group_workflow.py:ws_connected", "WebSocket connected", {})
images = get_images(ws, workflow)
ws.close()
_dbglog("run_group_workflow.py:workflow_done", "Workflow completed", {"num_nodes": len(images)})

# ---- STEP 6: Save Output Image ----
saved = False
for node_id in images:
    for image_data in images[node_id]:
        if image_data:
            out_dir = os.path.dirname(output_image_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_image_path, 'wb') as f:
                f.write(image_data)
            _dbglog("run_group_workflow.py:saved", "Saved output image", {"path": output_image_path, "size": len(image_data)})
            saved = True
            break
    if saved:
        break

if not saved:
    raise RuntimeError("No output image was generated or retrieved.")
