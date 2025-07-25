import argparse
import websocket
import uuid
import json
import urllib.request
import urllib.parse
import os
from PIL import Image
import io

# ---- STEP 1: Parse CLI Arguments ----
parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, required=True)
parser.add_argument('--output', type=str, required=True)
args = parser.parse_args()

input_image_path = args.input
output_image_path = args.output

# ---- STEP 2: Setup Server and Client ID ----
server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

# ---- STEP 3: ComfyUI API Helper Functions ----
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://{server_address}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{server_address}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break  # Done executing
        else:
            continue  # Binary previews

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

# ---- STEP 4: Load Workflow JSON and Inject Input Path ----
with open("C:/Users/vedan/OneDrive/Desktop/Mangakai/mangakai_backend/mangakai/face_to_anime (1).json", "r", encoding="utf-8") as f:
    prompt = json.load(f)
# Find the node that needs the input image path
# Replace `11` below with the actual node ID key in your JSON
# If you're unsure, print the prompt keys and locate it
prompt["11"]["inputs"]["image"] = input_image_path

# ---- STEP 5: Connect to WebSocket, Run Workflow, Get Image ----
ws = websocket.WebSocket()
ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
images = get_images(ws, prompt)
ws.close()

# ---- STEP 6: Save First Output Image to Desired Output Path ----
saved = False
for node_id in images:
    for image_data in images[node_id]:
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        with open(output_image_path, 'wb') as f:
            f.write(image_data)
        saved = True
        break
    if saved:
        break

if not saved:
    raise RuntimeError("No image was generated or retrieved.")
