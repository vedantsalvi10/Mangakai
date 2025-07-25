from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
# Create your views here

@api_view(['POST'])
def register(request):
  username = request.data.get("username")
  password = request.data.get("password")
  
  if not username or not password:
    return Response({"error":"fill all the information"},status=400)
  
  if User.objects.filter(username=username).exists():
     return Response({"error":"username already exists"},status=400)
  
  user = User.objects.create(username=username)
  user.set_password(password)
  user.save()
  token = Token.objects.create(user=user)
  
  return Response({ 
    'message':'user registered successfully',
    'token':token.key
  },status=200)  