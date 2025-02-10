# from rest_framework import serializers
# from .models import Lead

# class LeadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Lead
#         fields = '__all__'

from rest_framework import serializers
from .models import CarBrand, CarModel, Garage

class CarModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarModel
        fields = ['id', 'name']

class CarBrandSerializer(serializers.ModelSerializer):
    models = CarModelSerializer(many=True, read_only=True)
    
    class Meta:
        model = CarBrand
        fields = ['id', 'name', 'models']

class GarageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garage
        fields = ['id', 'name', 'mechanic', 'locality', 'link', 'mobile', 'is_active']