from django.contrib import admin
from .models import Profile, Customer, Order, Lead, Car, CarBrand, CarModel
from .models import  CarBrand, CarModel
from .models import Garage

class CarModelInline(admin.TabularInline):
    model = CarModel
    extra = 1

@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    inlines = [CarModelInline]

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'created_at', 'updated_at']
    list_filter = ['brand']
    search_fields = ['name', 'brand__name']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'is_caller']
    search_fields = ['user__username', 'status']
    list_filter = ['status','is_caller']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'mobile_number', 'created_at']
    search_fields = ['customer_name', 'mobile_number', 'customer_email']
    list_filter = ['created_at', 'language_barrier']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'created_at']
    search_fields = ['order_id',]
    list_filter = ['created_at']
    # Removed filter_horizontal = ['leads'] since the field doesn't exist anymore

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['brand', 'model', 'year', 'fuel', 'customer', 'created_at']
    search_fields = ['brand', 'model', 'reg_no', 'chasis_no']
    list_filter = ['brand', 'created_at']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['lead_id', 'customer', 'car', 'profile', 'order', 'lead_status', 'created_at']
    search_fields = ['lead_id', 'customer__customer_name', 'city']
    list_filter = ['lead_status', 'lead_type', 'city', 'created_at']
    fieldsets = (
        ('Relationships', {
            'fields': ('customer', 'profile', 'order', 'car')
        }),
        ('Basic Info', {
            'fields': ('lead_id', 'source', 'service_type', 'lead_type', 'estimated_price', 'products', 'ca_name', 'cce_name', 'ca_comments', 'cce_comments')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'building', 'landmark', 'map_link')
        }),
        ('Status', {
            'fields': ('lead_status', 'arrival_mode', 'disposition', 'arrival_time', 'is_read')
        }),
        ('Workshop', {
            'fields': ('workshop_details',)
        })
    )
    readonly_fields = ('lead_id',)



@admin.register(Garage)
class GarageAdmin(admin.ModelAdmin):
    list_display = ('name', 'mechanic', 'mobile', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'mechanic', 'locality', 'mobile')
    ordering = ('-created_at',)
    list_per_page = 20