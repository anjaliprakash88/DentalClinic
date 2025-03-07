from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from .serializer import (SuperAdminLoginSerializer,
                         SuperAdminSerializer)
from rest_framework.response import Response
from .models import (SuperAdmin)


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