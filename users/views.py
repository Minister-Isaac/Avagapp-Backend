from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

from users.choices import UserType

from .serializers import (
    ForgotPasswordSerializer, 
    PasswordResetConfirmSerializer, 
    SignupSerializer, 
    UserProfileSerializer, 
    UserSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.select_related("institution").order_by("id")
    
    def get_serializer_class(self):
        if self.action == "sign-up":
            return SignupSerializer
        if self.action == "user_profile":
            return UserProfileSerializer
        if self.action == "forgot_password":
            return ForgotPasswordSerializer
        if self.action == "reset_password_confirm":
            return PasswordResetConfirmSerializer
        return super().get_serializer_class()

    
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
            return Response({
                "user": UserSerializer(user).data,
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["POST"], detail=False)
    def login(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")
        
        if not email or not password or not role:
            return Response({"error": "Email, password and role are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, email=email, password=password, role=role)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(methods=["GET", "PUT"], detail=False, url_path="profile")
    def user_profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path="forgot-password")
    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                reset_url = f"{settings.FRONTEND_FORGET_PASSWORD_URL}/?uid={uid}&token={token}"
                # TODO add dramatiq to send task and ask for smtp config
                
                # forget_password_tasks.send(reset_url, email)
                return Response({"message": "Password reset email has been sent."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not not found."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["post"], url_path="password-reset/confirm")
    def reset_password_confirm(self, request, token=None):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            new_password = serializer.validated_data["new_password"]
            token = serializer.validated_data["token"]
            # Get uidb64 from request data
            uid = request.data.get("uid", "")
            try:
                uid = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            
            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)      


    @action(detail=False, methods=["GET"], url_path="get-users")
    def get_all_users(self, request):
        if request.user.role in [UserType.ADMIN or UserType.TEACHER]:
            users = User.objects.all().order_by("id")
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"detail": "Not authorized to view users."},
            status=status.HTTP_403_FORBIDDEN
        )