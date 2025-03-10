from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (Quadrant,
                     Tooth,
                     Treatment,
                     DentalChart)


class QuadrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quadrant
        fields = '__all__'


class ToothSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = '__all__'


class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = '__all__'


class DentalChartSerializer(serializers.ModelSerializer):
    quadrants = QuadrantSerializer(many=True, read_only=True, source='get_quadrants')
    teeth = ToothSerializer(many=True, read_only=True, source='get_teeth')
    treatments = TreatmentSerializer(many=True, read_only=True, source='get_treatments')

    class Meta:
        model = DentalChart
        fields = ['id', 'patient', 'created_at', 'updated_at', 'quadrants', 'teeth', 'treatments']


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
