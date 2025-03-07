from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.urls import reverse
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import login
from .serializer import (SuperAdminLoginSerializer,
                         SuperAdminSerializer,
                         SuperAdminUpdateSerializer,
                         UserUpdateSerializer)
from rest_framework.response import Response
from .models import (SuperAdmin)

# --------------SUPER ADMIN DASHBOARD-------------
class SuperAdminDashboard(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'superadmin/superadmindashboard.html'

    @method_decorator(login_required(login_url='/superadmin/login/'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        user = request.user
        try:
            super_admin = SuperAdmin.objects.get(user=user)
            super_admin_serializer = SuperAdminUpdateSerializer(super_admin)
        except ObjectDoesNotExist:
            super_admin_serializer = None

        user_serializer = UserUpdateSerializer(user)

        if request.accepted_renderer.format == 'html':
            return Response({
                'user': user_serializer.data,
                'super_admin': super_admin_serializer.data if super_admin_serializer else {}
            })
        else:
            return Response({
                'user': user_serializer.data,
                'super_admin': super_admin_serializer.data if super_admin_serializer else {}
            })

    def post(self, request):
        user = request.user
        user_data = request.data.get('user_info', {})
        super_admin_data = request.data.get('super_admin_info', {})

        user_serializer = UserUpdateSerializer(user, data=user_data, partial=True)

        try:
            super_admin = SuperAdmin.objects.get(user=user)
            super_admin_serializer = SuperAdminUpdateSerializer(super_admin, data=super_admin_data, partial=True)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'SuperAdmin profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if user_serializer.is_valid() and super_admin_serializer.is_valid():
            user_serializer.save()
            super_admin_serializer.save()
            return JsonResponse({
                'message': 'Profile updated successfully',
                'user_info': user_serializer.data,
                'super_admin_info': super_admin_serializer.data
            }, status=status.HTTP_200_OK)

        errors = {}
        errors.update(user_serializer.errors)
        errors.update(super_admin_serializer.errors)

        return JsonResponse({
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)

# -------------------------- SUPER ADMIN REGISTRATION--------------------------
class SuperAdmin_Signup(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'superadmin/superadmin_signup.html'

    def get(self, request):
        super = SuperAdmin.objects.all()
        serializer = SuperAdminSerializer(super, many=True)
        return Response({'serializer': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SuperAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'serializer': serializer.data, 'message': 'Superuser registered successfully!'},
                            status=status.HTTP_201_CREATED)
        return Response({'serializer': serializer.data, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


# -------------------------- SUPER ADMIN LOGIN --------------------------
class SuperAdminLogin(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'superadmin/superadmin_login.html'

    def get(self, request):
        serializer = SuperAdminLoginSerializer()
        return Response({'serializer': serializer.data})

    def post(self, request):
        serializer = SuperAdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            Token.objects.get_or_create(user=user)
            return HttpResponseRedirect(reverse('superadmindashboard'))
        return Response({"message": "Invalid credentials", 'serializer': serializer, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)