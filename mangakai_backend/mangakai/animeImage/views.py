from rest_framework.authtoken.models import Token  # token is to get user and get data related to that user
from rest_framework.decorators import api_view # to check which type of curl is there
from rest_framework.response import Response # to give a response to the frontend
from rest_framework.parsers import MultiPartParser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.decorators import parser_classes
import subprocess, uuid, os, sys 
from django.conf import settings # this is to get files like media/ output/input/poses
from animeImage.models import AnimeImage,PoseImage     # this are the storage tables where the panels are stored
import time # this is to create the wait time
import tempfile
from django.core.files import File
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import json as _json, time as _time
# #region agent log
def _dbglog(loc, msg, data=None, hyp=""):
    import os as _os
    _lp = _os.path.join(settings.BASE_DIR, "debug-3238e9.log")
    with open(_lp, "a") as _f:
        _f.write(_json.dumps({"sessionId":"3238e9","location":loc,"message":msg,"data":data or {},"hypothesisId":hyp,"timestamp":int(_time.time()*1000)}) + "\n")
# #endregion
poses_map = {
        'casting':{
            "file":"pose_templates/casting.png",
            "prompt":"anime character casting a magic spell, glowing energy between hands, cloak flowing, hands raised, dramatic screentone, manga panel style, black and white, no background, full body",
        },
        'talking':{
            "file":"pose_templates/talking.png",
            "prompt":" anime b oy standing confidently on a neon-lit city street at night, casual black hoodie and joggers, hands in pockets, soft shadowing, cinematic lighting, anime scene style, vivid colors",
        },
        'looking':{
            "file":"pose_templates/looking.png",
            "prompt":" anime boy standing confidently on a neon-lit city street at night, casual black hoodie and joggers, hands in pockets, soft shadowing, cinematic lighting, anime scene style, vivid colors",
        },
        'kicking':{
            "file":"pose_templates/kicking.png",
            "prompt":"anime style character performing a high side kick, casual white t-shirt and jeans, red sneakers, intense expression, looking to the side or slightly upward, spiky hair flowing with motion, head slightly turned, dynamic angle, energetic pose, mid-air action, clean background, vivid anime line art, natural anatomy, no armor, no weapons",
        },
        'fighting_position':{
            "file":"pose_templates/fighting_position.png",
            "prompt":"anime style character in a defensive fighting pose, casual clothes (hoodie and joggers), one fist raised near face, other clenched forward, serious expression, slight lean forward, dynamic pose, short messy hair, intense lighting, no armor, no weapons, no background, cinematic framing, anime shading",
        },
        'punching':{
            "file":"pose_templates/punching.png",
            "prompt":" anime style character throwing a powerful punch, same face and hairstyle, dynamic action pose, intense expression, high detail, motion blur on fist, sharp black outline, no background",
        },
        'standing':{
            "file":"pose_templates/standing.png",
            "prompt":" anime boy talking with slight expression, standing in a neon-lit city street at night, casual black hoodie and joggers, hands relaxed, waist-up portrait, soft shadowing, cinematic lighting, anime style, vivid colors",
        },
        'standing_crosshands':{
            "file":"pose_templates/standing_crosshands.png",
            "prompt":" anime boy talking with slight expression, standing in a neon-lit city street at night, casual black hoodie and joggers, hands relaxed, waist-up portrait, soft shadowing, cinematic lighting, anime style, vivid colors",
        },
        'sitting':{
            "file":"pose_templates/sitting.png",
            "prompt":"anime character sitting on a chair, relaxed posture, legs apart, arms resting on armrests, full body, looking forward, natural pose, no background",
        },
        'walking':{
            "file":"pose_templates/walking.png",
            "prompt":"anime character standing in a city street at night, same facial structure as reference, hoodie, black pants, soft lighting, detailed face, cinematic anime background, high detail",
        },    
    }

