# RunPod proxy authentication

When ComfyUI is exposed via **RunPod's proxy** (`https://POD_ID-PORT.proxy.runpod.net`), you may get **403 Forbidden** on uploads or other requests. The code does three things to improve compatibility:

1. **Trailing slash** – `COMFYUI_URL` is normalized (trailing slash removed) so paths are built as `...runpod.net/upload/image` instead of `...runpod.net//upload/image` (double slash can cause 403).
2. **Bearer token** – If `RUNPOD_API_KEY` is set, every request sends `Authorization: Bearer <key>`.
3. **Browser-like headers** – All requests send a Chrome-like `User-Agent` and `Accept` so Cloudflare (in front of the proxy) is less likely to block scripted traffic.

## Set the API key (recommended)

1. Get your API key from [RunPod Dashboard → API Keys](https://www.runpod.io/console/user/settings).
2. On the **backend server** (where Django/Gunicorn runs), set:

   ```bash
   export RUNPOD_API_KEY="your_runpod_api_key_here"
   ```

   Or in `.env` (e.g. for Gunicorn):

   ```
   RUNPOD_API_KEY=your_runpod_api_key_here
   ```

3. Restart Gunicorn so it picks up the new variable.

## If 403 persists

- **Use TCP instead of the proxy** – In RunPod, edit the template: expose the ComfyUI port as **TCP** (not HTTP). Then in **Connect → TCP Port Mapping** get the pod’s public IP and external port. Set `COMFYUI_URL` to `http://<IP>:<port>` (no proxy, no Cloudflare). This avoids proxy auth and timeouts.
- Ensure the pod is running and the port (e.g. 8188) is the one ComfyUI listens on.
