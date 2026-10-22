import logging
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import User, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    PasswordResetRequestSerializer, PasswordResetVerifyCodeSerializer, PasswordResetConfirmSerializer
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Trigger welcome / confirmation email (outputs to terminal via console backend)
            try:
                role_label = user.get_role_display()
                send_mail(
                    subject="Welcome to CareerFlow - Confirm Your Account",
                    message=(
                        f"Hello {user.full_name or user.username},\n\n"
                        f"Welcome to CareerFlow! Your account has been registered successfully as a {role_label}.\n\n"
                        f"You can log in to your dashboard here:\n"
                        f"http://localhost:5173/login\n\n"
                        f"Best regards,\n"
                        f"The CareerFlow Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome confirmation email: {e}")

            refresh = RefreshToken.for_user(user)
            refresh['role'] = user.role
            refresh['email'] = user.email

            return Response({
                'message': 'Registration successful.',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)

        first_error_field = next(iter(serializer.errors))
        first_error_msg = serializer.errors[first_error_field][0]
        return Response({
            'message': f"{first_error_field}: {first_error_msg}",
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = data['user']
            return Response({
                'message': 'Login successful.',
                'access': data['access'],
                'refresh': data['refresh'],
                'role': data['role'],
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response({
            'detail': 'Invalid email or password.',
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'error': 'Invalid or already expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    US-05-T2 & US-05-T5:
    Receives email, creates time-limited secure token, and dispatches reset instructions.
    Enforces blind enumeration protection: always returns 200 OK whether email exists or not.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = next(iter(serializer.errors.values()))[0]
            return Response({'error': first_err, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user:
            try:
                ip_addr = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
                if ip_addr and ',' in ip_addr:
                    ip_addr = ip_addr.split(',')[0].strip()

                raw_token = PasswordResetToken.create_token_for_user(user, ip_address=ip_addr, lifetime_minutes=15)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                # Retrieve the generated 4-digit verification code
                token_entry = PasswordResetToken.objects.filter(user=user, is_used=False).order_by('-created_at').first()
                code = token_entry.code if token_entry else ""

                # Prominently log the 4-digit code to the terminal for easy testing
                print("\n" + "=" * 64, flush=True)
                print("  [CAREERFLOW PASSWORD RESET VERIFICATION CODE]", flush=True)
                print(f"  User Email        : {user.email}", flush=True)
                print(f"  VERIFICATION CODE : >>>  {code}  <<<", flush=True)
                print("  Expires in        : 15 minutes", flush=True)
                print("  Action            : Paste code '", code, "' on the website to verify", sep="", flush=True)
                print("=" * 64 + "\n", flush=True)

                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
                reset_url = f"{frontend_url}/forgot-password?email={user.email}&step=code"

                context = {
                    'user_name': user.full_name or user.username,
                    'email': user.email,
                    'code': code,
                    'reset_url': reset_url,
                }

                plain_message = (
                    f"Hello {user.full_name or user.username},\n\n"
                    f"Your CareerFlow password reset 4-digit verification code is:\n\n"
                    f"   >>> {code} <<<\n\n"
                    f"Enter this code on the website to verify and set your new password:\n"
                    f"{reset_url}\n\n"
                    f"This code is valid for 15 minutes.\n\n"
                    f"Best regards,\nThe CareerFlow Team\n"
                )

                # Suppress verbose HTML noise in terminal when using console.EmailBackend
                is_console = 'console' in getattr(settings, 'EMAIL_BACKEND', '').lower()
                html_body = None if is_console else render_to_string('emails/password_reset.html', context)

                send_mail(
                    subject="Reset Your CareerFlow Password",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_body,
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to generate and email password reset token: {e}")

        # Always return identical success response to protect against user enumeration (AC 5)
        return Response({
            'message': 'If an account with that email exists, password reset instructions have been sent.',
            'email': email
        }, status=status.HTTP_200_OK)


class PasswordResetVerifyCodeView(APIView):
    """
    US-05: Verifies the 4-digit verification code before allowing password change.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetVerifyCodeSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = next(iter(serializer.errors.values()))[0]
            return Response({'error': first_err, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'valid': True,
            'message': 'Verification code verified successfully. You may now enter your new password.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    US-05-T3:
    Validates token, ensures expiry and single-use rules, hashes new password,
    and invalidates old credentials immediately.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password has been successfully reset. You may now log in with your new credentials.'
            }, status=status.HTTP_200_OK)

        error_msg = None
        if 'error' in serializer.errors:
            val = serializer.errors['error']
            error_msg = val[0] if isinstance(val, list) else str(val)
        elif 'new_password' in serializer.errors:
            val = serializer.errors['new_password']
            error_msg = val[0] if isinstance(val, list) else str(val)
        elif 'confirm_password' in serializer.errors:
            val = serializer.errors['confirm_password']
            error_msg = val[0] if isinstance(val, list) else str(val)
        else:
            first_val = next(iter(serializer.errors.values()))
            error_msg = first_val[0] if isinstance(first_val, list) else str(first_val)

        return Response({
            'error': error_msg,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)