@api_view(['POST'])
@parser_classes([MultiPartParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def animeImage(request):
  try:
    user = request.user
    # #region agent log
    _dbglog("views.py:animeImage:entry", "View called", {"user": str(user)}, "H5")
    # #endregion
    # get the input image 
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'No image uploaded'}, status=400)

    animeImage,_ = AnimeImage.objects.get_or_create(user=user)
    
    if animeImage.anime_image:
      animeImage.anime_image.delete(save=False)
    if animeImage.original_image:
      animeImage.original_image.delete(save=False)
    animeImage.original_image = image_file
    animeImage.save()
    # #region agent log
    _dbglog("views.py:animeImage:after_save", "Image saved to model", {"original_name": animeImage.original_image.name}, "H5")
    # #endregion
    output_filename = f'{uuid.uuid4()}.png'
    # 1) Download the uploaded original image locally (S3-safe)
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(animeImage.original_image.name)[-1], delete=False) as tmp_in:
      for chunk in animeImage.original_image.chunks():
        tmp_in.write(chunk)
      input_path = tmp_in.name
    # 2) Create a local output path
    tmp_out_dir = os.path.join(settings.BASE_DIR, "tmp_outputs")
    os.makedirs(tmp_out_dir, exist_ok=True)
    output_path = os.path.join(tmp_out_dir, output_filename)
    script_path = os.path.join(settings.BASE_DIR, "run_workflow.py")
    # #region agent log
    _dbglog("views.py:animeImage:paths", "Resolved paths", {"input_path": input_path, "output_path": output_path, "script_path": script_path, "script_exists": os.path.exists(script_path), "BASE_DIR": str(settings.BASE_DIR)}, "H4")
    # #endregion
    if not os.path.exists(script_path):
      return Response({"error": f"Workflow script not found: {script_path}"}, status=500)
    # 3) Run workflow
    # #region agent log
    _dbglog("views.py:animeImage:before_subprocess", "About to run subprocess", {"cmd": [sys.executable, script_path, '--input', input_path, '--output', output_path], "python_exe": sys.executable}, "H1,H2,H3")
    # #endregion
    try:
        result = subprocess.run(
            [sys.executable, script_path, '--input', input_path, '--output', output_path],
            check=True, capture_output=True, text=True
        )
        # #region agent log
        _dbglog("views.py:animeImage:subprocess_success", "Subprocess completed", {"stdout": result.stdout[:500] if result.stdout else "", "stderr": result.stderr[:500] if result.stderr else ""}, "H1,H2,H3")
        # #endregion
    except subprocess.CalledProcessError as e:
        # #region agent log
        _dbglog("views.py:animeImage:subprocess_FAILED", "Subprocess error", {"returncode": e.returncode, "stderr": e.stderr[:2000] if e.stderr else "", "stdout": e.stdout[:500] if e.stdout else ""}, "H1,H2,H3,H4")
        # #endregion
        return Response({'error': 'Failed to process image', 'detail': e.stderr[:500] if e.stderr else 'no stderr'}, status=500)
    # 4) Upload the generated output (S3 or local via ImageField)
    try:
        if not getattr(settings, "DEFAULT_FILE_STORAGE", "").endswith("S3Boto3Storage"):
            media_root = getattr(settings, "MEDIA_ROOT", None)
            if media_root:
                out_dir = os.path.join(str(media_root), "outputs")
                os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "rb") as f:
            animeImage.anime_image.save(output_filename, File(f), save=True)
    except Exception as upload_err:
        _dbglog("views.py:animeImage:upload_failed", "S3 upload failed", {"error": str(upload_err), "filename": output_filename}, "H5")
        return Response({"error": "Failed to upload image to storage", "detail": str(upload_err)}, status=500)
    # 5) Cleanup temp files
    for p in (input_path, output_path):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass
    s3_key = animeImage.anime_image.name
    storage = animeImage.anime_image.storage
    using_s3 = storage.__class__.__name__ == "S3Boto3Storage"

    if using_s3:
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        region = getattr(settings, "AWS_S3_REGION_NAME", "ap-south-1")
        animeurl = None
        if bucket and s3_key:
            try:
                # Use instance role credentials (default chain) — do NOT pass explicit keys
                client = boto3.client(
                    "s3",
                    region_name=region,
                    config=Config(signature_version="s3v4"),
                )
                try:
                    client.head_object(Bucket=bucket, Key=s3_key)
                except ClientError as e:
                    code = e.response.get("Error", {}).get("Code", "")
                    if code in ("404", "NoSuchKey"):
                        _dbglog("views.py:animeImage:s3_key_missing", "Object not in S3 after save", {"bucket": bucket, "key": s3_key}, "H5")
                        return Response({"error": "Image upload did not complete; object not found in storage.", "key": s3_key}, status=500)
                    raise
                animeurl = client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": s3_key},
                    ExpiresIn=3600,
                )
            except Exception as e:
                _dbglog("views.py:animeImage:presign_failed", "Presign failed", {"error": str(e), "key": s3_key}, "H5")
                raise
        if not animeurl or "X-Amz-Algorithm" not in (animeurl or ""):
            _dbglog("views.py:animeImage:no_sigv4", "Presigned URL missing SigV4 params", {"key": s3_key}, "H5")
            return Response(
                {"error": "Failed to generate secure image URL"},
                status=500,
            )
        # #region agent log
        _dbglog("views.py:animeImage:success", "Returning anime URL (S3)", {
            "url_len": len(animeurl),
            "key": s3_key,
        }, "H5")
        # #endregion
        return Response({'anime_image_url': animeurl}, status=200)
    else:
        # Local storage: file is under MEDIA_ROOT (e.g. media/outputs/xxx.png). Return absolute URL.
        relative_url = animeImage.anime_image.url
        animeurl = request.build_absolute_uri(relative_url)
        # #region agent log
        _dbglog("views.py:animeImage:success", "Returning anime URL (local)", {"url": animeurl, "key": s3_key}, "H5")
        # #endregion
        return Response({'anime_image_url': animeurl}, status=200)
  except Exception as exc:
    # #region agent log
    import traceback
    _dbglog("views.py:animeImage:UNHANDLED", "Unhandled exception", {"error": str(exc), "traceback": traceback.format_exc()}, "H5")
    # #endregion
    return Response({'error': str(exc)}, status=500)

@api_view(['POST'])
@parser_classes([MultiPartParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def posesGeneration(request):
    user = request.user
    anime_image = AnimeImage.objects.get(user=user)
    
    # Go through the pose map one by one and give those poses to the comfyUI to generate the images
    for pose_name, config in poses_map.items():
         pose_path = config["file"]
         prompt = config["prompt"]
         
         output_filename = f"{pose_name}.png"
         output_path = os.path.join(settings.MEDIA_ROOT, "poses", output_filename)
         
        #  give the pose prompt and imput image to the workflow so that it can generate the poses
         subprocess.run([
            sys.executable, "run_pose_workflow.py",      
            "--character", anime_image.anime_image.path,
            "--pose", os.path.join(settings.BASE_DIR, pose_path),
            "--prompt", prompt,
            "--output", output_path,
        ], check=True)
         
        #  wait for 10 seconds if no image then give error
         timeout = 10
         waited = 0
         while not os.path.exists(output_path) and waited <timeout:
             time.sleep(0.5)
             waited +=0.5
        
        # Store the generated pose in the path 
         PoseImage.objects.update_or_create(
            anime_image=anime_image,
            pose_name=pose_name,
             defaults={
                "image": f"poses/{output_filename}",  
            }  
        )



