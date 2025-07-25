from django.db import models

# model for anime character image generation
class AnimeImage(models.Model):
  user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
  original_image = models.ImageField(upload_to='uploads/')
  anime_image = models.ImageField(upload_to='outputs/', null=True, blank=True)

# model for pose generation
class PoseImage(models.Model):
  anime_image = models.ForeignKey(AnimeImage,related_name="poses",on_delete=models.CASCADE)
  pose_name = models.CharField(max_length=100)
  image = models.ImageField(upload_to='poses/')

  

  
  
  