from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/edit-form-submit/', views.edit_form_submit, name='edit_form_submit'),
    path('api/leads/search/', views.search_leads, name='search_leads'),
    path('api/leads/filter/', views.filter_leads, name='filter_leads'),
    path('api/leads/<str:id>/', views.get_lead, name='get_lead'),  # Change <int:id> to <str:id>
    path('api/leads/<str:id>/update/', views.update_lead, name='update_lead'),  # Change <int:id> to <str:id>
    path('api/create-lead-wordpress/', views.create_lead_from_wordpress, name='create_lead_wordpress'),
]