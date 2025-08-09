from rest_framework.authtoken.models import Token  # token is to get user and get data related to that user
from rest_framework.decorators import api_view  # to check which type of curl is there
from rest_framework.response import Response # to give  a response to the frontend
from rest_framework.decorators import parser_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.conf import settings  # this is to get files like media/ output/input/poses
from animeImage.models import AnimeImage,PoseImage # this are the storage tables where the panels are stored
from panelGeneration.models import MangaPage
from django.core.files import File
from rest_framework.parsers import JSONParser 
from openai import OpenAI # this is to set open ai model
from dotenv import load_dotenv # this env environment that is ignored by git(to safe gaurd the api key)
load_dotenv()
import json,os,time,uuid,subprocess

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
   - Each dialogue must include a natural-language `speaker` (not “main_character” or “second_character”).
     ✅ Use a short, readable speaker label like “Teenage Boy”, “Warrior”, “Demon”, “Girl”, based on the character’s **appearance and role**.
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

▶️ If the user says: *"A teenage boy stands on a rooftop at sunset, thinking about the battles he’s been through. He clenches his fist and says, 'I won’t lose anyone again.'"*

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
    { "type": "dialogue", "speaker": "Teenage Boy", "text": "I won’t lose anyone again." }
  ]
}

DO NOT include explanation. Output only valid JSON.
"""

@api_view(['POST'])
@parser_classes([JSONParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_story_prompt(request):
  # set the api key for open ai dtory generation
    API_KEY = os.getenv("API_KEY")
    client = OpenAI(api_key=API_KEY)
    
    user= request.user
    
    # get the story from the user
    user_story = request.data.get("story")
    if not user_story:
        return Response({'error': 'No story provided'}, status=400)
    #  pass the story to open ai to generate the info for the model so that a workflow can be chossen according to the requirement
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_story}
            ],
            temperature=0.8
        )
        print("🔹 OpenAI Raw Response:", response)

        # ✅ Extract content from open ai and create prompt_json that is to be passed to the workflow
        content = response.choices[0].message.content
        print("🔹 Extracted message content:", content)
        prompt_json = json.loads(content)
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    # get the characters and determine which workflow to use 1 character, 2 character or background
    try:
        characters = prompt_json.get("characters", [])
        prompt = prompt_json.get('prompt')
        anime_image = AnimeImage.objects.get(user=user)
        if not prompt:
             return Response({'error': 'Prompt missing from OpenAI response'}, status=500)
           
        output_filename = f"{uuid.uuid4().hex}_panel.png"
        output_path = os.path.join(settings.MEDIA_ROOT, "panels", output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # For group workflow (no characters)
        if len(characters) == 0:
          cmd = [
           "python", "run_group_workflow.py",
            "--prompt", prompt,
            "--output", output_path
         ]

          # For single character
        elif len(characters) == 1:
          main = characters[0]
          try:
            main_pose = PoseImage.objects.get(anime_image=anime_image, pose_name=main["pose"])
          except PoseImage.DoesNotExist:
            return Response({'error': f"Main pose not found: {main['pose']}"}, status=404)
          main_prompt = main["description"]
          cmd = [
           "python", "run_panel_workflow1.py",
           "--anime_image", anime_image.anime_image.path,
           "--main_pose", main_pose.image.path,
           "--main_prompt", main_prompt,
           "--output", output_path
         ]

          # For two characters
        elif len(characters) == 2:
           main = characters[0]
           second = characters[1]
           try:
             main_pose = PoseImage.objects.get(anime_image=anime_image, pose_name=main["pose"])
           except PoseImage.DoesNotExist:
               return Response({'error': f"Main pose not found: {main['pose']}"}, status=404)
           second_pose_path = os.path.join(settings.BASE_DIR, "pose_templates", f"{second['pose']}.png")
           if not os.path.exists(second_pose_path):
             return Response({'error': f"Second pose template not found: {second['pose']}"}, status=404)
           main_prompt = main["description"]
           second_prompt = second["description"]
           cmd = [
              "python", "run_panel_workflow2.py",
              "--anime_image", anime_image.anime_image.path,
              "--main_pose", main_pose.image.path,
              "--main_prompt", main_prompt,
              "--second_pose", second_pose_path,
              "--second_prompt", second_prompt,
              "--output", output_path
            ]
        else:
         return Response({'error': f'Unsupported number of characters: {len(characters)}'}, status=400)

        subprocess.run(cmd, check=True)
        
        #  this is to generate text bubbles
        text_bubbles = prompt_json.get("text_bubbles", [])
        
        #  set the text bubble for the image if there is any
        if text_bubbles:
         subprocess.run([
            "python", "add_bottom_bubble.py",
             output_path,
             output_path,
             json.dumps(text_bubbles)
        ])
        # Get or create a MangaPage for this user+anime_image
        existing_panel = MangaPage.objects.filter(user=user, anime_image=anime_image).first()
        if existing_panel and existing_panel.generated_panel:
          old_path = existing_panel.generated_panel.path
          if os.path.exists(old_path):
             os.remove(old_path)
        with open(output_path, 'rb') as f:
         mangapanel, _ = MangaPage.objects.update_or_create(
           user=user,
           anime_image=anime_image,
           defaults={
            'screenplay_text': user_story,
            'generated_panel': File(f, name=f"panels/{output_filename}")
           }
         )
        panel_url = request.build_absolute_uri(mangapanel.generated_panel.url)
        # give the output image
        return Response({
            "panel_image_url": panel_url
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)