from rest_framework import serializers
from django.contrib.auth import authenticate
from SUPERADMIN.models import User, Branch, Doctor


#---------------DOCTOR PROFILE SERIALIZER---------------
class UserViewProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class DoctorViewProfileSerializer(serializers.ModelSerializer):
    user = UserViewProfileSerializer()
    branch = BranchSerializer()

    class Meta:
        model = Doctor
        fields = '__all__'

#-----------------------------------Doctor LOGIN SERIALIZER--------------------------------------
class DoctorLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_doctor:
            raise serializers.ValidationError("You are not authorized as a doctor")
        return {'user': user}
