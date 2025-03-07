from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (User,
                     SuperAdmin)


# --------------SUPERADMIN DASHBOARD SERIALIZER--------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class SuperAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperAdmin
        fields = ['phone_number', 'address', 'designation']

# ---------------SUPER ADMIN REGISTER SERIALIZER---------------
""" ONLY FOR SUPER-ADMIN """
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email']
        extra_kwargs = {'password': {'write_only': True}}


class SuperAdminSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = SuperAdmin
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = user_data.pop('password')

        user_instance = User(**user_data)
        user_instance.set_password(password)
        user_instance.is_superadmin = True
        user_instance.save()

        super_admin_instance = SuperAdmin.objects.create(user=user_instance, **validated_data)
        return super_admin_instance

    def update(self, instance, validated_data):
        # Only update the SuperAdmin fields (not the user fields)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# ---------------SUPER ADMIN LOGIN SERIALIZER--------------
class SuperAdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_superadmin:
            raise serializers.ValidationError("You are not authorized as a superadmin")
        return {'user': user}