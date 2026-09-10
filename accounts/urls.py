from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('fonctionnalites/', views.features_view, name='features'),
    path('contact/', views.contact_view, name='contact'),
    path('accounts/login/', views.RateLimitedLoginView.as_view(), name='login'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
]