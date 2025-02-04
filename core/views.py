from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from rest_framework import status

from django.db import transaction
from .models import Customer, Lead, Profile, Order, Car
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def home_view(request):
     # Get 3 most recent leads
    page_number = request.GET.get('page', 1)
    recent_leads = Lead.objects.select_related('customer', 'profile', 'order').order_by('-created_at')
    last_lead = Lead.objects.order_by('-created_at').first()
    if last_lead:
        # Split the lead_id and get the last segment
        seq_num = int(last_lead.lead_id.split('-')[-1]) + 1
    else:
        # If no leads exist, start with 1
        seq_num = 1
    
    pagination_data = paginate_leads(recent_leads, page_number)
    users = User.objects.all().values('id', 'username')
    users_data = list(users)
    print('this is the seq num', seq_num)
    return Response({
        "message": "Recent Leads",
        'seq_num': seq_num,
        **pagination_data,
        "users": list(users)
    })



@api_view(['GET'])
def search_leads(request):
    query = request.GET.get('query', '').strip()
    page_number = request.GET.get('page', 1)
    leads = []

    # Check if query is string or number
    if query.isalpha() or (len(query) > 0 and not query.isnumeric()):
        if query.upper().startswith('L'):
            # Search in Lead IDs
            leads = Lead.objects.filter(lead_id__icontains=query)
        else:
            # Search in Customer names
            leads = Lead.objects.filter(customer__customer_name__icontains=query)
    else:
        # Search in Order IDs first
        if (len(query) <= 10):
            leads = Lead.objects.filter(customer__mobile_number__icontains=query)
        else:
            leads = Lead.objects.filter(order__order_id__icontains=query)
        
        # # If no results found, search in customer mobile numbers
        # if not leads.exists():
        #     leads = Lead.objects.filter(customer__mobile_number__icontains=query)

    pagination_data = paginate_leads(leads, page_number)
    return Response({
        "message": "Search Results",
        **pagination_data
    })

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def edit_form_submit(request):
    with transaction.atomic():
        try:
            # Get current user's profile
            print("Heres the edit page data",request.data)
            user_profile = Profile.objects.get(user=request.user)
            
            # Extract data
            data = request.data
            table_data = data['overview']['tableData']
            customer_data = request.data.get('customerInfo')
            cars_data = request.data.get('cars', [])
            location_data = request.data.get('location')
            workshop_data = request.data.get('workshop')
            arrival_data = request.data.get('arrivalStatus')
            basic_data = request.data.get('basicInfo')

            # Create or get customer
            customer, created = Customer.objects.get_or_create(
                mobile_number=customer_data['mobileNumber'],
                defaults={
                    'customer_name': customer_data['customerName'],
                    'whatsapp_number': customer_data['whatsappNumber'],
                    'customer_email': customer_data['customerEmail'],
                    'language_barrier': customer_data['languageBarrier']
                }
            )

            # Save cars
            saved_car = None
            for car_data in cars_data:
                saved_car = Car.objects.create(
                    customer=customer,
                    brand=car_data.get('carBrand'),
                    model=car_data.get('carModel'),
                    year=car_data.get('year'),
                    fuel=car_data.get('fuel'),
                    variant=car_data.get('variant'),
                    chasis_no=car_data.get('chasisNo'),
                    reg_no=car_data.get('regNo')
                )
                # Use first car if multiple cars are submitted
                if not saved_car:
                    saved_car = saved_car

             # Generate custom lead ID
            custom_lead_id = generate_custom_lead_id(customer_data['mobileNumber'])

            # Create lead with user's profile
            lead = Lead.objects.create(
                lead_id=custom_lead_id,
                profile=user_profile,  # Add the user's profile
                customer=customer,
                car=saved_car,
                source=customer_data['source'],
                lead_type=basic_data['carType'],
                # Location info
                address=location_data['address'],
                city=location_data['city'],
                state=location_data['state'],
                building=location_data['buildingName'],
                map_link=location_data['mapLink'],
                landmark=location_data['landmark'],
                # Status info
                lead_status=arrival_data['leadStatus'],
                arrival_mode=arrival_data['arrivalMode'],
                disposition=arrival_data['disposition'],
                arrival_time=arrival_data['dateTime'] if arrival_data['dateTime'] else None,
                products=table_data,
                estimated_price=basic_data['total'],
                # Workshop info
                workshop_details=workshop_data,
                ca_name=basic_data['caName'],
                cce_name=basic_data['cceName'],
                ca_comments=basic_data['caComments'],
                cce_comments=basic_data['cceComments'],
                # Store other data
                # products=table_data
            )

            return Response({
                "message": "Data saved successfully",
                "customer_id": customer.id,
                "lead_id": lead.id
            }, status=status.HTTP_201_CREATED)

        except Profile.DoesNotExist:
            return Response({
                "message": "User profile not found"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": f"Error saving data: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)



# @api_view(['POST'])
# def edit_form_submit(request):
#     try:
#         # Print received data for now
#         print("Received form data:", request.data)
#         return Response({
#             "message": "Form data received successfully",
#             "data": request.data
#         }, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({
#             "message": str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def filter_leads(request):
#     filter_data = request.data
#     print('This is the filter data', filter_data)
#     query = Lead.objects.all()
    
#     if filter_data.get('user'):
#         query = query.filter(profile__user__username=filter_data['user'])
#     if filter_data.get('source'):
#         query = query.filter(source=filter_data['source'])
#     if filter_data.get('status'):
#         query = query.filter(lead_status=filter_data['status'])
#     if filter_data.get('location'):
#         query = query.filter(city=filter_data['location'])
#     if filter_data.get('language_barrier'):
#         query = query.filter(customer__language_barrier=True)
#     # ... add other filters
    
#     leads = query.order_by('-created_at')
#     leads_data = lead_format(leads)
#     print(leads_data,'this is the leads data for', filter_data['user'])
    
#     return Response({'leads': leads_data})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def filter_leads(request):
    filter_data = request.data
    page_number = request.data.get('page', 1)
    query = Lead.objects.all()
    
    # User filter
    if filter_data.get('user'):
        query = query.filter(profile__user__username=filter_data['user'])
    
    # Basic filters
    if filter_data.get('source'):
        query = query.filter(source=filter_data['source'])
    if filter_data.get('status'):
        query = query.filter(lead_status=filter_data['status'])
    if filter_data.get('location'):
        query = query.filter(city=filter_data['location'])
    if filter_data.get('language_barrier'):
        query = query.filter(customer__language_barrier=True)
    if filter_data.get('arrivalMode'):
        query = query.filter(arrival_mode=filter_data['arrivalMode'])
        
    # Car type filter (luxury/normal)
    if filter_data.get('luxuryNormal'):
        query = query.filter(lead_type=filter_data['luxuryNormal'])
    
    # Date range filter
    # if filter_data.get('dateRange'):
    #     if filter_data['dateRange'].get('startDate'):
    #         query = query.filter(created_at__gte=filter_data['dateRange']['startDate'])
    #     if filter_data['dateRange'].get('endDate'):
    #         query = query.filter(created_at__lte=filter_data['dateRange']['endDate'])
            
    # Specific date filter
    if filter_data.get('dateCreated'):
        query = query.filter(created_at__date=filter_data['dateCreated'])
    
    # Order by latest first
    leads = query.order_by('-created_at')
    pagination_data = paginate_leads(leads, page_number)
    
    return Response(pagination_data)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_lead(request, id):
    # print('bc aavi gayo')
    try:
        lead = Lead.objects.get(lead_id=id)
        lead.is_read = True
        lead.save()
        # print('The lead bc -   ', lead)
        # Use the same lead_format function
        formatted_lead = lead_format([lead])  # Pass a list to lead_format
        # print('This is the formatted lead', formatted_lead)
        return Response(formatted_lead)  # Return the first item from the list
    except Lead.DoesNotExist:
        return Response(
            {"message": "Lead not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_lead(request, id):
    print('got to put view - ', id)
    with transaction.atomic():
        try:
            lead = Lead.objects.get(lead_id=id)
            car = lead.car
            print("Updating lead:", id)  # Debug print
            print("Request data:", request.data)  # Debug print
            
            # Extract data
            customer_data = request.data.get('customerInfo', {})
            cars_data = request.data.get('cars', [])
            location_data = request.data.get('location', {})
            workshop_data = request.data.get('workshop', {})
            arrival_data = request.data.get('arrivalStatus', {})
            basic_data = request.data.get('basicInfo', {})
            overview_data = request.data.get('overview', {})

            # Update customer
            if customer_data:
                customer = lead.customer
                customer.customer_name = customer_data.get('customerName', customer.customer_name)
                customer.mobile_number = customer_data.get('mobileNumber', customer.mobile_number)
                customer.whatsapp_number = customer_data.get('whatsappNumber', customer.whatsapp_number)
                customer.customer_email = customer_data.get('customerEmail', customer.customer_email)
                customer.language_barrier = customer_data.get('languageBarrier', customer.language_barrier)
                customer.save()

            # Update lead fields
            lead.source = customer_data.get('source', lead.source)
            lead.lead_type = basic_data.get('carType', lead.lead_type)
            lead.address = location_data.get('address', lead.address)
            lead.city = location_data.get('city', lead.city)
            lead.state = location_data.get('state', lead.state)
            lead.building = location_data.get('buildingName', lead.building)
            lead.map_link = location_data.get('mapLink', lead.map_link)
            lead.landmark = location_data.get('landmark', lead.landmark)
            lead.lead_status = arrival_data.get('leadStatus', lead.lead_status)
            lead.arrival_mode = arrival_data.get('arrivalMode', lead.arrival_mode)
            lead.disposition = arrival_data.get('disposition', lead.disposition)
            lead.arrival_time = arrival_data.get('dateTime', lead.arrival_time)
            lead.workshop_details = workshop_data
            lead.ca_name = workshop_data.get('ca', lead.ca_name)
            lead.products = overview_data.get('tableData', lead.products)
            lead.estimated_price = basic_data.get('total', lead.estimated_price)
            lead.save()

            if cars_data and car:
                car_data = cars_data[0]
                # Update existing car
                Car.objects.filter(id=car.id).update(
                    brand=car_data.get('carBrand'),
                    model=car_data.get('carModel'),
                    fuel=car_data.get('fuel'),
                    year=car_data.get('year'),
                    variant=car_data.get('variant'),
                    reg_no=car_data.get('regNo'),
                    chasis_no=car_data.get('chasisNo')
                )

            # Return updated lead data
            formatted_lead = lead_format([lead])[0]
            return Response(formatted_lead, status=status.HTTP_200_OK)

        except Lead.DoesNotExist:
            return Response(
                {"message": "Lead not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print("Error updating lead:", str(e))  # Debug print
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

def lead_format(leads):
    leads_data = [{
        'id': lead.lead_id or 'NA',
        'type': lead.lead_type or 'NA',
        'is_read':lead.is_read or False,

        'name': lead.customer.customer_name if lead.customer else 'NA',
        'vehicle': f"{lead.car.brand} {lead.car.model} {lead.car.year}" if lead.car else 'NA',
        'car': {
            'brand': lead.car.brand if lead.car else '',
            'model': lead.car.model if lead.car else '',
            'fuel': lead.car.fuel if lead.car else '',
            'variant': lead.car.variant if lead.car else '',
            'year': lead.car.year if lead.car else '',
            'chasis_no': lead.car.chasis_no if lead.car else '',
            'reg_no': lead.car.reg_no if lead.car else ''
        } if lead.car else None,

        'number': lead.customer.mobile_number if lead.customer else 'NA',
        'whatsapp_number': lead.customer.whatsapp_number if lead.customer else 'NA',
        'email': lead.customer.customer_email if lead.customer else 'NA',
        'source': lead.source or 'NA',
        'language_barrier':lead.customer.language_barrier or False,

        'address': lead.address or 'NA',
        'city': lead.city or 'NA',
        'state': lead.state or 'NA',
        'landmark': lead.landmark or 'NA',
        'building': lead.building or 'NA',
        'map_link': lead.map_link or 'NA',

        'lead_status': lead.lead_status or 'NA',
        'lead_type': lead.lead_type or 'NA',
        'arrival_mode': lead.arrival_mode or 'NA',
        'disposition': lead.disposition or 'NA',
        'arrival_time': lead.arrival_time if isinstance(lead.arrival_time, str) else lead.arrival_time.isoformat() if lead.arrival_time else '',
        'products': lead.products or 'NA',
        'estimated_price': lead.estimated_price or 'NA',

        'workshop_details': {
            'name': lead.workshop_details.get('name') if lead.workshop_details else '',
            'locality': lead.workshop_details.get('locality') if lead.workshop_details else '',
            'status': lead.workshop_details.get('status') if lead.workshop_details else '',
            'mobile': lead.workshop_details.get('mobile') if lead.workshop_details else '',
            'mechanic': lead.workshop_details.get('mechanic') if lead.workshop_details else '',
        } if lead.workshop_details else {},

        'orderId': lead.order.order_id if lead.order else 'NA',
        'regNumber': lead.car.reg_no if lead.car else 'NA',
        'status': lead.lead_status or 'NA',
        'cceName': lead.cce_name or 'NA',
        'caName': lead.ca_name or 'NA',
        'cceComments': lead.cce_comments or 'NA',
        'caComments': lead.ca_comments or 'NA',
        # 'arrivalDate': lead.arrival_time.strftime("%b %d,%Y,%H:%M") if lead.arrival_time else 'NA',
        'created_at': lead.created_at.isoformat() if lead.created_at else None,
        'updated_at': lead.created_at.isoformat() if lead.created_at else None,
    } for lead in leads]
    return leads_data

def paginate_leads(leads_queryset, page_number, items_per_page=5):
    """
    Helper function to paginate leads queryset
    """
    paginator = Paginator(leads_queryset, items_per_page)
    
    try:
        paginated_leads = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_leads = paginator.page(1)
    except EmptyPage:
        paginated_leads = paginator.page(paginator.num_pages)
    
    return {
        'leads': lead_format(paginated_leads),
        'total_pages': paginator.num_pages,
        'current_page': paginated_leads.number,
        'total_leads': paginator.count
    }


def generate_custom_lead_id(customer_number):
    # Get total leads count
    last_lead = Lead.objects.order_by('-created_at').first()
    if last_lead:
        # Split the lead_id and get the last segment
        seq_num = int(last_lead.lead_id.split('-')[-1]) + 1
    else:
        # If no leads exist, start with 1
        seq_num = 1
    # Format lead ID
    lead_id = f"L-{customer_number}-{seq_num}"
    return lead_id


@api_view(['POST'])
def create_lead_from_wordpress(request):
    try:
        with transaction.atomic():
            # Extract data from request
            data = request.data
            print('Received the 8888888888888888888888888888888888888 data:', data)
            car_details = data.get('car_details', {})
            user_number = data.get('user_number')

            # # Create or get customer
            customer, created = Customer.objects.get_or_create(
                mobile_number=user_number,
                defaults={'customer_name': 'Customer'}
            )

            # Check if the car already exists for this customer
            car_exists = Car.objects.filter(
                customer=customer,
                brand=car_details.get('car_name', '').strip(),
                model=car_details.get('car_model', '').strip()
            ).exists()

            # Create car
            if not car_exists:
                car = Car.objects.create(
                    customer=customer,
                    brand=car_details.get('car_name', '').strip(),
                    model=car_details.get('car_model', '').strip(),
                    year=car_details.get('car_year', ''),
                    fuel=car_details.get('fuel_type', '')
                )

             # Generate custom lead ID
            custom_lead_id = generate_custom_lead_id(customer.mobile_number)

            # Create lead
            lead = Lead.objects.create(
                lead_id=custom_lead_id,
                customer=customer,
                car=car,
                source='Website',
                service_type=data.get('service_type', ''),
                lead_status=' '
            )

            return Response({
                'status': 'success',
                # 'lead_id': lead.lead_id
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)