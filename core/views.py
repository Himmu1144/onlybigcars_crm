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
from django.db.models import Q

from django.db import transaction
from .models import Customer, Lead, Profile, Order, Car, UserStatus
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count

from .models import CarBrand
from .serializers import CarBrandSerializer

from .models import Garage
from .serializers import GarageSerializer

from django.utils import timezone
from datetime import datetime, timedelta
import pytz


#  # Custom paginator function
# def custom_paginate_leads(leads_queryset, page_number, items_per_page=5):
#     total_leads = leads_queryset.count()
#     paginator = Paginator(leads_queryset, items_per_page)
    
#     try:
#         page_number = int(page_number)
#         paginated_leads = paginator.page(page_number)
#     except (PageNotAnInteger, ValueError):
#         paginated_leads = paginator.page(1)
#     except EmptyPage:
#         paginated_leads = paginator.page(paginator.num_pages)
    
#     return {
#         'leads': lead_format(paginated_leads),
#         'total_pages': paginator.num_pages,
#         'current_page': paginated_leads.number,
#         'total_leads': total_leads,
#         'leads_per_page': items_per_page
#     }


def custom_paginate_leads(leads_queryset, page_number, items_per_page=5):
    """
    Helper function to paginate leads queryset with additional validation
    """
    # print("\n=== PAGINATION DEBUGGING ===")
    # print(f"Total leads before pagination: {leads_queryset.count()}")
    # print(f"Requested page number: {page_number}")
    
    # Ensure we're working with a valid queryset
    if not leads_queryset.exists():
        return {
            'leads': [],
            'total_pages': 0,
            'current_page': 1,
            'total_leads': 0,
            'leads_per_page': items_per_page
        }

    # Create paginator
    paginator = Paginator(leads_queryset, items_per_page)
    total_leads = leads_queryset.count()
    total_pages = paginator.num_pages
    
    try:
        # Convert page_number to integer and validate
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        elif page_number > total_pages:
            page_number = total_pages
            
        paginated_leads = paginator.page(page_number)
        
        # Verify the leads on current page
        leads_on_page = list(paginated_leads)
        print(f"Leads on page {page_number}:")
        for lead in leads_on_page:
            print(f"- Lead ID: {lead.lead_id}, User: {lead.profile.user.username}")
            
    except (PageNotAnInteger, ValueError):
        print("Invalid page number, defaulting to page 1")
        paginated_leads = paginator.page(1)
        page_number = 1
    except EmptyPage:
        print(f"Page {page_number} is empty, showing last page")
        paginated_leads = paginator.page(paginator.num_pages)
        page_number = paginator.num_pages

    result = {
        'leads': lead_format(paginated_leads),
        'total_pages': total_pages,
        'current_page': page_number,
        'total_leads': total_leads,
        'leads_per_page': items_per_page
    }
    
    # print(f"Returning {len(result['leads'])} leads for page {result['current_page']}")
    # print(f"Total pages: {result['total_pages']}")
    # print("=== END PAGINATION DEBUGGING ===\n")
    
    return result

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def home_view(request):
    try:
        # Get 3 most recent leads
        page_number = request.GET.get('page', 1)
        recent_leads = Lead.objects.select_related('customer', 'profile', 'order').order_by('-created_at')
        garages = Garage.objects.filter(is_active=True).values('id', 'name', 'mechanic', 'locality','mobile')
        last_lead = Lead.objects.order_by('-created_at').first()
        if last_lead:
            # Split the lead_id and get the last segment
            seq_num = int(last_lead.lead_id.split('-')[-1]) + 1
        else:
            # If no leads exist, start with 1
            seq_num = 1

        

        # Get current logged in user
        current_user = request.user
        is_admin = current_user.is_superuser

        # Filter leads based on admin status
        if not is_admin:
            # Non-admins can only see their own leads
            recent_leads = Lead.objects.select_related('customer', 'profile', 'order')\
                .filter(cce_name=current_user.username)\
                .order_by('-created_at')

        try:
            # Get current month start and end dates
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # For month end, get the first day of next month and subtract 1 microsecond
            if now.month == 12:
                next_month = now.replace(year=now.year+1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month+1, day=1)
            month_end = next_month - timedelta(microseconds=1)

            # Filter leads by the current month
            user_completed_leads = Lead.objects.filter(
                profile__user=current_user,
                lead_status='Completed',
                created_at__gte=month_start,
                created_at__lte=month_end
            )
        except Exception as e:
            # Calculate statistics for the logged-in user's completed leads
            user_completed_leads = Lead.objects.filter(
                profile__user=current_user,
                lead_status='Completed'  # Assuming 'Completed' is the status value
            )
            print(f"Error filtering leads by month: {str(e)}")

        
        # Total count of completed leads by this user
        total_completed = user_completed_leads.count()
        
        # GMV - Sum of final_amount for all completed leads
        gmv = sum(lead.final_amount or 0 for lead in user_completed_leads)
        
        # Average Ticket Size (ATS) - GMV divided by number of leads
        ats = gmv / total_completed if total_completed > 0 else 0
        
        
        
        # pagination_data = paginate_leads(recent_leads, page_number)
        pagination_data = custom_paginate_leads(recent_leads, page_number)  # Using custom_paginate_leads here
        users = User.objects.all().values('id', 'username')
        users_data = list(users)
        print('this is the seq num', seq_num)
        return Response({
            "message": "Recent Leads",
            'seq_num': seq_num,
            **pagination_data,
            "users": list(users),
            "garages": list(garages),  # Add garages to response
            'is_admin': is_admin,
            'current_username': current_user.username,

            "user_stats": {
            "total_completed_leads": total_completed,
            "gmv": gmv,
            "ats": ats,
        }
        })
    except Exception as e:
        return Response({
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)  


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
            # leads = Lead.objects.filter(customer__customer_name__icontains=query)
            leads = Lead.objects.filter(
                Q(customer__customer_name__icontains=query) | 
                Q(car__reg_no__icontains=query)
            )
    else:
        query = query.strip()
        if (len(query) <= 10):
            leads = Lead.objects.filter(customer__mobile_number__icontains=query)
        else:
            leads = Lead.objects.filter(order__order_id__icontains=query)
        

    # Get current logged in user
    current_user = request.user
    is_admin = current_user.is_superuser
    # Filter leads based on admin status
    if not is_admin:
        # Non-admins can only see their own leads
        leads = leads.filter(cce_name=current_user.username)
    
    # Apply pagination
    pagination_data = custom_paginate_leads(leads, page_number)
    
    # Add admin status to response
    pagination_data.update({
        'is_admin': is_admin,
        'current_username': current_user.username,
    })
    
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
            overview_data = data['overview']
            customer_data = request.data.get('customerInfo')
            cars_data = request.data.get('cars', [])
            location_data = request.data.get('location')
            workshop_data = request.data.get('workshop')
            arrival_data = request.data.get('arrivalStatus')
            basic_data = request.data.get('basicInfo')

            # Check if customer exists
            try:
                customer = Customer.objects.get(mobile_number=customer_data['mobileNumber'])
                # Update customer information
                customer.customer_name = customer_data['customerName']
                customer.whatsapp_number = customer_data['whatsappNumber']
                customer.customer_email = customer_data['customerEmail']
                customer.language_barrier = customer_data['languageBarrier']
                customer.save()
            except Customer.DoesNotExist:
                # Create new customer
                customer = Customer.objects.create(
                    mobile_number=customer_data['mobileNumber'],
                    customer_name=customer_data['customerName'],
                    whatsapp_number=customer_data['whatsappNumber'],
                    customer_email=customer_data['customerEmail'],
                    language_barrier=customer_data['languageBarrier']
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


            # Initialize status history for new lead 18 feb
            initial_status = arrival_data.get('leadStatus')
            initial_status_history = [{
                'status': initial_status,
                'changed_by': request.user.username,
                'timestamp': timezone.now().astimezone(pytz.timezone('Asia/Kolkata')).isoformat()
            }] if initial_status else []

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
                discount=overview_data['discount'],
                afterDiscountAmount=overview_data['finalAmount'],
                estimated_price=basic_data['total'],
                # Workshop info
                workshop_details=workshop_data,
                ca_name=basic_data['caName'],
                cce_name=basic_data['cceName'],
                ca_comments=basic_data['caComments'],
                cce_comments=basic_data['cceComments'],
                status_history=initial_status_history,  # Add initial status history
                # Additional arrival
                final_amount=arrival_data.get('finalAmount', 0),
                battery_feature=arrival_data.get('batteryFeature', ''),
                commission_due=arrival_data.get('commissionDue', 0),
                commission_received=arrival_data.get('commissionReceived', 0),
                commission_percent=arrival_data.get('commissionPercent', 0),
                additional_work=arrival_data.get('additionalWork', ''),
                fuel_status=arrival_data.get('fuelStatus', ''),
                speedometer_rd=arrival_data.get('speedometerRd', ''),
                inventory=arrival_data.get('inventory', ''),
                # Store other data
                # products=table_data
            )

            try:

                # Create order if lead status is Complete
                if arrival_data['leadStatus'].lower() == 'job card':
                    # Check if lead already has an order
                    if not hasattr(lead, 'order') or lead.order is None:
                        print('This lead does not have any order as of yet.')
                        order_id = generate_order_id(customer_data['mobileNumber'])
                        order = Order.objects.create(
                            order_id=order_id,
                        )
                        
                        # Update lead with order reference
                        lead.order = order
                        lead.save()

            except Exception as e:
                print('Error saving data:', str(e))


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
    
    # Start with base queryset with all related fields
    query = Lead.objects.select_related(
        'customer', 
        'car', 
        'profile', 
        'profile__user', 
        'order'
    ).all()

    # Replace the existing garage filter code with this
    if filter_data.get('garage'):
        garage_names = filter_data['garage']
        print(f"\nApplying garage filter for: {garage_names}")
        print("Before garage filter count:", query.count())

        if isinstance(garage_names, list) and garage_names:
            # Filter using the contains operator for JSON field
            
            garage_q = Q()
            for name in garage_names:
                # Build OR conditions for each garage name
                garage_q |= Q(workshop_details__name=name)
            query = query.filter(garage_q)
        elif garage_names:  # Single string value
            query = query.filter(workshop_details__name=garage_names)

        print("After garage filter count:", query.count())
    
    print("\n=== FILTER DEBUGGING START ===")
    print(f"Initial query count: {query.count()}")
    print(f"Filter data received: {filter_data}")
    
    # User filter
    if filter_data.get('user'):
        username = filter_data['user']
        print(f"\nApplying user filter for: {username}")
        print("Before user filter count:", query.count())
        # Debug current usernames in query
        print("Current usernames in query:", list(query.values_list('profile__user__username', flat=True).distinct()))
        
        query = query.filter(profile__user__username=username)
        print("After user filter count:", query.count())
        # Verify filtered results
        filtered_usernames = list(query.values_list('profile__user__username', flat=True).distinct())
        print("Usernames after filter:", filtered_usernames)
        if username not in filtered_usernames:
            print(f"WARNING: Username {username} not found in filtered results!")
    
    # Source filter
    if filter_data.get('source'):
        source = filter_data['source']
        print(f"\nApplying source filter for: {source}")
        print("Before source filter count:", query.count())
        query = query.filter(source=source)
        print("After source filter count:", query.count())
        # Verify source values
        sources = list(query.values_list('source', flat=True).distinct())
        print("Sources in filtered results:", sources)
    
    # Status filter
    if filter_data.get('status'):
        status = filter_data['status']
        if status == 'Analytics':
            print('Stats Status Selected')
            query = query.filter(lead_status__in=['Completed', 'Commision Due'])
            
            # # Calculate commission totals
            # total_commission_due = sum(lead.commission_due or 0 for lead in query)
            # total_commission_received = sum(lead.commission_received or 0 for lead in query)
            # total_final_amount = sum(lead.final_amount or 0 for lead in query)
            
            # # Add these values to pagination_data later
            # pagination_data.update({
            #     'commission_stats': {
            #         'total_commission_due': total_commission_due,
            #         'total_commission_received': total_commission_received,
            #         # 'total_final_amount': total_final_amount
            #     }
            # })
            
            statuses = list(query.values_list('lead_status', flat=True).distinct())
        else:
            print(f"\nApplying status filter for: {status}")
            print("Before status filter count:", query.count())
            query = query.filter(lead_status=status)
            print("After status filter count:", query.count())
            # Verify statuses
            statuses = list(query.values_list('lead_status', flat=True).distinct())
            print("Statuses in filtered results:", statuses)
        
    # Location filter
    if filter_data.get('location'):
        location = filter_data['location']
        print(f"\nApplying location filter for: {location}")
        print("Before location filter count:", query.count())
        # Special case for Bangalore/Bengaluru
        if location == 'Bangalore':
            query = query.filter(Q(city='Bangalore') | Q(city='Bengaluru')) #28-2
        else:
            query = query.filter(city=location)
        print("After location filter count:", query.count())
        # Verify cities
        cities = list(query.values_list('city', flat=True).distinct())
        print("Cities in filtered results:", cities)
    
    # Language barrier filter
    if filter_data.get('language_barrier'):
        print("\nApplying language barrier filter")
        print("Before language barrier filter count:", query.count())
        query = query.filter(customer__language_barrier=True)
        print("After language barrier filter count:", query.count())
    
    # Arrival mode filter
    if filter_data.get('arrivalMode'):
        mode = filter_data['arrivalMode']
        print(f"\nApplying arrival mode filter for: {mode}")
        print("Before arrival mode filter count:", query.count())
        query = query.filter(arrival_mode=mode)
        print("After arrival mode filter count:", query.count())
    


    # Date range filter
    if filter_data.get('dateRange'):
        start_date = filter_data['dateRange'].get('startDate')
        end_date = filter_data['dateRange'].get('endDate')
        
        if start_date and end_date:
            print("\n=== DATE RANGE FILTER DEBUGGING ===")
            print(f"Input dates: start={start_date}, end={end_date}")
            print(f"Before filter - Total leads: {query.count()}")
            
            try:
                if start_date == end_date:
                    print(f"\n*** Both dates are same: {start_date} ***")
                    # Use __date lookup to filter by exact date without time
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(created_at__date=start_dt)
                    print(f"After single day filter - Total leads: {query.count()}")
                    
                    # Debug sample results for single day
                    sample_leads = query.values('lead_id', 'created_at')[:5]
                    print("\nSample leads for single day:")
                    for lead in sample_leads:
                        print(f"Lead ID: {lead['lead_id']}, Created: {lead['created_at']}")

                else:
                    # Convert and log datetime objects
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    print(f"\nInitial datetime objects:")
                    print(f"start_dt: {start_dt}")
                    print(f"end_dt: {end_dt}")
                    
                    # Add one day to end date and set time bounds
                    end_dt = end_dt + timedelta(days=1)
                    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                    print(f"\nAdjusted datetime objects:")
                    print(f"start_dt: {start_dt}")
                    print(f"end_dt: {end_dt}")
                    
                    # Make timezone aware
                    ist = pytz.timezone('Asia/Kolkata')
                    start_dt = timezone.make_aware(start_dt, ist)
                    end_dt = timezone.make_aware(end_dt, ist)
                    print(f"\nTimezone aware datetime objects (IST):")
                    print(f"start_dt: {start_dt}")
                    print(f"end_dt: {end_dt}")
                    
                    # Apply filter
                    query = query.filter(created_at__gte=start_dt, created_at__lte=end_dt)
                    print(f"\nAfter date range filter - Total leads: {query.count()}")
                    
                    
                    # Debug sample results for date range
                    sample_leads = query.values('lead_id', 'created_at')[:5]
                    print("\nSample leads for date range:")
                    for lead in sample_leads:
                        print(f"Lead ID: {lead['lead_id']}, Created: {lead['created_at']}")
                
            except ValueError as e:
                print(f"\nERROR: Date parsing failed - {str(e)}")
                return Response({
                    'error': f'Invalid date format: {str(e)}. Please use YYYY-MM-DD format.'
                }, status=400)
            except Exception as e:
                print(f"\nERROR: Unexpected error in date filtering - {str(e)}")
                return Response({
                    'error': f'Date filtering error: {str(e)}'
                }, status=400)
            finally:
                print("=== END DATE RANGE FILTER DEBUGGING ===\n")


    # Car type filter
    if filter_data.get('luxuryNormal'):
        car_type = filter_data['luxuryNormal']
        print(f"\nApplying car type filter for: {car_type}")
        print("Before car type filter count:", query.count())
        query = query.filter(lead_type=car_type)
        print("After car type filter count:", query.count())
    
    # Final ordering
    print("\nApplying final ordering")
    leads = query.order_by('-created_at')
    
    # # Double-check the filtering
    # print("\nVerifying final filtered results:")
    # print(f"Total leads after all filters: {leads.count()}")
    # unique_users = leads.values_list('profile__user__username', flat=True).distinct()
    # print(f"Unique users in filtered results: {list(unique_users)}")
    
    # # Apply pagination with extra validation
    # pagination_data = custom_paginate_leads(leads, page_number, items_per_page=5)
    
    # # Final verification
    # if pagination_data['leads']:
    #     print("\nVerifying leads in response:")
    #     for lead in pagination_data['leads']:
    #         print(f"Lead ID: {lead['id']}, User: {lead.get('profile__user__username', 'N/A')}")

    # Calculate the required values
    total_leads = leads.count()
    total_estimated_price = sum(lead.afterDiscountAmount if lead.afterDiscountAmount else lead.estimated_price or 0 for lead in leads)
    total_final_amount = sum(lead.final_amount or 0 for lead in leads)

    # Calculate per lead values
    est_price_per_lead = total_estimated_price / total_leads if total_leads > 0 else 0
    final_amount_per_lead = total_final_amount / total_leads if total_leads > 0 else 0

 



    # Double-check the filtering
    print("\nVerifying final filtered results:")
    print(f"Total leads after all filters: {total_leads}")
    unique_users = leads.values_list('profile__user__username', flat=True).distinct()
    print(f"Unique users in filtered results: {list(unique_users)}")

    # Apply pagination with extra validation
    pagination_data = custom_paginate_leads(leads, page_number, items_per_page=5)

    # Final verification
    if pagination_data['leads']:
        print("\nVerifying leads in response:")
        for lead in pagination_data['leads']:
            print(f"Lead ID: {lead['id']}, User: {lead.get('profile__user__username', 'N/A')}")

    if filter_data.get('status'):
        status = filter_data['status']
        if status == 'Analytics':
            # Calculate commission totals
            total_commission_due = sum(lead.commission_due or 0 for lead in query)
            total_commission_received = sum(lead.commission_received or 0 for lead in query)
            total_final_amount = sum(lead.final_amount or 0 for lead in query)
            
            # Add these values to pagination_data later
            pagination_data.update({
                'commission_stats': {
                    'total_commission_due': total_commission_due,
                    'total_commission_received': total_commission_received,
                    # 'total_final_amount': total_final_amount
                }
            })
            

    # Add the calculated values to the response
    pagination_data.update({
        'total_leads': total_leads,
        'total_estimated_price': total_estimated_price,
        'est_price_per_lead': est_price_per_lead,
        'total_final_amount': total_final_amount,
        'final_amount_per_lead': final_amount_per_lead
    })
        
    
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
    #     # print('The lead bc -   ', lead)
    #     # Use the same lead_format function
    #     formatted_lead = lead_format([lead])  # Pass a list to lead_format
    #     # print('This is the formatted lead', formatted_lead)
    #     return Response(formatted_lead)  # Return the first item from the list
    # except Lead.DoesNotExist:
    #     return Response(
    #         {"message": "Lead not found"}, 
    #         status=status.HTTP_404_NOT_FOUND
    #     )
    # Get user information
       # Get user information
        current_user = request.user
        is_admin = current_user.is_superuser
        
        # Format lead data
        formatted_lead = lead_format([lead])  
        
        # Return lead data with admin status and users
        return Response({
            '0': formatted_lead[0],  # Keep existing format
            'is_admin': is_admin,
            'users': list(User.objects.all().values('id', 'username'))
        })
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
            print('ca name bc - ', basic_data['cceName'])

            # Update customer
            if customer_data:
                customer = lead.customer
                customer.customer_name = customer_data.get('customerName', customer.customer_name)
                customer.mobile_number = customer_data.get('mobileNumber', customer.mobile_number)
                customer.whatsapp_number = customer_data.get('whatsappNumber', customer.whatsapp_number)
                customer.customer_email = customer_data.get('customerEmail', customer.customer_email)
                customer.language_barrier = customer_data.get('languageBarrier', customer.language_barrier)
                customer.save()

            # Replace the existing status history code (around line 773-790) with this:
            # status history handling
            new_status = arrival_data.get('leadStatus')
            old_status = lead.lead_status  # Get the previous status

            # Only add to history if there's a new status and it's different from the old one
            if new_status and new_status != old_status:
                # Initialize status_history if None
                if lead.status_history is None:
                    lead.status_history = []
                
                # Add new status entry
                status_entry = {
                    'status': new_status,
                    'changed_by': request.user.username,
                    'timestamp': timezone.now().astimezone(pytz.timezone('Asia/Kolkata')).isoformat()
                }
                
                lead.status_history.append(status_entry)

            # Get user information
            current_user = request.user
            is_admin = current_user.is_superuser

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
            lead.ca_name = basic_data.get('caName', lead.ca_name)
            if is_admin:
                lead.cce_name = basic_data.get('cceName', lead.cce_name)
            lead.products = overview_data.get('tableData', lead.products)
            lead.estimated_price = basic_data.get('total', lead.estimated_price)
            lead.final_amount = arrival_data.get('finalAmount', lead.final_amount)
            # lead.commission_due = arrival_data.get('commissionDue', lead.commission_due)
            # lead.commission_received = arrival_data.get('commissionReceived', lead.commission_received)
            # lead.commission_percent = arrival_data.get('commissionPercent', lead.commission_percent)
            lead.commission_due = arrival_data.get('commissionDue', 0) if arrival_data.get('commissionDue') != '' else 0
            lead.commission_received = arrival_data.get('commissionReceived', 0) if arrival_data.get('commissionReceived') != '' else 0
            lead.commission_percent = arrival_data.get('commissionPercent', 0) if arrival_data.get('commissionPercent') != '' else 0
            lead.battery_feature = arrival_data.get('batteryFeature', lead.battery_feature)
            lead.additional_work = arrival_data.get('additionalWork', lead.additional_work)
            lead.fuel_status = arrival_data.get('fuelStatus', lead.fuel_status)
            lead.speedometer_rd = arrival_data.get('speedometerRd', lead.speedometer_rd)
            lead.inventory = arrival_data.get('inventory', lead.inventory)
            lead.discount = overview_data.get('discount', lead.discount)
            lead.afterDiscountAmount = overview_data.get('finalAmount', lead.afterDiscountAmount)
            ist = pytz.timezone('Asia/Kolkata') # 18 feb
            lead.updated_at = timezone.now().astimezone(ist) # 18 feb
            lead.save()

            try:

                # Create order if lead status is Complete
                if arrival_data['leadStatus'].lower() == 'job card':
                    # Check if lead already has an order
                    if not hasattr(lead, 'order') or lead.order is None:
                        print('This lead does not have any order-')
                        order_id = generate_order_id(customer_data['mobileNumber'])
                        order = Order.objects.create(
                            order_id=order_id,
                        )
                        
                        # Update lead with order reference
                        lead.order = order
                        lead.save()

            except Exception as e:
                print('Error saving data:', str(e))


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

            # Return updated lead data with admin status
            formatted_lead = lead_format([lead])[0]
            
            
            print('ca name - ', lead.cce_name)
            
            return Response({
                '0': formatted_lead,  # Keep existing format
                'is_admin': is_admin,
                'users': list(User.objects.all().values('id', 'username'))
            }, status=status.HTTP_200_OK)
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
        'overview': {
            'tableData': lead.products or [],
            'total': float(lead.estimated_price) if lead.estimated_price else 0,
            'discount': float(lead.discount) if lead.discount is not None else 0,
            'finalAmount': float(lead.afterDiscountAmount) if lead.afterDiscountAmount is not None 
                else float(lead.estimated_price) if lead.estimated_price 
                else 0
        },


        'estimated_price': lead.estimated_price or 0,
        'final_amount': lead.final_amount or 0,
        'commission_due': lead.commission_due or 0,
        'commission_received': lead.commission_received or 0,
        'commission_percent': lead.commission_percent or 0,
        'battery_feature': lead.battery_feature or 'NA',
        'additional_work': lead.additional_work or 'NA',
        'fuel_status': lead.fuel_status or 'NA',
        'speedometer_rd': lead.speedometer_rd or 'NA',
        'inventory': lead.inventory or 'NA',


        'workshop_details': {
            'name': lead.workshop_details.get('name') if lead.workshop_details else '',
            'locality': lead.workshop_details.get('locality') if lead.workshop_details else '',
            'status': lead.workshop_details.get('status') if lead.workshop_details else '',
            'mobile': lead.workshop_details.get('mobile') if lead.workshop_details else '',
            'mechanic': lead.workshop_details.get('mechanic') if lead.workshop_details else '',
        } if lead.workshop_details else {},

        'status_history': lead.status_history or [], # 18 feb

        'orderId': lead.order.order_id if lead.order else 'NA',
        'regNumber': lead.car.reg_no if lead.car else 'NA',
        'vinNumber': lead.car.chasis_no if lead.car else 'NA', # 18 Feb
        'status': lead.lead_status or 'NA',
        'cceName': lead.cce_name or 'NA',
        'caName': lead.ca_name or 'NA',
        'cceComments': lead.cce_comments or 'NA',
        'caComments': lead.ca_comments or 'NA',
        # 'arrivalDate': lead.arrival_time.strftime("%b %d,%Y,%H:%M") if lead.arrival_time else 'NA',
        'created_at': lead.created_at.isoformat() if lead.created_at else None,
        'updated_at': lead.updated_at.isoformat() if lead.updated_at else None, # 18 feb
        'profile__user__username': lead.profile.user.username,
    } for lead in leads]
    return leads_data

