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
parser.add_argument('--anime_image',   type=str, required=True, help="Path to anime character image")
parser.add_argument('--main_pose',     type=str, required=True, help="Path to main character pose image")
parser.add_argument('--main_prompt',   type=str, required=True, help="Description for main character")
parser.add_argument('--second_pose',   type=str, required=True, help="Path to second character pose template")
parser.add_argument('--second_prompt', type=str, required=True, help="Description for second character")
parser.add_argument('--output',        type=str, required=True, help="Path to save the final panel")
args = parser.parse_args()

output_image_path = args.output
_dbglog("run_panel_workflow2.py:start", "Script started", {"anime_image": args.anime_image, "output": output_image_path})

# ---- STEP 2: Setup Server and Client ID ----
server_address = os.getenv("COMFYUI_URL")
_dbglog("run_panel_workflow2.py:env", "COMFYUI_URL value", {"COMFYUI_URL": server_address or "NOT SET"})

if not server_address:
    raise RuntimeError("COMFYUI_URL environment variable is not set.")
if not server_address.startswith(("http://", "https://")):
    raise ValueError(f"Invalid COMFYUI_URL '{server_address}'. Must start with http:// or https://")

try:
    resp = requests.get(f"{server_address}/system_stats", timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"ComfyUI server returned status {resp.status_code}")
except requests.exceptions.RequestException as e:
    raise RuntimeError(f"Cannot connect to ComfyUI at {server_address}: {e}")

client_id = str(uuid.uuid4())

# ---- STEP 3: ComfyUI API Helper Functions ----
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(
        f"{server_address}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req)
        body = resp.read()
        _dbglog("run_panel_workflow2.py:queue_prompt:ok", "Prompt queued", {"status": resp.status, "body": body.decode()[:300]})
        return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:2000]
        _dbglog("run_panel_workflow2.py:queue_prompt:FAIL", "ComfyUI rejected prompt", {"status": e.code, "body": err_body})
        raise

def upload_image(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_data = f.read()
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{server_address}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    _dbglog("run_panel_workflow2.py:upload_image", "Uploaded image to ComfyUI", {"result": result, "path": filepath})
    return result["name"]

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{server_address}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen(f"{server_address}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    _dbglog("run_panel_workflow2.py:get_images:start", "Waiting for WS messages", {"prompt_id": prompt_id})

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    _dbglog("run_panel_workflow2.py:get_images:done", "Workflow execution complete", {})
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
                _dbglog("run_panel_workflow2.py:get_images:downloading", "Downloading output image", {"node_id": node_id, "filename": image['filename']})
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        if images_output:
            output_images[node_id] = images_output

    return output_images

# ---- STEP 4: Load Workflow JSON and Upload Images ----
workflow_path = os.path.join(BASE_DIR, "character2.json")
_dbglog("run_panel_workflow2.py:workflow_json", "Loading workflow", {"path": workflow_path, "exists": os.path.exists(workflow_path)})
with open(workflow_path, "r", encoding="utf-8") as f:
    prompt = json.load(f)

anime_image_name  = upload_image(args.anime_image)
main_pose_name    = upload_image(args.main_pose)
second_pose_name  = upload_image(args.second_pose)

prompt["23"]["inputs"]["image"] = anime_image_name
prompt["27"]["inputs"]["image"] = main_pose_name
prompt["37"]["inputs"]["text"]  = args.main_prompt
prompt["40"]["inputs"]["image"] = second_pose_name
prompt["43"]["inputs"]["text"]  = args.second_prompt

# ---- STEP 5: Connect WebSocket, Run Workflow ----
ws_address = server_address.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
_dbglog("run_panel_workflow2.py:connecting_ws", "Connecting WebSocket", {"ws_address": ws_address})
ws = websocket.WebSocket()
ws.connect(f"{ws_address}/ws?clientId={client_id}")
_dbglog("run_panel_workflow2.py:ws_connected", "WebSocket connected", {})
images = get_images(ws, prompt)
ws.close()
_dbglog("run_panel_workflow2.py:workflow_done", "Workflow completed", {"num_nodes": len(images)})

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
            _dbglog("run_panel_workflow2.py:saved", "Saved output image", {"path": output_image_path, "size": len(image_data)})
            saved = True
            break
    if saved:
        break

if not saved:
    raise RuntimeError("No output image was generated or retrieved.")
