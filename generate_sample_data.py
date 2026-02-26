"""
Generate REALISTIC sample data where delays have actual patterns:
- Heavy packages + short schedule = more likely delayed
- Long distance routes = more likely delayed
- Certain vendors = more reliable than others
"""
import os
import sys
import django
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from deliveries.models import Vendor, Delivery

# Clear old sample data
Delivery.objects.all().delete()
print("Cleared old deliveries.")

# Vendors with reliability score (higher = more reliable)
vendors_data = {
    'JNE': 0.75,
    'SiCepat': 0.80,
    'Anteraja': 0.55,
    'J&T Express': 0.70,
    'Pos Indonesia': 0.45,
}
vendors = {}
for name, reliability in vendors_data.items():
    obj, _ = Vendor.objects.get_or_create(name=name)
    vendors[name] = {'obj': obj, 'reliability': reliability}

# City pairs with distance category
cities_near = [('Jakarta', 'Bandung'), ('Jakarta', 'Bekasi'), ('Surabaya', 'Semarang'),
               ('Yogyakarta', 'Semarang'), ('Jakarta', 'Depok')]
cities_medium = [('Jakarta', 'Surabaya'), ('Bandung', 'Semarang'), ('Jakarta', 'Yogyakarta'),
                 ('Surabaya', 'Yogyakarta'), ('Semarang', 'Bandung')]
cities_far = [('Jakarta', 'Makassar'), ('Jakarta', 'Medan'), ('Surabaya', 'Makassar'),
              ('Bandung', 'Medan'), ('Surabaya', 'Palembang')]

names = ['Budi Santoso', 'Siti Rahayu', 'Ahmad Fauzi', 'Dewi Lestari',
         'Rizky Pratama', 'Nurul Hidayah', 'Hendra Wijaya', 'Rina Marlina',
         'Eko Susanto', 'Fitriani Putri', 'Andi Saputra', 'Yuni Astuti']

created = 0
base_date = date(2024, 1, 1)

for i in range(1, 201):
    tracking = f"TRK-2024-{i:04d}"

    # Pick distance category
    dist_roll = random.random()
    if dist_roll < 0.33:
        origin, dest = random.choice(cities_near)
        dist_category = 'near'
    elif dist_roll < 0.66:
        origin, dest = random.choice(cities_medium)
        dist_category = 'medium'
    else:
        origin, dest = random.choice(cities_far)
        dist_category = 'far'

    # Pick vendor
    vendor_name = random.choice(list(vendors.keys()))
    vendor_info = vendors[vendor_name]

    # Package weight
    weight = round(random.uniform(0.3, 30.0), 2)

    # Scheduled delivery window
    order_date = base_date + timedelta(days=random.randint(0, 300))
    sched_days = random.randint(2, 10)
    scheduled = order_date + timedelta(days=sched_days)

    # ── DELAY PROBABILITY LOGIC ──────────────────────────
    # Base delay probability
    delay_prob = 0.15  # 15% base

    # Heavy package increases delay risk
    if weight > 20:
        delay_prob += 0.30
    elif weight > 10:
        delay_prob += 0.15
    elif weight > 5:
        delay_prob += 0.05

    # Far distance increases delay risk
    if dist_category == 'far':
        delay_prob += 0.25
    elif dist_category == 'medium':
        delay_prob += 0.10

    # Short schedule increases delay risk
    if sched_days <= 3:
        delay_prob += 0.25
    elif sched_days <= 5:
        delay_prob += 0.10

    # Unreliable vendor increases delay risk
    delay_prob += (1 - vendor_info['reliability']) * 0.3

    # Cap at 95%
    delay_prob = min(delay_prob, 0.95)

    # Determine if actually delayed
    is_delayed = random.random() < delay_prob

    if is_delayed:
        actual_delay = random.randint(1, 7)
        actual = scheduled + timedelta(days=actual_delay)
        status = 'delayed'
    else:
        # On time or early
        actual_offset = random.randint(-2, 0)
        actual = scheduled + timedelta(days=actual_offset)
        status = 'delivered'

    # Some still in transit or pending (no actual date)
    if random.random() < 0.15:
        actual = None
        status = random.choice(['pending', 'in_transit'])

    Delivery.objects.create(
        tracking_number=tracking,
        vendor=vendor_info['obj'],
        recipient_name=random.choice(names),
        origin_city=origin,
        destination_city=dest,
        order_date=order_date,
        scheduled_date=scheduled,
        actual_delivery_date=actual,
        weight_kg=weight,
        status=status,
    )
    created += 1

# Print summary
total = Delivery.objects.count()
delayed = Delivery.objects.filter(status='delayed').count()
delivered = Delivery.objects.filter(status='delivered').count()
other = total - delayed - delivered
print(f"\nCreated {created} deliveries:")
print(f"  Delivered (on time): {delivered}")
print(f"  Delayed:             {delayed}")
print(f"  Pending/In Transit:  {other}")
print(f"  Delay ratio:         {delayed}/{delayed+delivered} = {delayed/(delayed+delivered)*100:.1f}%")
print("\nNow go to /predict/ and click Train Model again!")
