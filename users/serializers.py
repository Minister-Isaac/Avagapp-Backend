import re
from rest_framework import serializers

from learning.models import Subject
from learning.serializers import SubjectSerializer
from users.choices import UserType

from .models import Notification, NotificationRecipient, StudentProfile
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(source="is_active", read_only=True)
    class Meta:
        model = User
        fields = (
            "id", "avatar", "email", "role",
            "institution", "first_name", "last_name",
            "phone_number", "subject_taught", "experience_years",
            "created_at", "updated_at", "status",
            )
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "email": {"read_only": True},
            "phone_number": {"required": False}
        }
        

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(required=False)
    subject_taught = serializers.CharField(required=False)  # Accept subject name as input
    experience_years = serializers.IntegerField(required=False, min_value=0)
    
    class Meta:
        model = User
        fields = (
            "email", "password", "confirm_password",
            "role", "institution", "phone_number", "first_name",
            "last_name", "subject_taught", "experience_years"
            )

    def validate(self, attrs):
        # Check password and confirm password match
        if attrs.get("password") != attrs.get("confirm_password"):
            raise ValidationError("password do not match.")
        role = attrs.get("role")
        subject_taught = attrs.get("subject_taught")
        experience_years = attrs.get("experience_years")

        if role == 'teacher':
            if subject_taught is None:
                raise ValidationError("This field is required for teachers 'subject_taught'.")
            if experience_years is None:
                raise ValidationError("This field is required for teachers 'experience_years'.")
             # Validate that the subject exists
            try:
                subject = Subject.objects.get(name__iexact=subject_taught)
                attrs['subject_taught'] = subject  # Replace subject name with the Subject instance
            except Subject.DoesNotExist:
                raise ValidationError(f"Subject with name '{subject_taught}' does not exist.")
            
        return attrs
    
    def create(self, validated_data):
        try:
            user = User.objects.create_user(
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                phone_number=validated_data.get("phone_number"),
                email=validated_data["email"],
                password=validated_data["password"],
                role=validated_data["role"],
                institution=validated_data.get("institution"),
                subject_taught=validated_data.get("subject_taught"),
                experience_years=validated_data.get("experience_years")
            )
            return user
        except Exception as e:
            raise ValidationError(f"error creating user: {e}")


class UserProfileSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            "id", "first_name", "last_name", "phone_number", "email", "phone_number",
            "avatar", "password", "confirm_password"
        ]
        # fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "email": {"read_only": True}
        }

    def validate(self, data):
        # Check password and confirm password match
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError("password do not match.")
        return data

    def validate_new_password(self, value):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 character long.")
        if not re.search(r"[A-Z]", value):
            raise ValidationError("Password must contain one uppercase letter.")
        if not re.search(r"\d", value):
            raise ValidationError("Password must contain at least one numeric digit.")
        if not re.search(r"[a-zA-Z0-9]", value):
            raise ValidationError("Password must contain at least one alphanumeric character.")
        return value
    
    def update(self, instance, validated_data):
        confirm_password = validated_data.pop("confirm_password", None)
        password = validated_data.pop("password", None)
        
        # If either password or confirm_password is provided, both must be present
        if (password and not confirm_password) or (confirm_password and not password):
            raise ValidationError("Both password and confirm_password are required to change the password.")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    

class ForgotPasswordSerializer(serializers.Serializer):
     email = serializers.EmailField()
     
     def validate_email(self, value):
        try:
            User.objects.get(email=value)  
            return value 
        except User.DoesNotExist:
            raise  serializers.ValidationError("There is no user registered with this email address.") 
    
  
class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError( "The two password fields didn't match.")
        return data
    
    def validate_new_password(self, value):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 character long.")
        if not re.search(r"[A-Z]", value):
            raise ValidationError("Password must contain one uppercase letter.")
        if not re.search(r"\d", value):
            raise ValidationError("Password must contain at least one numeric digit.")
        if not re.search(r"[a-zA-Z0-9]", value):
            raise ValidationError("Password must contain at least one alphanumeric character.")
        return value


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"
        

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserType.choices)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        role = attrs.get("role")

        # Check if the email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address or incorrect email.")

        # Check if the password is correct
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Incorrect password.")
        
        # Check if the user has the correct role
        if user.role != role:
            raise serializers.ValidationError("User role mismatch.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user
        return attrs
    

class TeacherListSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(source='subject_taught', read_only=True)
    experience = serializers.IntegerField(source='experience_years', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "subject", "experience", "first_name", "last_name", "avatar"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def update(self, instance, validated_data):
        # Update first_name and last_name if provided
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save()
        return instance
    

class TeacherDetailSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(source='subject_taught', read_only=True)
    experience = serializers.IntegerField(source='experience_years', read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "first_name",
            "last_name", "email",
            "subject", "experience",
            "phone_number", "institution",
            "avatar", "created_at",]
            
    
class CreateNotificationSerializer(serializers.ModelSerializer):
    recipient_roles = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Specify the roles to send the notification to (e.g., ['teacher', 'student' 'both'])."
    )
    
    class Meta:
        model = Notification
        fields = ["id", "message", "title", "recipient_roles", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        roles = [UserType.ADMIN, UserType.TEACHER]
        if user.role not in roles:
            raise serializers.ValidationError("Only admins can create notifications.")
       
       # Extract recipient roles and remove from validated_data
        recipient_roles = validated_data.pop("recipient_roles")
        
        notification = Notification.objects.create(**validated_data)
        
        # Determine recipient roles
        if recipient_roles == "both":
            recipient_roles = [UserType.STUDENT, UserType.TEACHER]
        elif recipient_roles == "student":
            recipient_roles = [UserType.STUDENT]
        elif recipient_roles == "teacher":
            recipient_roles = [UserType.TEACHER]
        else:
            raise serializers.ValidationError("Invalid recipient roles. Use 'student', 'teacher', or 'both'.")
        
        # Filter users based on recipient roles
        recipients = User.objects.filter(role__in=recipient_roles)
        for recipient in recipients:
            NotificationRecipient.objects.create(notification=notification, user=recipient)
            
        return notification
    
class NotificationRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRecipient
        fields = "__all_"
        read_only_fields = ["id", "read_at"]