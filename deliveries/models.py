from django.db import models


class Vendor(models.Model):
    """
    Represents a logistics vendor (shipping company).
    Example: JNE, TIKI, SiCepat, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Primary operating region of the vendor (e.g. Java, Sumatra)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'

    def __str__(self):
        return self.name


class Delivery(models.Model):
    """
    Represents a single delivery order tracked in the system.
    """

    # --- Status Choices ---
    STATUS_PENDING = 'pending'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_DELAYED = 'delayed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_DELAYED, 'Delayed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # --- Core Fields ---
    tracking_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique tracking number for this delivery"
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deliveries',
        help_text="The vendor handling this delivery"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    # --- Location Fields ---
    origin_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)

    # --- Date Fields ---
    order_date = models.DateField(help_text="Date the order was placed")
    scheduled_date = models.DateField(
        help_text="Expected delivery date agreed with vendor"
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual date the delivery was completed (leave blank if pending)"
    )

    # --- Package Details ---
    weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Package weight in kilograms"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Number of items in this delivery"
    )
    recipient_name = models.CharField(max_length=150)
    notes = models.TextField(blank=True, null=True)

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'

    def __str__(self):
        return f"{self.tracking_number} — {self.recipient_name} [{self.get_status_display()}]"

    @property
    def is_delayed(self):
        """Returns True if actual delivery date exceeded the scheduled date."""
        if self.actual_delivery_date and self.scheduled_date:
            return self.actual_delivery_date > self.scheduled_date
        return False

    @property
    def delay_days(self):
        """
        Returns number of days delayed (positive = late, negative = early).
        Returns None if actual delivery date is not yet recorded.
        """
        if self.actual_delivery_date and self.scheduled_date:
            delta = self.actual_delivery_date - self.scheduled_date
            return delta.days
        return None
