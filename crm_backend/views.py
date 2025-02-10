from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'non_field_errors': ['Please provide both username and password']
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username
            })
        else:
            return Response({
                'non_field_errors': ['Invalid username or password']
            }, status=status.HTTP_400_BAD_REQUEST)

class CustomLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_200_OK)



# Name:                                     hjh
# Number:                            7777777777
# Car Details:              Ferrari FF 2022 CNG
# Chasis Number:                            N/A
# Registration No:                          N/A

# Arrival Mode:                          Pickup
# Arrival Time:                2025-02-04T18:02

# Address:
# Indiranagar, Bengaluru, Karnataka            

# Map Link:  
# https://maps.app.goo.gl/88TjUpZ6GBfj2iYj9

# Work Summary:

# Comprehensive Service hbjsadjasjdjgsahgdgsadhg
# Engine Oil Change d ahsdjasdhbhsabdsajdjsajjds
# Brake Fluid Top-up udhsadjbasjbdhbashdbhsabhdb
           
# Total Amount:                           ₹1545

# Workshop Name:                            N/A
# Lead Status:                         Assigned
# Lead Source:                          Website

# Lead ID:                      L-7777777777-29


# Name:                                     hjh
# Number:                            7777777777
# Car Details:              Ferrari FF 2022 CNG
# Chasis Number:                            N/A
# Registration No:                          N/A

# Arrival Mode:                          Pickup
# Arrival Time:                2025-02-04T18:02
# Address:            Indiranagar, Bengaluru, Karnataka


# Work Summary:           Comprehensive Service
# Total Amount:                           ₹1545

# Workshop Name:                            N/A
# Lead Status:                         Assigned
# Lead Source:                          Website

# Lead ID:                      L-7777777777-29




# Name:                            jay malhotra
# Number:                            7777777777
# Car:        Land Rover Discovery Sport 2022 Petrol
# Chasis No:             267167676725352145
# Reg No:                   2671676774

# Arrival Mode:                          Pickup
# Arrival Time:                2025-02-0 18:02

# Address:            
# Indiranagar, Bengaluru, Karnataka

# Map Link:           
# https://maps.app.goo.gl/88TjUpZ6GBfj2iYj9

# Work Summary:       
# Comprehensive Service, Standard Service, 
# Basic Service

# Total Amount:                          ₹13715

# Workshop Name:                           
# Onlybigcars - Motor Masters, jahangirpuri

# Lead Status:                         Assigned
# Lead Source:                          Website

# Lead ID:                      
# L-7777777777-29

