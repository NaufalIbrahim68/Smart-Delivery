from django.urls import path
from . import views

app_name = 'deliveries'

urlpatterns = [
    # Phase 2 — Delivery Management
    path('', views.delivery_list, name='delivery_list'),
    path('delivery/<int:pk>/', views.delivery_detail, name='delivery_detail'),
    path('delivery/create/', views.delivery_create, name='delivery_create'),

    # Phase 3 — Excel Import
    path('import/', views.import_excel, name='import_excel'),

    # Phase 4 — Dashboard Analytics
    path('dashboard/', views.dashboard, name='dashboard'),

    # Phase 5 — AI Prediction
    path('predict/', views.predict_delay, name='predict_delay'),
]
