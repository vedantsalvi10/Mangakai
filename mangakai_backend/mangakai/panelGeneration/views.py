from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import parser_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.conf import settings
from django.http import HttpResponse
from animeImage.models import AnimeImage, PoseImage
from panelGeneration.models import MangaPage
from django.core.files import File
from rest_framework.parsers import JSONParser
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import json, os, uuid, subprocess, sys, tempfile
import boto3
from botocore.config import Config
import time as _time

# ---- debug logger (shared session ID) ----
def _dbglog(loc, msg, data=None):
    lp = os.path.join(settings.BASE_DIR, "debug-3238e9.log")
    with open(lp, "a") as f:
        f.write(json.dumps({
            "sessionId": "3238e9", "location": loc, "message": msg,
            "data": data or {}, "timestamp": int(_time.time() * 1000)
        }) + "\n")

def _download_field_to_tmp(field):
    """Download an ImageField to a temp file. Uses boto3 when S3 is configured so we
    don't rely on Django's default storage (which may be filesystem and fail for S3 keys)."""
    if not field.name:
        raise ValueError("ImageField has no name (file not saved).")
    ext = os.path.splitext(field.name)[1] or '.png'
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if bucket:
            region = getattr(settings, "AWS_S3_REGION_NAME", "ap-south-1")
            s3 = boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))
            s3.download_fileobj(bucket, field.name, tmp)
        else:
            for chunk in field.chunks():
                tmp.write(chunk)
        return tmp.name

def _make_s3_client():
    region = getattr(settings, "AWS_S3_REGION_NAME", "ap-south-1")
    return boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))

SYSTEM_PROMPT = """
You are a manga panel prompt generator for an AI image generation system.

The user will give you a short story that describes **one panel** of a manga.

Your task is to return:
1. A **concise visual prompt** string suitable for AI image generation — it must describe a manga-style colorful panel with expressive, cinematic detail.
2. Character details:
   - If the story includes only one or two **explicit characters**, return them as structured objects in the `characters` array.
   - ❗️If the story includes **groups**, **crowds**, or **non-specific visual elements** (e.g. "a demon army", "his friends in the distance", "a group of villagers"):
     ✅ DO NOT return any structured characters.
     ✅ Return an **empty `characters` array**: `"characters": []`
     ✅ Include all visual information in the `prompt` string instead.
4. A `text_bubbles` array that contains:
   - A narration line (if applicable).
   - One or more dialogue lines.
   - Each dialogue must include a natural-language `speaker` (not "main_character" or "second_character").
     ✅ Use a short, readable speaker label like "Teenage Boy", "Warrior", "Demon", "Girl", based on the character's **appearance and role**.
     ✅ Derive the speaker name from the **noun phrases** in the character description or user story (e.g., "A teenage boy" → "Teenage Boy").
     ❌ Never use "main_character" or "second_character" as speaker names.

---

❗️STRICT RULES❗️
- ❌ DO NOT invent characters that are not in the user prompt.
- ✅ Use **only** these poses (if characters are included):
  [ "casting", "fighting_position", "kicking", "looking", "punching", "sitting", "standing_crosshands", "talking", "walking" ]
- ❌ DO NOT create your own pose names.
- ✅ The main character is always based on the user's uploaded anime-style image — if present.
- ✅ All characters and groups must visually match the **same setting**.
- ✅ `text_bubbles` must follow the tone and flow of the story.
- ✅ If using the crowd/group/multi-character workflow: return `"characters": []` and push all visual elements to the prompt only.

---



✅ Output only valid JSON in the format:

{
  "prompt": "main character doing something, (optional: second character doing something), background, manga panel, black and white",
  "characters": [
    {
      "name": "main_character",
      "pose": "pose_from_list",
      "description": "clear visual and emotional details, with background cues"
    }
    (optional second_character)
  ],
  "text_bubbles": [
    { "type": "narration", "text": "..." },
    { "type": "dialogue", "speaker": "Descriptive Name", "text": "..." },
    { "type": "dialogue", "speaker": "Descriptive Name", "text": "..." }
  ]
}

---
✅ Output only valid JSON in the format ():

{
  "prompt": "group or characters doing something, visual setting, cinematic style, manga panel, black and white",
  "characters": [],
  "text_bubbles": [
    { "type": "narration", "text": "..." },
    { "type": "dialogue", "speaker": "Descriptive Name", "text": "..." },
    { "type": "dialogue", "speaker": "Descriptive Name", "text": "..." }
  ]
}

---

📌 EXAMPLE:

▶️ If the user says: *"A teenage boy stands on a rooftop at sunset, thinking about the battles he's been through. He clenches his fist and says, 'I won't lose anyone again.'"*

Return:
{
  "prompt": "teenage boy standing on rooftop at sunset, clenched fist, emotional expression, cityscape in background, manga panel, black and white",
  "characters": [
    {
      "name": "main_character",
      "pose": "standing_crosshands",
      "description": "teenage boy with messy hair and school uniform, standing on rooftop with the sunset behind him, clenching his fist, eyes filled with emotion"
    }
  ],
  "text_bubbles": [
    { "type": "narration", "text": "He had been through too much to lose again." },
    { "type": "dialogue", "speaker": "Teenage Boy", "text": "I won't lose anyone again." }
  ]
}

DO NOT include explanation. Output only valid JSON.
"""

