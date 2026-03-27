from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from .models import Delivery, Vendor
from .forms import DeliveryForm, ExcelUploadForm
import os
import pandas as pd
import json
import io
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .services import PredictionService


# -----------------------------------------------
#  PHASE 2 -- Delivery Management
# -----------------------------------------------

@login_required
def delivery_list(request):
    """Step 5 + 8 -- List all deliveries with search, filter, and pagination."""
    deliveries = Delivery.objects.select_related('vendor').all()

    # Search
    query = request.GET.get('q', '')
    if query:
        deliveries = deliveries.filter(
            Q(tracking_number__icontains=query) |
            Q(recipient_name__icontains=query) |
            Q(origin_city__icontains=query) |
            Q(destination_city__icontains=query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)

    # Filter by date (order_date)
    date_filter = request.GET.get('date', '')
    if date_filter:
        deliveries = deliveries.filter(order_date=date_filter)

    # Pagination
    paginator = Paginator(deliveries, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    vendors = Vendor.objects.filter(is_active=True)
    status_choices = Delivery.STATUS_CHOICES

    context = {
        'deliveries': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'vendors': vendors,
        'status_choices': status_choices,
        'query': query,
        'status_filter': status_filter,
        'date_filter': date_filter,
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
    return render(request, 'deliveries/delivery_form.html', {'form': form, 'title': 'Create Delivery'})





@login_required
def export_pdf(request):
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    from datetime import datetime

    # ── 1. Apply Filters ─────────────────────────────────────────
    deliveries = Delivery.objects.select_related('vendor').all()
    query = request.GET.get('q', '')
    if query:
        deliveries = deliveries.filter(
            Q(tracking_number__icontains=query) |
            Q(recipient_name__icontains=query) |
            Q(origin_city__icontains=query) |
            Q(destination_city__icontains=query)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)
    date_filter = request.GET.get('date', '')
    if date_filter:
        deliveries = deliveries.filter(order_date=date_filter)

    # ── 2. Setup Response ─────────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="deliveries_export.pdf"'

    # ── 3. Color Palette ──────────────────────────────────────────
    DARK_BLUE   = colors.HexColor('#0f172a')
    ACCENT_BLUE = colors.HexColor('#2563eb')
    LIGHT_GRAY  = colors.HexColor('#f1f5f9')
    MID_GRAY    = colors.HexColor('#94a3b8')
    WHITE       = colors.white
    STATUS_COLORS = {
        'pending':    colors.HexColor('#f59e0b'),
        'in_transit': colors.HexColor('#3b82f6'),
        'delivered':  colors.HexColor('#10b981'),
        'delayed':    colors.HexColor('#ef4444'),
        'cancelled':  colors.HexColor('#6b7280'),
    }

    # ── 4. Custom paragraph styles ────────────────────────────────
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=20,
                                 textColor=WHITE, alignment=TA_LEFT, leading=24)
    style_sub   = ParagraphStyle('sub',   fontName='Helvetica',      fontSize=10,
                                 textColor=MID_GRAY, alignment=TA_LEFT)
    style_meta  = ParagraphStyle('meta',  fontName='Helvetica',      fontSize=8,
                                 textColor=MID_GRAY, alignment=TA_RIGHT)
    style_cell  = ParagraphStyle('cell',  fontName='Helvetica',      fontSize=8,
                                 textColor=DARK_BLUE, leading=10)
    style_hdr   = ParagraphStyle('hdr',   fontName='Helvetica-Bold', fontSize=8,
                                 textColor=WHITE)

    # ── 5. Build PDF with canvas for header/footer ─────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=25*mm, leftMargin=25*mm,
        topMargin=40*mm, bottomMargin=20*mm,
    )

    generated_on = datetime.now().strftime('%d %b %Y, %H:%M')
    total_records = deliveries.count()

    def draw_header_footer(canvas_obj, doc):
        canvas_obj.saveState()
        page_w, page_h = landscape(letter)

        # Header background
        canvas_obj.setFillColor(DARK_BLUE)
        canvas_obj.rect(0, page_h - 28*mm, page_w, 28*mm, fill=True, stroke=False)

        # Accent bar
        canvas_obj.setFillColor(ACCENT_BLUE)
        canvas_obj.rect(0, page_h - 29*mm, page_w, 1*mm, fill=True, stroke=False)

        # Logo placeholder circle
        canvas_obj.setFillColor(ACCENT_BLUE)
        canvas_obj.circle(25*mm, page_h - 14*mm, 8*mm, fill=True, stroke=False)
        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.drawCentredString(25*mm, page_h - 16*mm, 'SDS')

        # Title text
        canvas_obj.setFillColor(WHITE)
        canvas_obj.setFont('Helvetica-Bold', 18)
        canvas_obj.drawString(38*mm, page_h - 13*mm, 'Smart Delivery System')
        canvas_obj.setFillColor(MID_GRAY)
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawString(38*mm, page_h - 20*mm, 'Delivery Export Report')

        # Meta on right side of header
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(MID_GRAY)
        canvas_obj.drawRightString(page_w - 25*mm, page_h - 12*mm, f'Generated: {generated_on}')
        canvas_obj.drawRightString(page_w - 25*mm, page_h - 18*mm, f'Total Records: {total_records}')

        # Footer line
        canvas_obj.setStrokeColor(LIGHT_GRAY)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(25*mm, 14*mm, page_w - 25*mm, 14*mm)

        # Footer text
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(MID_GRAY)
        canvas_obj.drawString(25*mm, 9*mm, 'Smart Delivery System — Confidential Report')
        canvas_obj.drawRightString(page_w - 25*mm, 9*mm, f'Page {doc.page}')

        canvas_obj.restoreState()

    # ── 6. Build Table Data ────────────────────────────────────────
    headers = ['#', 'Tracking Number', 'Vendor', 'Status', 'Origin → Destination',
               'Order Date', 'Sched. Date', 'Qty', 'Recipient']
    table_data = [[Paragraph(h, style_hdr) for h in headers]]

    for idx, d in enumerate(deliveries, start=1):
        route = f"{d.origin_city} → {d.destination_city}"
        table_data.append([
            Paragraph(str(idx), style_cell),
            Paragraph(d.tracking_number, style_cell),
            Paragraph(d.vendor.name if d.vendor else '—', style_cell),
            Paragraph(d.get_status_display(), style_cell),
            Paragraph(route, style_cell),
            Paragraph(str(d.order_date), style_cell),
            Paragraph(str(d.scheduled_date), style_cell),
            Paragraph(str(d.quantity), style_cell),
            Paragraph(d.recipient_name, style_cell),
        ])

    col_widths = [15*mm, 45*mm, 35*mm, 30*mm, 60*mm, 28*mm, 28*mm, 15*mm, 40*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Build row-based style with alternating rows and status color
    tbl_style_cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0),  DARK_BLUE),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  WHITE),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  8),
        ('TOPPADDING',    (0, 0), (-1, 0),  8),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 7.5),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for row_idx, d in enumerate(deliveries, start=1):
        bg = LIGHT_GRAY if row_idx % 2 == 0 else WHITE
        tbl_style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))
        # Status cell color
        sc = STATUS_COLORS.get(d.status, MID_GRAY)
        tbl_style_cmds.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), sc))
        tbl_style_cmds.append(('FONTNAME',  (3, row_idx), (3, row_idx), 'Helvetica-Bold'))

    table.setStyle(TableStyle(tbl_style_cmds))

    # ── 7. Assemble elements ───────────────────────────────────────
    filter_info = []
    if query:        filter_info.append(f'Search: "{query}"')
    if status_filter: filter_info.append(f'Status: {status_filter.replace("_"," ").title()}')
    if date_filter:  filter_info.append(f'Date: {date_filter}')
    filter_text = '  |  '.join(filter_info) if filter_info else 'Showing all records'

    elements = [
        Spacer(1, 4*mm),
        Paragraph(filter_text, ParagraphStyle('fi', fontName='Helvetica', fontSize=8,
                                              textColor=MID_GRAY, alignment=TA_RIGHT)),
        Spacer(1, 3*mm),
        HRFlowable(width='100%', thickness=0.5, color=LIGHT_GRAY),
        Spacer(1, 4*mm),
        table,
    ]

    doc.build(elements, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)

    response.write(buffer.getvalue())
    return response




