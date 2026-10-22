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