@api_view(['POST'])
@parser_classes([JSONParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_story_prompt(request):
  try:
    API_KEY = os.getenv("API_KEY")
    client  = OpenAI(api_key=API_KEY)
    user    = request.user

    user_story = request.data.get("story")
    if not user_story:
        return Response({'error': 'No story provided'}, status=400)

    _dbglog("views.py:generate_story_prompt:entry", "View called", {"user": str(user)})

    # 1) Ask OpenAI for structured panel description
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_story},
            ],
            temperature=0.8,
        )
        content     = response.choices[0].message.content
        prompt_json = json.loads(content)
        _dbglog("views.py:generate_story_prompt:openai_ok", "OpenAI response parsed", {"characters": len(prompt_json.get("characters", []))})
    except Exception as e:
        _dbglog("views.py:generate_story_prompt:openai_FAIL", "OpenAI error", {"error": str(e)})
        return Response({"error": str(e)}, status=500)

    # 2) Resolve characters and pick workflow
    characters  = prompt_json.get("characters", [])
    prompt_text = prompt_json.get("prompt")

    if not prompt_text:
        return Response({'error': 'Prompt missing from OpenAI response'}, status=500)

    # Only need AnimeImage when the prompt uses 1 or 2 characters (background-only uses no character image)
    anime_image = None
    anime_tmp   = None
    if len(characters) >= 1:
        try:
            anime_image = AnimeImage.objects.get(user=user)
        except AnimeImage.DoesNotExist:
            return Response({
                'error': 'Create your character first. Go to the Character page, upload a photo, and confirm your anime character before generating panels with characters.',
            }, status=400)

    using_s3 = bool(getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))
    bucket   = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)

    tmp_out_dir     = os.path.join(settings.BASE_DIR, "tmp_outputs")
    os.makedirs(tmp_out_dir, exist_ok=True)
    output_filename = f"{uuid.uuid4().hex}_panel.png"
    output_path     = os.path.join(tmp_out_dir, output_filename)

    tmp_files = []  # track temp files to clean up

    if anime_image is not None:
        anime_tmp = _download_field_to_tmp(anime_image.anime_image)
        tmp_files.append(anime_tmp)
        _dbglog("views.py:generate_story_prompt:anime_tmp", "Downloaded anime image", {"path": anime_tmp})

    # 3) Build subprocess command for the chosen workflow
    if len(characters) == 0:
        script_path = os.path.join(settings.BASE_DIR, "run_group_workflow.py")
        cmd = [
            sys.executable, script_path,
            "--prompt", prompt_text,
            "--output", output_path,
        ]

    elif len(characters) == 1:
        main = characters[0]
        try:
            main_pose_obj = PoseImage.objects.get(anime_image=anime_image, pose_name=main["pose"])
        except PoseImage.DoesNotExist:
            return Response({'error': f"Main pose not found: {main['pose']}"}, status=404)
        pose_tmp = _download_field_to_tmp(main_pose_obj.image)
        tmp_files.append(pose_tmp)
        script_path = os.path.join(settings.BASE_DIR, "run_panel_workflow1.py")
        cmd = [
            sys.executable, script_path,
            "--anime_image", anime_tmp,
            "--main_pose",   pose_tmp,
            "--main_prompt", main["description"],
            "--output",      output_path,
        ]

    elif len(characters) == 2:
        main   = characters[0]
        second = characters[1]
        try:
            main_pose_obj = PoseImage.objects.get(anime_image=anime_image, pose_name=main["pose"])
        except PoseImage.DoesNotExist:
            return Response({'error': f"Main pose not found: {main['pose']}"}, status=404)
        pose_tmp = _download_field_to_tmp(main_pose_obj.image)
        tmp_files.append(pose_tmp)
        second_pose_path = os.path.join(settings.BASE_DIR, "pose_templates", f"{second['pose']}.png")
        if not os.path.exists(second_pose_path):
            return Response({'error': f"Second pose template not found: {second['pose']}"}, status=404)
        script_path = os.path.join(settings.BASE_DIR, "run_panel_workflow2.py")
        cmd = [
            sys.executable, script_path,
            "--anime_image",   anime_tmp,
            "--main_pose",     pose_tmp,
            "--main_prompt",   main["description"],
            "--second_pose",   second_pose_path,
            "--second_prompt", second["description"],
            "--output",        output_path,
        ]

    else:
        return Response({'error': f'Unsupported number of characters: {len(characters)}'}, status=400)

    # 4) Run the ComfyUI workflow
    _dbglog("views.py:generate_story_prompt:before_subprocess", "Running workflow subprocess", {"cmd": cmd})
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        _dbglog("views.py:generate_story_prompt:subprocess_ok", "Workflow subprocess done", {"stderr": result.stderr[:300] if result.stderr else ""})
    except subprocess.CalledProcessError as e:
        _dbglog("views.py:generate_story_prompt:subprocess_FAIL", "Workflow subprocess failed", {"returncode": e.returncode, "stderr": e.stderr[:1000] if e.stderr else ""})
        return Response({"error": "Panel generation failed", "detail": e.stderr[:500] if e.stderr else "no stderr"}, status=500)

    # 5) Add text bubbles in-place
    text_bubbles = prompt_json.get("text_bubbles", [])
    if text_bubbles:
        bubble_script = os.path.join(settings.BASE_DIR, "add_bottom_bubble.py")
        try:
            subprocess.run(
                [sys.executable, bubble_script, output_path, output_path, json.dumps(text_bubbles)],
                check=True, capture_output=True, text=True, timeout=60,
            )
            _dbglog("views.py:generate_story_prompt:bubbles_ok", "Text bubbles added", {})
        except subprocess.CalledProcessError as e:
            _dbglog("views.py:generate_story_prompt:bubbles_FAIL", "Text bubble script failed", {"stderr": e.stderr[:500] if e.stderr else ""})

    # 6) Upload panel to S3 or local storage
    if using_s3:
        s3_key   = f"panels/{output_filename}"
        s3client = _make_s3_client()
        try:
            file_size = os.path.getsize(output_path)
            _dbglog("views.py:generate_story_prompt:pre_upload", "Uploading panel to S3", {"key": s3_key, "size": file_size})
            with open(output_path, "rb") as f:
                s3client.put_object(Bucket=bucket, Key=s3_key, Body=f, ContentType="image/png")
            _dbglog("views.py:generate_story_prompt:upload_ok", "Panel uploaded to S3", {"key": s3_key})
        except Exception as upload_err:
            _dbglog("views.py:generate_story_prompt:upload_FAIL", "S3 upload failed", {"error": str(upload_err)})
            return Response({"error": "Failed to upload panel to S3", "detail": str(upload_err)}, status=500)

        MangaPage.objects.update_or_create(
            user=user,
            anime_image=anime_image,
            defaults={"screenplay_text": user_story, "generated_panel": s3_key},
        )

        panel_url = s3client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=3600,
        )
        _dbglog("views.py:generate_story_prompt:success", "Returning panel URL (S3)", {"key": s3_key, "url_len": len(panel_url)})
    else:
        media_root = getattr(settings, "MEDIA_ROOT", settings.BASE_DIR)
        panels_dir = os.path.join(str(media_root), "panels")
        os.makedirs(panels_dir, exist_ok=True)
        with open(output_path, "rb") as f:
            mangapanel, _ = MangaPage.objects.update_or_create(
                user=user,
                anime_image=anime_image,
                defaults={
                    "screenplay_text": user_story,
                    "generated_panel": File(f, name=f"panels/{output_filename}"),
                },
            )
        panel_url = request.build_absolute_uri(mangapanel.generated_panel.url)
        _dbglog("views.py:generate_story_prompt:success", "Returning panel URL (local)", {"url": panel_url})

    # 7) Cleanup
    for p in tmp_files + [output_path]:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    return Response({"panel_image_url": panel_url})

  except Exception as exc:
    import traceback
    _dbglog("views.py:generate_story_prompt:UNHANDLED", "Unhandled exception", {"error": str(exc), "traceback": traceback.format_exc()})
    return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def panel_download(request):
    """Stream the user's latest panel image as a download (avoids S3 CORS in the browser)."""
    try:
        page = (
            MangaPage.objects.filter(user=request.user)
            .exclude(generated_panel="")
            .order_by("-id")
            .first()
        )
        if not page or not page.generated_panel.name:
            return Response({"error": "No panel found"}, status=404)

        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if bucket:
            s3 = _make_s3_client()
            obj = s3.get_object(Bucket=bucket, Key=page.generated_panel.name)
            body = obj["Body"].read()
        else:
            with page.generated_panel.open("rb") as f:
                body = f.read()

        response = HttpResponse(body, content_type="image/png")
        response["Content-Disposition"] = 'attachment; filename="manga_panel.png"'
        return response
    except Exception as e:
        _dbglog("views.py:panel_download:error", "Download failed", {"error": str(e)})
        return Response({"error": str(e)}, status=500)
