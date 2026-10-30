from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role', 'role_display', 'created_at']
        read_only_fields = ['id', 'created_at', 'role_display']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'role', 'password', 'confirm_password']
        extra_kwargs = {
            'username': {'required': False},
            'full_name': {'required': False},
            'role': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value.lower()

    def validate(self, attrs):
        confirm_password = attrs.pop('confirm_password', None)
        if confirm_password and attrs['password'] != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        if not validated_data.get('username'):
            email = validated_data['email']
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            validated_data['username'] = username

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email').lower()
        password = attrs.get('password')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")

        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['email'] = user.email

        return {
            'user': user,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetVerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=10)

    def validate(self, attrs):
        from .models import PasswordResetToken
        email = attrs.get('email', '').strip().lower()
        code = attrs.get('code', '').strip()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"code": "Invalid verification code or email address."})

        if not PasswordResetToken.verify_code(user, code):
            raise serializers.ValidationError({"code": "Invalid or expired verification code. Please request a new one."})

        attrs['user'] = user
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=False, allow_blank=True)
    token = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        from django.core.exceptions import ValidationError as DjangoValidationError
        from .models import PasswordResetToken

        uid = attrs.get('uid')
        token = attrs.get('token')
        email = attrs.get('email')
        code = attrs.get('code')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if confirm_password and new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        user = None

        # Option A: 4-digit code with email
        if email and code:
            try:
                user = User.objects.get(email__iexact=email.strip().lower())
            except User.DoesNotExist:
                raise serializers.ValidationError({"error": "Invalid verification code or email address."})

            if not user.is_active:
                raise serializers.ValidationError({"error": "This account is inactive."})

            if not PasswordResetToken.validate_and_consume_code(user, code):
                raise serializers.ValidationError({
                    "error": "The verification code is invalid, already used, or has expired. Please request a new code."
                })

        # Option B: Cryptographic token with uid
        elif uid and token:
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                raise serializers.ValidationError({"error": "The password reset link is invalid or has expired."})

            if not user.is_active:
                raise serializers.ValidationError({"error": "This account is inactive."})

            if not PasswordResetToken.validate_and_consume_token(user, token):
                raise serializers.ValidationError({
                    "error": "The password reset link is invalid or has expired. Please request a new one."
                })
        else:
            raise serializers.ValidationError({
                "error": "Please provide either the 4-digit verification code or the reset token."
            })

        # Validate password complexity using Django's configured validators
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


import re
from urllib.parse import urlparse
from .models import CandidateProfile


class CandidateProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', required=False, allow_blank=True)
    role = serializers.CharField(source='user.role', read_only=True)
    role_display = serializers.CharField(source='user.get_role_display', read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'user_id', 'email', 'full_name', 'role', 'role_display',
            'phone_number', 'linkedin_url', 'github_url', 'target_role',
            'bio', 'avatar', 'avatar_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'email', 'role', 'role_display', 'avatar_url', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)
        for field in ['linkedin_url', 'github_url']:
            val = data.get(field)
            if val and isinstance(val, str):
                val_clean = val.strip()
                if val_clean and not (val_clean.startswith('http://') or val_clean.startswith('https://')):
                    data[field] = f"https://{val_clean}"
        return super().to_internal_value(data)

    def get_avatar_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def validate_phone_number(self, value):
        if not value:
            return value
        clean = str(value).strip()
        digits_only = re.sub(r'\D', '', clean)
        if len(digits_only) < 7 or len(digits_only) > 16:
            raise serializers.ValidationError("Enter a valid phone number with 7 to 15 digits (e.g. +1 555-123-4567).")
        if not re.match(r'^\+?[0-9\s\-()]+$', clean):
            raise serializers.ValidationError("Phone number contains invalid characters.")
        return clean

    def validate_linkedin_url(self, value):
        if not value:
            return value
        clean = str(value).strip()
        parsed = urlparse(clean)
        if not parsed.scheme or not parsed.netloc:
            clean = f"https://{clean}"
            parsed = urlparse(clean)
        domain = parsed.netloc.lower()
        if not (domain == 'linkedin.com' or domain.endswith('.linkedin.com')):
            raise serializers.ValidationError("Please provide a valid LinkedIn URL (e.g. https://www.linkedin.com/in/yourname).")
        return clean

    def validate_github_url(self, value):
        if not value:
            return value
        clean = str(value).strip()
        parsed = urlparse(clean)
        if not parsed.scheme or not parsed.netloc:
            clean = f"https://{clean}"
            parsed = urlparse(clean)
        domain = parsed.netloc.lower()
        if not (domain == 'github.com' or domain.endswith('.github.com')):
            raise serializers.ValidationError("Please provide a valid GitHub URL (e.g. https://github.com/yourusername).")
        return clean

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'full_name' in user_data:
            instance.user.full_name = user_data['full_name']
            instance.user.save(update_fields=['full_name'])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