# def paginate_leads(leads_queryset, page_number, items_per_page=5):
#     """
#     Helper function to paginate leads queryset
#     """
#     paginator = Paginator(leads_queryset, items_per_page)
    
#     try:
#         paginated_leads = paginator.page(page_number)
#     except PageNotAnInteger:
#         paginated_leads = paginator.page(1)
#     except EmptyPage:
#         paginated_leads = paginator.page(paginator.num_pages)
    
#     return {
#         'leads': lead_format(paginated_leads),
#         'total_pages': paginator.num_pages,
#         'current_page': paginated_leads.number,
#         'total_leads': paginator.count
#     }


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
            city = data.get('city')

            # # Create or get customer
            customer, created = Customer.objects.get_or_create(
                mobile_number=user_number,
                defaults={'customer_name': 'Customer'}
            )

            print('Customer - ', customer)

            # Check if the car already exists for this customer
            car = Car.objects.filter(
                customer=customer,
                brand=car_details.get('car_name', '').strip(),
                model=car_details.get('car_model', '').strip()
            ).first()

            # Create car
            if not car:
                car = Car.objects.create(
                    customer=customer,
                    brand=car_details.get('car_name', '').strip(),
                    model=car_details.get('car_model', '').strip(),
                    year=car_details.get('car_year', ''),
                    fuel=car_details.get('fuel_type', '')
                )

             # Generate custom lead ID
            custom_lead_id = generate_custom_lead_id(customer.mobile_number)

            dummy_table_data = [{"name": "Service Name", "type": "Service Type", "total": "0", "workdone": "wordone", "determined": False},]

            # 18 feb
            # profiles = Profile.objects.annotate(lead_count=Count('profile_leads')).order_by('lead_count')
            profiles = Profile.objects.filter(is_caller=True).annotate(lead_count=Count('profile_leads')).order_by('lead_count')
    
            # print("\n--- All Profiles with Lead Counts ---")
            # for profile in profiles:
            #     print(f"Profile: {profile.user.username}, Lead Count: {profile.lead_count}")
    
            # # Get profile with least leads
            # least_busy_profile = profiles.first()

            # Filter active profiles
            active_profiles = profiles.filter(user__userstatus__status='Active')

            if active_profiles.exists():
                print("\n--- Active Profiles with Lead Counts ---")
                for profile in active_profiles:
                    print(f"Profile: {profile.user.username}, Lead Count: {profile.lead_count}")
                # Get profile with least leads among active profiles
                least_busy_profile = active_profiles.first()
            else:
                print("\n--- No Active Profiles Found, Using All Profiles ---")
                for profile in profiles:
                    print(f"Profile: {profile.user.username}, Lead Count: {profile.lead_count}")
                # Get profile with least leads among all profiles
                least_busy_profile = profiles.first()



            print("\n--- Profile with Least Leads ---")
            print(f"Username: {least_busy_profile.user.username}")
            print(f"Lead Count: {least_busy_profile.lead_count}")

            
            
            try:
                print('Creating lead')
                # Create lead
                lead = Lead.objects.create(
                    lead_id=custom_lead_id,
                    customer=customer,
                    car=car,
                    city=city,
                    profile=least_busy_profile,
                    source='Website',
                    # source='Reference',
                    products=dummy_table_data,
                    estimated_price=0,
                    service_type=data.get('service_type', ''),
                    lead_status='Assigned',
                    cce_name=least_busy_profile.user.username,
                )
            except Exception as e:
                print('Error creating lead:', str(e))
                return Response({
                    'status': 'error',
                    'message': 'Error creating lead'
                }, status=status.HTTP_400_BAD_REQUEST)

            print(f'********** Lead - {lead} , Car - {car} **********, Customer - {customer}')

            return Response({
                'status': 'success',
                'lead_id': lead.lead_id
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_car_data(request):
    brands = CarBrand.objects.prefetch_related('models').all()
    serializer = CarBrandSerializer(brands, many=True)
    return Response(serializer.data)
    
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def garage_list(request):
    if request.method == 'GET':
        garages = Garage.objects.filter(is_active=True)
        serializer = GarageSerializer(garages, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = GarageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def garage_detail(request, pk):
    try:
        garage = Garage.objects.get(pk=pk)
    except Garage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = GarageSerializer(garage)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = GarageSerializer(garage, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        garage.is_active = False
        garage.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user_status(request):
    user = request.user
    status = request.data.get('status')
    
    if status not in ['Active', 'Break', 'Lunch', 'Training', 'Meeting', 'offline']:
        return Response({'error': 'Invalid status'}, status=400)
        
    user_status, created = UserStatus.objects.get_or_create(user=user)
    
    # Add to history before updating current status
    ist = pytz.timezone('Asia/Kolkata')
    current_time = timezone.now().astimezone(ist)
    current_date = current_time.date().isoformat()
    
    if current_date not in user_status.status_history:
        user_status.status_history[current_date] = []
    
    user_status.status_history[current_date].append({
        'status': status,
        'timestamp': current_time.isoformat()
    })
    
    user_status.status = status
    user_status.timestamp = current_time
    user_status.save()
    
    return Response({'status': status, 'timestamp': current_time.isoformat()})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_status(request):
    user = request.user
    try:
        user_status = UserStatus.objects.get(user=user)
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = user_status.timestamp.astimezone(ist)
        return Response({
            'status': user_status.status,
            'timestamp': timestamp.isoformat(),
            'history': user_status.status_history
        })
    except UserStatus.DoesNotExist:
        return Response({'status': 'offline'}, status=404)

# ---------------------------------------------------------------------


def generate_order_id(mobile_number):
    """Generate order ID in format: YYxxxxMMDDHHmm"""
    # Get current time in Asia/Kolkata timezone
    ist = pytz.timezone('Asia/Kolkata')
    now = timezone.now().astimezone(ist)
    
    year = now.strftime('%y')  # Last 2 digits of year
    month = now.strftime('%m')
    day = now.strftime('%d')
    hour = now.strftime('%H')
    minute = now.strftime('%M')
    
    # Get last 4 digits of mobile number
    last_four = mobile_number[-4:] if len(mobile_number) >= 4 else mobile_number.zfill(4)
    
    # Combine all parts
    order_id = f"{year}{last_four}{month}{day}{hour}{minute}"
    return order_id


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_customer_by_mobile(request, mobile_number):
    try:
        # Get customer and their most recent lead
        customer = Customer.objects.get(mobile_number=mobile_number)
        latest_lead = Lead.objects.filter(customer=customer).order_by('-created_at').first()
        
        data = {
            'customerName': customer.customer_name,
            'whatsappNumber': customer.whatsapp_number,
            'customerEmail': customer.customer_email,
            'languageBarrier': customer.language_barrier,
            'location': {
                'address': latest_lead.address if latest_lead else '',
                'city': latest_lead.city if latest_lead else '',
                'state': latest_lead.state if latest_lead else '',
                'buildingName': latest_lead.building if latest_lead else '',
                'landmark': latest_lead.landmark if latest_lead else '',
                'mapLink': latest_lead.map_link if latest_lead else ''
            } if latest_lead else {},
            'cars': [
                {
                    'carBrand': car.brand,
                    'carModel': car.model,
                    'year': car.year,
                    'fuel': car.fuel,
                    'variant': car.variant,
                    'chasisNo': car.chasis_no,
                    'regNo': car.reg_no
                } for car in customer.cars.all()
            ]
        }
        return Response(data)
    except Customer.DoesNotExist:
        return Response({'message': 'Customer not found'}, status=404)