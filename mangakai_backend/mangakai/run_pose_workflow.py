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

def _basename_any_sep(p: str) -> str:
    # ComfyUI model dropdowns use basenames; workflows exported on Windows can contain backslashes/subfolders.
    # Normalize both "foo/bar/baz" and "foo\\bar\\baz" to "baz".
    if not isinstance(p, str):
        return p
    p = p.replace("\\", "/")
    return p.split("/")[-1]

def _normalize_controlnet_names(prompt: dict) -> None:
    # Fix common workflow export issue: ControlNetLoader.inputs.control_net_name includes subfolders (e.g. "1.5\\file.safetensors")
    for node in (prompt or {}).values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") != "ControlNetLoader":
            continue
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        if "control_net_name" in inputs:
            inputs["control_net_name"] = _basename_any_sep(inputs["control_net_name"])

def _dbglog(loc, msg, data=None):
    lp = os.path.join(BASE_DIR, "debug-3238e9.log")
    with open(lp, "a") as f:
        f.write(json.dumps({
            "sessionId": "3238e9", "location": loc, "message": msg,
            "data": data or {}, "timestamp": int(_time.time() * 1000)
        }) + "\n")

# ---- STEP 1: Parse CLI Arguments ----
parser = argparse.ArgumentParser()
parser.add_argument('--character', type=str, required=True, help="Path to animefied image")
parser.add_argument('--pose',      type=str, required=True, help="Path to pose template image")
parser.add_argument('--prompt',    type=str, required=True, help="Positive prompt for the pose")
parser.add_argument('--output',    type=str, required=True, help="Path to save the final image")
args = parser.parse_args()

output_image_path = args.output
_dbglog("run_pose_workflow.py:start", "Script started", {"character": args.character, "pose": args.pose, "output": output_image_path})

# ---- STEP 2: Setup Server and Client ID ----
server_address = os.getenv("COMFYUI_URL")
_dbglog("run_pose_workflow.py:env", "COMFYUI_URL value", {"COMFYUI_URL": server_address or "NOT SET"})

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
    _dbglog("run_pose_workflow.py:runpod", "RunPod API key set", {})

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
        _dbglog("run_pose_workflow.py:queue_prompt:ok", "Prompt queued", {"status": resp.status, "body": body.decode()[:300]})
        return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:2000]
        _dbglog("run_pose_workflow.py:queue_prompt:FAIL", "ComfyUI rejected prompt", {"status": e.code, "body": err_body})
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
    headers = {**_comfy_headers, "Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(
        f"{server_address}/upload/image",
        data=body,
        headers=headers,
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    _dbglog("run_pose_workflow.py:upload_image", "Uploaded image to ComfyUI", {"result": result, "path": filepath})
    return result["name"]

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
    wait_start = _time.time()
    _dbglog("run_pose_workflow.py:get_images:start", "Waiting for WS messages", {"prompt_id": prompt_id})

    # ComfyUI may send executing(node=null) at start and at end. Ignore the first node=null if it
    # happens within 2s (spurious "execution started"); then treat the next as real completion.
    seen_node_executing = False
    min_wait = 2.0
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data.get('prompt_id') != prompt_id:
                    continue
                if data.get('node') is not None:
                    seen_node_executing = True
                    continue
                # node is None -> completion signal
                elapsed = _time.time() - wait_start
                if not seen_node_executing and elapsed < min_wait:
                    continue  # ignore very early null (likely "execution started" not "done")
                _dbglog("run_pose_workflow.py:get_images:done", "Workflow execution complete", {"elapsed": round(elapsed, 2), "seen_node_executing": seen_node_executing})
                break

    history = get_history(prompt_id)[prompt_id]
    output_images = {}
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                # Include both "output" and "temp" — ComfyUI often returns SaveImage as temp
                _dbglog("run_pose_workflow.py:get_images:downloading", "Downloading output image", {"node_id": node_id, "filename": image['filename'], "type": image.get('type')})
                image_data = get_image(image['filename'], image.get('subfolder', ''), image.get('type', 'output'))
                images_output.append(image_data)
        if images_output:
            output_images[node_id] = images_output

    return output_images

# ---- STEP 4: Load Workflow JSON and Upload Images ----
workflow_path = os.path.join(BASE_DIR, "poses (1).json")
_dbglog("run_pose_workflow.py:workflow_json", "Loading workflow", {"path": workflow_path, "exists": os.path.exists(workflow_path)})
with open(workflow_path, "r", encoding="utf-8") as f:
    prompt = json.load(f)

_normalize_controlnet_names(prompt)

character_name = upload_image(args.character)
pose_name_on_server = upload_image(args.pose)

prompt["6"]["inputs"]["text"]  = args.prompt
prompt["9"]["inputs"]["image"]  = pose_name_on_server
prompt["15"]["inputs"]["image"] = character_name

# ---- STEP 5: Connect WebSocket, Run Workflow ----
ws_address = server_address.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
_dbglog("run_pose_workflow.py:connecting_ws", "Connecting WebSocket", {"ws_address": ws_address})
ws = websocket.WebSocket()
ws.settimeout(330)  # 5.5 min max so we don't hang if server never sends completion
ws.connect(f"{ws_address}/ws?clientId={client_id}")
_dbglog("run_pose_workflow.py:ws_connected", "WebSocket connected", {})
images = get_images(ws, prompt)
ws.close()
_dbglog("run_pose_workflow.py:workflow_done", "Workflow completed", {"num_nodes": len(images)})

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
            _dbglog("run_pose_workflow.py:saved", "Saved output image", {"path": output_image_path, "size": len(image_data)})
            saved = True
            break
    if saved:
        break

if not saved:
    raise RuntimeError("No output image was generated or retrieved.")
