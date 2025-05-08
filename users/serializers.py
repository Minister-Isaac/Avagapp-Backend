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
        fields = ("id", "username", "email", "role", "institution")
        

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    
    class Meta:
        model = User
        fields = ("username", "email", "password", "confirm_password", "role", "institution")

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