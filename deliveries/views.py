from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from .models import Delivery, Vendor
from .forms import DeliveryForm, ExcelUploadForm
import pandas as pd
import os


# ─────────────────────────────────────────────
#  PHASE 2 — Delivery Management
# ─────────────────────────────────────────────

@login_required
def delivery_list(request):
    """Step 5 + 8 — List all deliveries with search and filter."""
    deliveries = Delivery.objects.select_related('vendor').all()

    # Step 8: Search
    query = request.GET.get('q', '')
    if query:
        deliveries = deliveries.filter(
            Q(tracking_number__icontains=query) |
            Q(recipient_name__icontains=query) |
            Q(origin_city__icontains=query) |
            Q(destination_city__icontains=query)
        )

    # Step 8: Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)

    # Step 8: Filter by vendor
    vendor_filter = request.GET.get('vendor', '')
    if vendor_filter:
        deliveries = deliveries.filter(vendor_id=vendor_filter)

    vendors = Vendor.objects.filter(is_active=True)
    status_choices = Delivery.STATUS_CHOICES

    context = {
        'deliveries': deliveries,
        'vendors': vendors,
        'status_choices': status_choices,
        'query': query,
        'status_filter': status_filter,
        'vendor_filter': vendor_filter,
    }
    return render(request, 'deliveries/delivery_list.html', context)


@login_required
def delivery_detail(request, pk):
    """Step 6 — Show detail of a single delivery."""
    delivery = get_object_or_404(Delivery, pk=pk)
    return render(request, 'deliveries/delivery_detail.html', {'delivery': delivery})


@login_required
def delivery_create(request):
    """Step 7 — Create a new delivery via a form."""
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            delivery = form.save()
            messages.success(request, f'✅ Delivery {delivery.tracking_number} created successfully!')
            return redirect('deliveries:delivery_list')
    else:
        form = DeliveryForm()
    return render(request, 'deliveries/delivery_form.html', {'form': form})


# ─────────────────────────────────────────────
#  PHASE 3 — Excel Import (Steps 9–12)
# ─────────────────────────────────────────────

@login_required
def import_excel(request):
    """Step 9–12 — Upload and import deliveries from an Excel file."""
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file, engine='openpyxl')

                # Step 12: Validate required columns
                required_cols = [
                    'tracking_number', 'recipient_name', 'origin_city',
                    'destination_city', 'order_date', 'scheduled_date',
                    'weight_kg', 'status'
                ]
                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    messages.error(request, f'❌ Missing columns: {", ".join(missing)}')
                    return redirect('deliveries:import_excel')

                created, skipped, errors = 0, 0, []

                for index, row in df.iterrows():
                    row_num = index + 2  # Excel row (1=header, so data starts at 2)
                    tracking = str(row.get('tracking_number', '')).strip()

                    if not tracking or tracking == 'nan':
                        errors.append(f'Row {row_num}: Missing tracking number')
                        continue

                    if Delivery.objects.filter(tracking_number=tracking).exists():
                        skipped += 1
                        continue

                    try:
                        # Resolve vendor by name
                        vendor = None
                        vendor_name = str(row.get('vendor', '')).strip()
                        if vendor_name and vendor_name != 'nan':
                            vendor, _ = Vendor.objects.get_or_create(name=vendor_name)

                        Delivery.objects.create(
                            tracking_number=tracking,
                            vendor=vendor,
                            recipient_name=str(row.get('recipient_name', '')).strip(),
                            origin_city=str(row.get('origin_city', '')).strip(),
                            destination_city=str(row.get('destination_city', '')).strip(),
                            order_date=pd.to_datetime(row['order_date']).date(),
                            scheduled_date=pd.to_datetime(row['scheduled_date']).date(),
                            actual_delivery_date=pd.to_datetime(row['actual_delivery_date']).date()
                                if pd.notna(row.get('actual_delivery_date')) else None,
                            weight_kg=float(row.get('weight_kg', 0)),
                            status=str(row.get('status', 'pending')).strip().lower(),
                            notes=str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else '',
                        )
                        created += 1
                    except Exception as e:
                        errors.append(f'Row {row_num}: {e}')

                if created:
                    messages.success(request, f'✅ {created} deliveries imported, {skipped} skipped (duplicates).')
                if errors:
                    for err in errors[:5]:  # Show max 5 errors
                        messages.warning(request, err)

                return redirect('deliveries:delivery_list')

            except Exception as e:
                messages.error(request, f'❌ Failed to read Excel file: {e}')
    else:
        form = ExcelUploadForm()

    return render(request, 'deliveries/import_excel.html', {'form': form})


