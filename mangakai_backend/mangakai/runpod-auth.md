# RunPod proxy authentication

When ComfyUI is exposed via **RunPod's proxy** (`https://POD_ID-PORT.proxy.runpod.net`), the proxy requires an API key or requests return **403 Forbidden**.

## Fix

1. Get your API key from [RunPod Dashboard → API Keys](https://www.runpod.io/console/user/settings).
2. On the **backend server** (where Django/Gunicorn runs), set the environment variable:

   ```bash
   export RUNPOD_API_KEY="your_runpod_api_key_here"
   ```

   If you use a `.env` file (e.g. for Gunicorn), add:

   ```
   RUNPOD_API_KEY=your_runpod_api_key_here
   ```

3. Restart Gunicorn so it picks up the new variable.

All workflow scripts (`run_workflow.py`, `run_pose_workflow.py`, `run_panel_workflow1.py`, `run_panel_workflow2.py`, `run_group_workflow.py`) will then send `Authorization: Bearer <key>` on every HTTP request to `COMFYUI_URL`. If `RUNPOD_API_KEY` is not set (e.g. when using ngrok), no header is added and behavior is unchanged.
