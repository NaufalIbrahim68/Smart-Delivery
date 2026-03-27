import pandas as pd
import os

# Data for 10 sample deliveries
data = [
    {
        'tracking_number': 'TEST-001',
        'recipient_name': 'Ahmad Dahlan',
        'origin_city': 'Jakarta',
        'destination_city': 'Surabaya',
        'order_date': '2024-03-01',
        'scheduled_date': '2024-03-05',
        'weight_kg': 2.5,
        'quantity': 1,
        'status': 'delivered',
        'vendor': 'JNE',
        'actual_delivery_date': '2024-03-04',
        'notes': 'Fragile'
    },
    {
        'tracking_number': 'TEST-002',
        'recipient_name': 'Siti Hawa',
        'origin_city': 'Bandung',
        'destination_city': 'Jakarta',
        'order_date': '2024-03-02',
        'scheduled_date': '2024-03-04',
        'weight_kg': 1.0,
        'quantity': 2,
        'status': 'in_transit',
        'vendor': 'SiCepat',
        'actual_delivery_date': '',
        'notes': 'Please call before delivery'
    },
    {
        'tracking_number': 'TEST-003',
        'recipient_name': 'Budi Cahyono',
        'origin_city': 'Surabaya',
        'destination_city': 'Makassar',
        'order_date': '2024-03-02',
        'scheduled_date': '2024-03-08',
        'weight_kg': 15.5,
        'quantity': 3,
        'status': 'pending',
        'vendor': 'Pos Indonesia',
        'actual_delivery_date': '',
        'notes': 'Heavy package'
    },
    {
        'tracking_number': 'TEST-004',
        'recipient_name': 'Dewi Sri',
        'origin_city': 'Yogyakarta',
        'destination_city': 'Semarang',
        'order_date': '2024-03-03',
        'scheduled_date': '2024-03-05',
        'weight_kg': 0.5,
        'quantity': 1,
        'status': 'delivered',
        'vendor': 'J&T Express',
        'actual_delivery_date': '2024-03-05',
        'notes': ''
    },
    {
        'tracking_number': 'TEST-005',
        'recipient_name': 'Agus Purnomo',
        'origin_city': 'Jakarta',
        'destination_city': 'Medan',
        'order_date': '2024-03-03',
        'scheduled_date': '2024-03-07',
        'weight_kg': 5.0,
        'quantity': 5,
        'status': 'delayed',
        'vendor': 'Anteraja',
        'actual_delivery_date': '2024-03-09',
        'notes': 'Delayed due to weather'
    },
    {
        'tracking_number': 'TEST-006',
        'recipient_name': 'Rina Wati',
        'origin_city': 'Semarang',
        'destination_city': 'Surabaya',
        'order_date': '2024-03-04',
        'scheduled_date': '2024-03-06',
        'weight_kg': 3.2,
        'quantity': 2,
        'status': 'in_transit',
        'vendor': 'SiCepat',
        'actual_delivery_date': '',
        'notes': ''
    },
    {
        'tracking_number': 'TEST-007',
        'recipient_name': 'Eko Prasetyo',
        'origin_city': 'Medan',
        'destination_city': 'Jakarta',
        'order_date': '2024-03-05',
        'scheduled_date': '2024-03-10',
        'weight_kg': 8.0,
        'quantity': 1,
        'status': 'pending',
        'vendor': 'JNE',
        'actual_delivery_date': '',
        'notes': 'Electronics'
    },
    {
        'tracking_number': 'TEST-008',
        'recipient_name': 'Nadia Safitri',
        'origin_city': 'Makassar',
        'destination_city': 'Bandung',
        'order_date': '2024-03-05',
        'scheduled_date': '2024-03-12',
        'weight_kg': 2.1,
        'quantity': 4,
        'status': 'in_transit',
        'vendor': 'J&T Express',
        'actual_delivery_date': '',
        'notes': ''
    },
    {
        'tracking_number': 'TEST-009',
        'recipient_name': 'Hendra Gunawan',
        'origin_city': 'Jakarta',
        'destination_city': 'Bandung',
        'order_date': '2024-03-06',
        'scheduled_date': '2024-03-07',
        'weight_kg': 4.5,
        'quantity': 2,
        'status': 'delivered',
        'vendor': 'SiCepat',
        'actual_delivery_date': '2024-03-07',
        'notes': 'Next day delivery'
    },
    {
        'tracking_number': 'TEST-010',
        'recipient_name': 'Lestari Indah',
        'origin_city': 'Surabaya',
        'destination_city': 'Jakarta',
        'order_date': '2024-03-06',
        'scheduled_date': '2024-03-09',
        'weight_kg': 22.0,
        'quantity': 10,
        'status': 'delayed',
        'vendor': 'Pos Indonesia',
        'actual_delivery_date': '2024-03-12',
        'notes': 'Bulk shipment'
    },
]

df = pd.DataFrame(data)

# Rename columns to human-readable Excel headers
df.rename(columns={
    'tracking_number': 'Tracking Number',
    'recipient_name': 'Recipient Name',
    'origin_city': 'Origin City',
    'destination_city': 'Destination City',
    'order_date': 'Order Date',
    'scheduled_date': 'Scheduled Date',
    'weight_kg': 'Weight (kg)',
    'quantity': 'Quantity',
    'status': 'Status',
    'vendor': 'Vendor',
    'actual_delivery_date': 'Actual Delivery Date',
    'notes': 'Notes',
}, inplace=True)

# Export to Excel
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_import.xlsx')
df.to_excel(file_path, index=False)
print(f"Created sample Excel file at: {file_path}")
