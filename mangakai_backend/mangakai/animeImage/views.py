from rest_framework.authtoken.models import Token  # token is to get user and get data related to that user
from rest_framework.decorators import api_view # to check which type of curl is there
from rest_framework.response import Response # to give a response to the frontend
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import parser_classes
import subprocess, uuid, os 
from django.conf import settings # this is to get files like media/ output/input/poses
from animeImage.models import AnimeImage,PoseImage     # this are the storage tables where the panels are stored
import time # this is to create the wait time

poses_map = {
        'casting':{
            "file":"pose_templates/casting.png",
            "prompt":"anime character casting a magic spell, glowing energy between hands, cloak flowing, hands raised, dramatic screentone, manga panel style, black and white, no background, full body",
        },
        'talking':{
            "file":"pose_templates/talking.png",
            "prompt":" anime boy standing confidently on a neon-lit city street at night, casual black hoodie and joggers, hands in pockets, soft shadowing, cinematic lighting, anime scene style, vivid colors",
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
def animeImage(request):
    # get the token from the params to get the user and assign the user with input and output image
    token_key = request.query_params.get('token')
    
    if not token_key:
        return Response({'error': 'Token not provided'}, status=400)
    
    try:
        token = Token.objects.get(key=token_key)
        user = token.user
    except Token.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=401)
    
    # get the input image 
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'No image uploaded'}, status=400)

    # check if the anime image for a particular user already exists or not if it does then delete that image also delete the output image
    # (This allows us to save memory and not repeat a action)
    animeImage,_ = AnimeImage.objects.get_or_create(user=user)
    
    if animeImage.anime_image:
      animeImage.anime_image.delete(save=False)
    if animeImage.original_image:
      animeImage.original_image.delete(save=False)
    animeImage.original_image = image_file
    animeImage.save()
    output_filename = f'{uuid.uuid4()}.png'
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # run the worflow and give input image path and store the output image in output image path
    try:
        subprocess.run([
            'python', 'run_workflow.py',
            '--input', animeImage.original_image.path,
            '--output', output_path
        ], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("❌ Error running workflow:", e.stderr)
        return Response({'error': 'Failed to process image'}, status=500)

    # 🔁 Wait until file exists (max 10 seconds)
    timeout = 10
    waited = 0
    while not os.path.exists(output_path) and waited < timeout:
        time.sleep(0.5)
        waited += 0.5

    if not os.path.exists(output_path):
        return Response({'error': 'Anime image not generated in time'}, status=500)
    
    # store the output image in output image path
    animeImage.anime_image.name = f'outputs/{output_filename}'
    animeImage.save()
    
    # get the url and give it to frontend for the user to check
    animeurl = request.build_absolute_uri(animeImage.anime_image.url)
    return Response({'anime_image_url': animeurl}, status=200)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def posesGeneration(request):

    # based on the token that the user provided in the params get the anime image that is to be given with the poses
    token_key = request.query_params.get('token')
    if not token_key:
        return Response({'error': 'Token not provided'}, status=400)
    
    try:
        token = Token.objects.get(key=token_key)
        user = token.user
    except Token.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=401)
    anime_image = AnimeImage.objects.get(user=user)
    
    # Go through the pose map one by one and give those poses to the comfyUI to generate the images
    for pose_name, config in poses_map.items():
         pose_path = config["file"]
         prompt = config["prompt"]
         
         output_filename = f"{pose_name}.png"
         output_path = os.path.join(settings.MEDIA_ROOT, "poses", output_filename)
         
        #  give the pose prompt and imput image to the workflow so that it can generate the poses
         subprocess.run([
            "python", "run_pose_workflow.py",      
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



