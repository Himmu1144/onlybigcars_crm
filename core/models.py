import uuid
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, null=True, blank=True)
    is_caller = models.BooleanField(default=False) 
    # leads = models.ManyToManyField('Lead', blank=True, related_name='assigned_profiles')
    # orders = models.ManyToManyField('Order', blank=True, related_name='assigned_profiles')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_profile')
        ]

    def __str__(self):
        return self.user.username

class Customer(models.Model):
    mobile_number = models.CharField(max_length=15, unique=True)  # Made unique
    customer_name = models.CharField(max_length=100)
    whatsapp_number = models.CharField(max_length=15, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    language_barrier = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_name} - {self.mobile_number}"

class Order(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    # customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_orders')
    # profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='profile_orders')
    # order_details = models.JSONField(null=True, blank=True)
    # leads = models.ManyToManyField('Lead', blank=True, related_name='related_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id}"

    # def get_customers(self):
    #     """Helper method to get related customers"""
    #     return self.customers.all()
    
class Car(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cars')
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.CharField(max_length=4)
    fuel = models.CharField(max_length=1000,null=True, blank=True)
    variant = models.CharField(max_length=100, null=True, blank=True)
    chasis_no = models.CharField(max_length=100, null=True, blank=True)
    reg_no = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

class Lead(models.Model):
    # Add this method to generate lead_id
    def generate_lead_id():
        return str(uuid.uuid4()).split('-')[0].upper()

    lead_id = models.CharField(
        max_length=100, 
        unique=True,
        default=generate_lead_id,
        editable=False
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_leads')
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, related_name='leads')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='profile_leads')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name='order_leads')
    
    # Basic Information
    source = models.CharField(max_length=100, null=True, blank=True)
    service_type = models.CharField(max_length=100, null=True, blank=True)
    products = models.JSONField(null=True, blank=True)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lead_type = models.CharField(max_length=50, null=True, blank=True)

    # Location Information
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    building = models.CharField(max_length=200, null=True, blank=True)
    landmark = models.CharField(max_length=200, null=True, blank=True)
    map_link = models.CharField(max_length=200, null=True, blank=True)

    # Status and Timing
    lead_status = models.CharField(max_length=100, null=True, blank=True)
    arrival_mode = models.CharField(max_length=100, null=True, blank=True)
    disposition = models.CharField(max_length=100, null=True, blank=True)
    arrival_time = models.DateTimeField(null=True, blank=True)

    # Workshop Details
    workshop_details = models.JSONField(null=True, blank=True)
    ca_name = models.CharField(max_length=100, null=True, blank=True)
    ca_comments = models.TextField(null=True, blank=True)
    cce_name = models.CharField(max_length=100, null=True, blank=True)
    # cce = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='assigned_leads')
    cce_comments = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False,)

    def __str__(self):
        return f"Lead {self.lead_id}"
    
# updated some code here
class CarBrand(models.Model):
    name= models.CharField(max_length=100, unique= True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__ (self):
        return self.name
    
class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['brand', 'name']

    def __str__(self):
        return f"{self.brand.name} - {self.name}"
    
class Garage(models.Model):
    name = models.CharField(max_length=200)
    mechanic = models.CharField(max_length=100)
    locality = models.TextField()
    link = models.URLField(blank=True, null=True)
    mobile = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Garage'
        verbose_name_plural = 'Garages'

    def __str__(self):
        return self.name

