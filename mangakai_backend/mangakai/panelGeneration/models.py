from django.db import models
from animeImage.models import AnimeImage,PoseImage

# model for manga panel generation 
class MangaPage(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    anime_image = models.ForeignKey(AnimeImage, on_delete=models.CASCADE, related_name="pages")
    screenplay_text = models.TextField()
    generated_panel = models.ImageField(upload_to="panels/", null=True, blank=True)