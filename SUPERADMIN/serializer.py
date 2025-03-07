from rest_framework import serializers
import random
import string
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import (User,
                     SuperAdmin,
                     Doctor,
                     Branch)

#----------------------Doctor Serializer--------------------------------
class UserSerializer2(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        extra_kwargs = {'password': {'write_only': True}}

class DoctorCreateSerializer(serializers.ModelSerializer):
    user = UserSerializer2()
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=True)
    class Meta:
        model = Doctor
        fields = ['id', 'experience_years', 'specialization', 'qualification', 'phone_number', 'address', 'user', 'branch']

    def create(self, validated_data):
        user_data = validated_data.pop('user', None)

        password = user_data.pop('password', None)
        if not password:
            password=self._generate_random_password()

        username=user_data.get('username', None)
        if not username:
            username = f"{user_data['first_name'].lower()}_{user_data['last_name'].lower()}"

        user_instance = get_user_model()(**user_data)
        user_instance.username = username
        user_instance.set_password(password)
        user_instance.is_doctor=True
        user_instance.save()

        reception_instance = Doctor.objects.create(
            user = user_instance,
            **validated_data
        )
        self.send_reception_id_email(user_instance.email, user_instance.username, password)
        return  reception_instance


    def send_reception_id_email(self, email, username, password):
        subject ="Doctor Account Details"
        message = f"Dear Doctor,\n\n Your account has been created. Here the login details \n\n Username: {username}\nPassword:{password} \n\n Thank You !"
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(subject, message, from_email, [email])

    def _generate_random_password(self):
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return password

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