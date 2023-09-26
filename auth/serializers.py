from django.contrib.auth import password_validation
from rest_framework import serializers
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from user.models import User
from workspace.models import Workspace
from rest_framework_simplejwt.serializers import (TokenObtainPairSerializer,
                                                  TokenRefreshSerializer)

class AuthUserSerializer(serializers.Serializer):
    username = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        # TODO: update var to email instead
        fields = ['username', 'first_name', 'last_name', 'password']
        
    def validate_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def validate_username(self, value):
        username = value
        if username and AuthUser.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(f"User {username} already exists.")
        return value
    
    def create(self, validated_data):
        auth_user = AuthUser(
            email=validated_data.get('username'), 
            username=validated_data.get('username'), 
            first_name=validated_data.get('first_name'), 
            last_name=validated_data.get('last_name')
            )
        auth_user.set_password(validated_data.get('password'))
        auth_user.save()

        return auth_user
    

class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    
    def __init__(self, *args, **kwargs):
        request = kwargs.get('context').get('request')
        if request is not None and hasattr(request, 'user'):
            self.user = request.user
        super().__init__(*args, **kwargs)
        
    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise serializers.ValidationError('Your old password was entered incorrectly. Please enter it again.')
        return value
    
    def validate_password(self, value):
        password_validation.validate_password(value, self.user)
        return value
    
    def create(self, validated_data):
        password = validated_data['password']
        self.user.set_password(password)
        self.user.save()
        return self.user
    
class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        self.form = PasswordResetForm(data)
        if self.form.is_valid():
            return self.form.cleaned_data
        raise serializers.ValidationError(self.form.errors)
    
    def create(self, validated_data):
        request = validated_data.get('request')
        self.form.save(
            request=request,
            email_template_name='password_reset_email.html',
        )
        return validated_data

class DoPasswordResetSerializer(serializers.Serializer):
    # Ref: django.contrib.auth.views.PasswordResetConfirmView
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    token_generator = default_token_generator

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = AuthUser.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            ValidationError,
        ):
            user = None
        return user

    def validate(self, data):
        self.user = self.get_user(data['uidb64'])
        if self.user is None:
            raise serializers.ValidationError('Password reset unsuccessful.')
        password = data['password']
        token = data['token']
        if not self.token_generator.check_token(self.user, token):
            raise serializers.ValidationError('Password reset unsuccessful.')
        password_validation.validate_password(password, self.user)
        return data
    
    def create(self, validated_data):
        password = validated_data['password']
        self.user.set_password(password)
        self.user.save()
        return validated_data
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['access_token'] = data.pop('access')
        data['refresh_token'] = data.pop('refresh')
        return data

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None
    access = None
    refresh_token = serializers.CharField()
    access_token = serializers.CharField(read_only=True)
    
    def validate(self, attrs):
        attrs['refresh'] = attrs.pop('refresh_token')
        data = super().validate(attrs)
        data['access_token'] = data.pop('access')
        return data

