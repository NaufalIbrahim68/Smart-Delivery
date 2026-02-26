from django.contrib import admin
from .models import Delivery, Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Vendor model.
    """
    list_display = ('name', 'region', 'contact_email', 'contact_phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'region')
    search_fields = ('name', 'region', 'contact_email')
    list_editable = ('is_active',)
    ordering = ('name',)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Delivery model.
    """
    list_display = (
        'tracking_number',
        'vendor',
        'recipient_name',
        'status',
        'origin_city',
        'destination_city',
        'order_date',
        'scheduled_date',
        'actual_delivery_date',
        'weight_kg',
        'quantity',
    )
    list_filter = ('status', 'vendor', 'origin_city', 'destination_city')
    search_fields = ('tracking_number', 'recipient_name', 'origin_city', 'destination_city')
    ordering = ('-order_date',)
    date_hierarchy = 'order_date'

    # Organise the detail/edit form into logical sections
    fieldsets = (
        ('Tracking Info', {
            'fields': ('tracking_number', 'vendor', 'status')
        }),
        ('Route', {
            'fields': ('origin_city', 'destination_city')
        }),
        ('Dates', {
            'fields': ('order_date', 'scheduled_date', 'actual_delivery_date')
        }),
        ('Package & Recipient', {
            'fields': ('weight_kg', 'quantity', 'recipient_name', 'notes')
        }),
    )

    # Make computed properties visible in the list (read-only)
    readonly_fields = ('created_at', 'updated_at')
