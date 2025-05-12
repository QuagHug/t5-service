import jwt
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip authentication for certain paths if needed
        exempt_paths = ['/admin/', '/api-docs/']
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Authorization header must start with Bearer'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = auth_header.split(' ')[1]
        
        try:
            # Verify the token using the shared secret key
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Add the user info to the request for use in views
            request.user_id = payload.get('user_id')
            request.username = payload.get('username')
            
            # Continue with the request
            return self.get_response(request)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {'error': 'Token has expired'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError:
            return JsonResponse(
                {'error': 'Invalid token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            ) 