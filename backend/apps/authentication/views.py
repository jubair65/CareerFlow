import logging
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

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