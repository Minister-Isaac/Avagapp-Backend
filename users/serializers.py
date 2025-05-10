import re
from rest_framework import serializers

from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "avatar", "username", "email", "role", "institution", "first_name", "last_name", "phone_number")
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "email": {"read_only": True},
            "phone_number": {"required": False}
        }
        

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(required=False)
    
    
    class Meta:
        model = User
        fields = ("username", "email", "password", "confirm_password", "role", "institution", "phone_number", "first_name", "last_name")

    def validate(self, attrs):
        # Check password and confirm password match
        if attrs.get("password") != attrs.get("confirm_password"):
            raise ValidationError("password do not match.")
        return attrs
    
    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 character long.")
        if not re.search(r"[A-Z]", value):
            raise ValidationError("Password must contain one uppercase letter.")
        if not re.search(r"\d", value):
            raise ValidationError("Password must contain at least one numeric digit.")
        if not re.search(r"[a-zA-Z0-9]", value):
            raise ValidationError("Password must contain at least one alphanumeric character.")
        return value
    
    def create(self, validated_data):
        try:
            user = CustomUser.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=validated_data["password"],
                role=validated_data["role"],
                institution=validated_data.get("institution")
            )
            return user
        except Exception as e:
            raise ValidationError(f"error creating user: {e}")
        
class UserProfileSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            "id", "full_name", "phone_number", "email", "phone_number",
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
        validate_password.pop("confirm_password")
        password = validated_data.pop("password", None)
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
            raise serializers.ValidationError({"new_password": "The two password fields didn't match."})
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
