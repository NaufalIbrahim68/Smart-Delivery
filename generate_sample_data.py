"""
Script to generate sample delivery data for testing.
Run with: python generate_sample_data.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import random
from datetime import date, timedelta
from deliveries.models import Vendor, Delivery

# ── Create Vendors ──────────────────────────────────────────
vendors_data = [
    {'name': 'JNE', 'region': 'Java', 'contact_email': 'cs@jne.co.id'},
    {'name': 'SiCepat', 'region': 'Java', 'contact_email': 'cs@sicepat.com'},
    {'name': 'Anteraja', 'region': 'Kalimantan', 'contact_email': 'cs@anteraja.id'},
    {'name': 'J&T Express', 'region': 'Sumatra', 'contact_email': 'cs@jet.co.id'},
    {'name': 'Pos Indonesia', 'region': 'Nationwide', 'contact_email': 'cs@posindonesia.co.id'},
]
vendors = []
for v in vendors_data:
    obj, created = Vendor.objects.get_or_create(name=v['name'], defaults=v)
    vendors.append(obj)
    print(f"  Vendor: {obj.name} ({'created' if created else 'exists'})")

# ── Create Deliveries ───────────────────────────────────────
cities = ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Makassar',
          'Semarang', 'Palembang', 'Yogyakarta', 'Depok', 'Bekasi']
names  = ['Budi Santoso', 'Siti Rahayu', 'Ahmad Fauzi', 'Dewi Lestari',
          'Rizky Pratama', 'Nurul Hidayah', 'Hendra Wijaya', 'Rina Marlina',
          'Eko Susanto', 'Fitriani Putri']
statuses = ['pending', 'in_transit', 'delivered', 'delayed', 'cancelled']

created_count = 0
base_date = date(2024, 1, 1)

for i in range(1, 101):
    tracking = f"TRK-2024-{i:04d}"
    if Delivery.objects.filter(tracking_number=tracking).exists():
        continue

    order_date   = base_date + timedelta(days=random.randint(0, 300))
    sched_offset = random.randint(3, 10)
    scheduled    = order_date + timedelta(days=sched_offset)

    status = random.choices(
        statuses, weights=[10, 20, 50, 15, 5], k=1
    )[0]

    actual = None
    if status in ('delivered', 'delayed'):
        delay = random.randint(-2, 5) if status == 'delayed' else random.randint(-1, 0)
        actual = scheduled + timedelta(days=delay)

    origin = random.choice(cities)
    dest   = random.choice([c for c in cities if c != origin])

    Delivery.objects.create(
        tracking_number=tracking,
        vendor=random.choice(vendors),
        recipient_name=random.choice(names),
        origin_city=origin,
        destination_city=dest,
        order_date=order_date,
        scheduled_date=scheduled,
        actual_delivery_date=actual,
        weight_kg=round(random.uniform(0.3, 25.0), 2),
        status=status,
    )
    created_count += 1

print(f"\n✅ Done! {created_count} deliveries created.")
print("You can now log in at http://127.0.0.1:8000/accounts/login/")
print("Username: admin | Password: admin123")