def track_delivery(request):
    """Phase 2B — Public Tracking"""
    tracking_number = request.GET.get('tracking_number', '').strip()
    delivery = None
    if tracking_number:
        delivery = Delivery.objects.filter(tracking_number=tracking_number).first()
        if not delivery:
            messages.warning(request, '⚠️ Tracking number not found.')

    # If AJAX / XHR request (from login page widget), return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if delivery:
            return JsonResponse({
                'found': True,
                'tracking_number': delivery.tracking_number,
                'status':          delivery.status,
                'status_display':  delivery.get_status_display(),
                'recipient_name':  delivery.recipient_name,
                'origin':          delivery.origin_city,
                'destination':     delivery.destination_city,
                'scheduled_date':  str(delivery.scheduled_date),
                'vendor':          delivery.vendor.name if delivery.vendor else None,
            })
        else:
            return JsonResponse({'found': False})

    return render(request, 'deliveries/track.html', {'delivery': delivery, 'tracking_number': tracking_number})


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

                # Map human-readable Excel headers to database field names
                column_mapping = {
                    'Tracking Number': 'tracking_number',
                    'Recipient Name': 'recipient_name',
                    'Origin City': 'origin_city',
                    'Destination City': 'destination_city',
                    'Order Date': 'order_date',
                    'Scheduled Date': 'scheduled_date',
                    'Weight (kg)': 'weight_kg',
                    'Quantity': 'quantity',
                    'Status': 'status',
                    'Vendor': 'vendor',
                    'Actual Delivery Date': 'actual_delivery_date',
                    'Notes': 'notes',
                }
                df.rename(columns=column_mapping, inplace=True)

                # Step 12: Validate required columns
                required_cols = [
                    'tracking_number', 'recipient_name', 'origin_city',
                    'destination_city', 'order_date', 'scheduled_date',
                    'weight_kg', 'quantity', 'status'
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
                            quantity=int(row['quantity']),
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

    # Build chart data for Chart.js — use json.dumps() for valid JSON (not Python list syntax)
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
        # Chart.js data — passed as Python objects, json_script handles encoding in template
        'status_labels': status_labels,
        'status_values': status_values,
        'vendor_names':  vendor_names,
        'vendor_totals': vendor_totals,
        'vendor_delays': vendor_delays,
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
                'quantity':       d.quantity,
                'origin_enc':     origin_enc,
                'dest_enc':       dest_enc,
                'vendor_enc':     vendor_enc,
                'is_delayed':     1 if d.is_delayed else 0,
            })

        df = pd.DataFrame(rows)
        X = df[['order_to_sched', 'weight_kg', 'quantity', 'origin_enc', 'dest_enc', 'vendor_enc']]
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
                quantity     = int(request.POST.get('quantity', 1))

                # Use DataFrame with feature names to match training format (avoids sklearn warning)
                features_df = pd.DataFrame([{
                    'order_to_sched': (sched_date - order_date).days,
                    'weight_kg':      weight,
                    'quantity':       quantity,
                    'origin_enc':     hash(origin) % 100,
                    'dest_enc':       hash(destination) % 100,
                    'vendor_enc':     hash(vendor_name) % 50,
                }])
                result = model.predict(features_df)[0]
                proba  = model.predict_proba(features_df)[0]
                prediction_result = {
                    'label':       'DELAYED' if result == 1 else 'ON TIME',
                    'is_delayed':  result == 1,
                    'confidence':  round(max(proba) * 100, 2),
                    'order_date':  order_date,
                    'sched_date':  sched_date,
                    'origin':      origin,
                    'destination': destination,
                    'vendor':      vendor_name or 'Unknown',
                    'weight':      weight,
                    'quantity':    quantity,
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


@csrf_exempt
def api_predict(request):
    """
    POST /api/predict/
    Input JSON: order_to_sched, weight_kg, quantity, origin_city, destination_city, vendor_name
    return prediction result (On Time / Late Risk)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        
        order_to_sched = data.get('order_to_sched')
        weight_kg = data.get('weight_kg')
        quantity = data.get('quantity')
        origin_city = data.get('origin_city')
        destination_city = data.get('destination_city')
        vendor_name = data.get('vendor_name')
        
        # Validation checks
        if any(v is None for v in [order_to_sched, weight_kg, quantity, origin_city, destination_city, vendor_name]):
            return JsonResponse({
                'error': 'Missing required fields: order_to_sched, weight_kg, quantity, origin_city, destination_city, vendor_name'
            }, status=400)
            
        # Encode strings for ML model
        origin_enc = hash(origin_city) % 100
        dest_enc = hash(destination_city) % 100
        vendor_enc = hash(vendor_name) % 50
            
        result = PredictionService.predict_delivery_risk(
            order_to_sched, weight_kg, quantity, origin_enc, dest_enc, vendor_enc
        )
        
        return JsonResponse({
            'prediction': result
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except FileNotFoundError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