# ─────────────────────────────────────────────
#  PHASE 4 — Dashboard Analytics (Steps 13–16)
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    """Steps 13-16 -- Analytics dashboard with statistics and charts."""
    total = Delivery.objects.count()

    # Build status counts WITH display labels (to avoid |replace filter in template)
    status_display_map = dict(Delivery.STATUS_CHOICES)
    raw_counts = Delivery.objects.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in raw_counts}

    # Full list including statuses with 0 count
    status_counts = [
        {
            'status': code,
            'label': label,
            'count': status_map.get(code, 0),
        }
        for code, label in Delivery.STATUS_CHOICES
        if status_map.get(code, 0) > 0  # only show statuses that have data
    ]

    vendor_stats = (
        Delivery.objects
        .values('vendor__name')
        .annotate(total=Count('id'), delayed=Count('id', filter=Q(status='delayed')))
        .order_by('-total')[:10]
    )

    # Build chart data for Chart.js
    status_labels = [s[1] for s in Delivery.STATUS_CHOICES]
    status_values = [status_map.get(code, 0) for code, _ in Delivery.STATUS_CHOICES]

    vendor_names  = [v['vendor__name'] or 'Unknown' for v in vendor_stats]
    vendor_totals = [v['total'] for v in vendor_stats]
    vendor_delays = [v['delayed'] for v in vendor_stats]

    # Recent deliveries
    recent_deliveries = Delivery.objects.select_related('vendor').order_by('-created_at')[:5]

    context = {
        'total': total,
        'status_counts': status_counts,
        'vendor_stats': vendor_stats,
        'recent_deliveries': recent_deliveries,
        # Chart.js data
        'status_labels':  status_labels,
        'status_values':  status_values,
        'vendor_names':   vendor_names,
        'vendor_totals':  vendor_totals,
        'vendor_delays':  vendor_delays,
    }
    return render(request, 'deliveries/dashboard.html', context)


# ─────────────────────────────────────────────
#  PHASE 5 — AI Prediction (Steps 17–21)
# ─────────────────────────────────────────────

@login_required
def predict_delay(request):
    """Steps 17–21 — Train ML model and predict delivery delay."""
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from django.conf import settings as django_settings

    MODEL_PATH = os.path.join(django_settings.BASE_DIR, 'delay_model.pkl')
    prediction_result = None
    accuracy = None
    model_trained = os.path.exists(MODEL_PATH)

    # ── Train action ──────────────────────────────────
    if request.method == 'POST' and 'train' in request.POST:
        qs = Delivery.objects.exclude(actual_delivery_date=None).exclude(scheduled_date=None)
        if qs.count() < 10:
            messages.warning(request, '⚠️ Not enough data to train (need at least 10 completed deliveries).')
            return redirect('deliveries:predict_delay')

        rows = []
        for d in qs:
            order_to_sched = (d.scheduled_date - d.order_date).days
            origin_enc = hash(d.origin_city) % 100
            dest_enc   = hash(d.destination_city) % 100
            vendor_enc = hash(d.vendor.name if d.vendor else 'unknown') % 50
            rows.append({
                'order_to_sched': order_to_sched,
                'weight_kg':      float(d.weight_kg),
                'origin_enc':     origin_enc,
                'dest_enc':       dest_enc,
                'vendor_enc':     vendor_enc,
                'is_delayed':     1 if d.is_delayed else 0,
            })

        df = pd.DataFrame(rows)
        X = df[['order_to_sched', 'weight_kg', 'origin_enc', 'dest_enc', 'vendor_enc']]
        y = df['is_delayed']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        accuracy = round(accuracy_score(y_test, model.predict(X_test)) * 100, 2)

        joblib.dump(model, MODEL_PATH)
        messages.success(request, f'✅ Model trained! Accuracy: {accuracy}%')
        model_trained = True

    # ── Predict action ───────────────────────────────
    elif request.method == 'POST' and 'predict' in request.POST:
        if not model_trained:
            messages.error(request, '❌ Train the model first.')
        else:
            try:
                model = joblib.load(MODEL_PATH)
                order_date   = pd.to_datetime(request.POST.get('order_date')).date()
                sched_date   = pd.to_datetime(request.POST.get('scheduled_date')).date()
                origin       = request.POST.get('origin_city', '')
                destination  = request.POST.get('destination_city', '')
                vendor_name  = request.POST.get('vendor_name', '')
                weight       = float(request.POST.get('weight_kg', 1))

                features = [[
                    (sched_date - order_date).days,
                    weight,
                    hash(origin) % 100,
                    hash(destination) % 100,
                    hash(vendor_name) % 50,
                ]]
                result = model.predict(features)[0]
                proba  = model.predict_proba(features)[0]
                prediction_result = {
                    'label':       'DELAYED' if result == 1 else 'ON TIME',
                    'is_delayed':  result == 1,
                    'confidence':  round(max(proba) * 100, 2),
                }
            except Exception as e:
                messages.error(request, f'❌ Prediction error: {e}')

    vendors = Vendor.objects.filter(is_active=True)
    return render(request, 'deliveries/predict_delay.html', {
        'model_trained':     model_trained,
        'prediction_result': prediction_result,
        'accuracy':          accuracy,
        'vendors':           vendors,
    })
