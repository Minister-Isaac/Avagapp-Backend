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
from django.utils import timezone

from avag_learning.paginators import CustomPagination
from users.choices import UserType
from users.models import Notification, NotificationRecipient

from .serializers import (
    CreateNotificationSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    NotificationSerializer, 
    PasswordResetConfirmSerializer, 
    SignupSerializer, 
    UserProfileSerializer, 
    UserSerializer,
    TeacherListSerializer,
    TeacherDetailSerializer
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
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        roles = [UserType.ADMIN, UserType.TEACHER]
        # If the requesting user is a student
        if request.user.role == UserType.STUDENT:
            # Ensure the student can only delete their own account
            if user != request.user:
                return Response(
                    "You are not authorized to edit this user.",
                    status=status.HTTP_403_FORBIDDEN
                )
        if request.user.role in roles:
            # Ensure teachers can only edit students
            if user.role != UserType.STUDENT:
                return Response("You are not authorized to edit this user.", status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        roles = [UserType.ADMIN, UserType.TEACHER]
        # If the requesting user is a student
        if request.user.role == UserType.STUDENT:
            # Ensure the student can only delete their own account
            if user != request.user:
                return Response(
                    "You are not authorized to delete this user.",
                    status=status.HTTP_403_FORBIDDEN
                )

        if request.user.role in roles:
            # Ensure teachers can only delete students
            if user.role != UserType.STUDENT:
                return Response("You are not authorized to delete this user.", status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
    
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
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data["user"]
    
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status=status.HTTP_200_OK)
    
    
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


    @action(detail=False, methods=["GET"], url_path="get-all-students")
    def get_all_students(self, request):
        roles = [UserType.ADMIN, UserType.TEACHER]
        if request.user.role in roles:
            users = User.objects.filter(role=UserType.STUDENT).order_by("id")
            paginator = CustomPagination()
            paginated_student = paginator.paginate_queryset(users, request, view=self)
            serializer = self.get_serializer(paginated_student, many=True)
            return paginator.get_paginated_response(serializer.data)
        return Response(
            {"detail": "Not authorized to get student."},
            status=status.HTTP_403_FORBIDDEN
        )
        

class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(role='teacher')
    serializer_class = TeacherListSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeacherDetailSerializer
        return super().get_serializer_class()
    


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        # Students should only see their own notifications
        if self.request.user.role == "student":
            return Notification.objects.filter(recipients=self.request.user).order_by('-created_at')
        # Admins and teachers can see all notifications (you might want to adjust this)
        return Notification.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateNotificationSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, id=None):
        user = request.user
        notification = self.get_object()
        try:
            nr = NotificationRecipient.objects.get(notification=notification, user=user)
            nr.is_read = True
            nr.read_at = timezone.now()
            nr.save()
            return Response({"message": "Notification marked as read."}, status=200)
        except NotificationRecipient.DoesNotExist:
            return Response({"error": "Notification not found for this user."}, status=404)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = NotificationRecipient.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})