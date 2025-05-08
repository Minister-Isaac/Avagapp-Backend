from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate


from .serializers import SignupSerializer, UserSerializer
from users.models import  CustomUser

class UserViewSet(viewsets.ModelViewSet):
    serializer = UserSerializer
    queryset = CustomUser.objects.select_related("institution").order_by("id")
    
    def get_permissions(self):
        actions = ["login", "signup"]
        if self.action in actions:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @action(methods=["POST"], detail= False, url_path="sign-up")
    def signup(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["POST"], detail=False)
    def login(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        
        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    
    
    