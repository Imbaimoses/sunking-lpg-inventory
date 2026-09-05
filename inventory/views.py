from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation

from .forms import CylinderScanInForm
from .models import Cylinder, CylinderTransaction


def dashboard(request):

    active_cylinders = Cylinder.objects.filter(
        is_active=True
    )

    total_cylinders = active_cylinders.count()

    full_cylinders = active_cylinders.filter(
        status="FULL"
    ).count()

    empty_cylinders = active_cylinders.filter(
        status="EMPTY"
    ).count()

    paygo_cylinders = active_cylinders.filter(
        brand__iexact="PayGo"
    ).count()

    wajiko_cylinders = active_cylinders.filter(
        brand__iexact="Wajiko"
    ).count()

    greenwells_cylinders = active_cylinders.filter(
        brand__iexact="GreenWells"
    ).count()

    recent_transactions = (
        CylinderTransaction.objects
        .select_related("cylinder")
        .order_by("-created_at")[:10]
    )

    context = {
        "total_cylinders": total_cylinders,
        "full_cylinders": full_cylinders,
        "empty_cylinders": empty_cylinders,
        "paygo_cylinders": paygo_cylinders,
        "wajiko_cylinders": wajiko_cylinders,
        "greenwells_cylinders": greenwells_cylinders,
        "recent_transactions": recent_transactions,
    }

    return render(
        request,
        "inventory/dashboard.html",
        context
    )


# ============================================================
# FAST SCAN IN
# ============================================================

def scan_in(request):

    return render(
        request,
        "inventory/scan_in.html"
    )


@require_POST
def fast_scan_in(request):

    serial_number = request.POST.get(
        "serial_number",
        ""
    ).strip().upper()

    weight = request.POST.get(
        "weight",
        ""
    ).strip()

    brand = request.POST.get(
        "brand",
        ""
    ).strip()

    status = request.POST.get(
        "status",
        ""
    ).strip()

    # --------------------------------------------------------
    # SERIAL VALIDATION
    # --------------------------------------------------------

    if not serial_number:

        return JsonResponse({
            "success": False,
            "message": "Please scan a cylinder."
        })

    if not serial_number.startswith("GLP"):

        return JsonResponse({
            "success": False,
            "message": (
                "Invalid cylinder number. "
                "Cylinder numbers must begin with GLP."
            )
        })

    # --------------------------------------------------------
    # BRAND VALIDATION
    # --------------------------------------------------------

    allowed_brands = [
        "PayGo",
        "Wajiko",
        "GreenWells",
    ]

    if brand not in allowed_brands:

        return JsonResponse({
            "success": False,
            "message": "Please select a valid cylinder brand."
        })

    # --------------------------------------------------------
    # STATUS VALIDATION
    # --------------------------------------------------------

    if status not in ["FULL", "EMPTY"]:

        return JsonResponse({
            "success": False,
            "message": "Please select Full or Empty."
        })

    # --------------------------------------------------------
    # WEIGHT VALIDATION
    # --------------------------------------------------------

    if not weight:

        return JsonResponse({
            "success": False,
            "message": "Please enter the cylinder weight."
        })

    try:

        cylinder_weight = Decimal(weight)

    except (InvalidOperation, ValueError):

        return JsonResponse({
            "success": False,
            "message": "Invalid weight."
        })

    if cylinder_weight <= 0:

        return JsonResponse({
            "success": False,
            "message": "Weight must be greater than zero."
        })

    # --------------------------------------------------------
    # DUPLICATE CHECK
    # --------------------------------------------------------

    existing = Cylinder.objects.filter(
        Q(serial_number__iexact=serial_number)
        | Q(barcode__iexact=serial_number)
    ).first()

    if existing:

        if existing.is_active:

            return JsonResponse({
                "success": False,
                "message": (
                    f"{existing.serial_number} is already "
                    "in active inventory."
                )
            })

        # Existing cylinder was previously removed.
        # We can bring it back into inventory.
        try:

            with transaction.atomic():

                existing.serial_number = serial_number
                existing.barcode = serial_number
                existing.weight = cylinder_weight
                existing.brand = brand
                existing.status = status
                existing.is_active = True

                existing.save()

                CylinderTransaction.objects.create(
                    cylinder=existing,
                    transaction_type="IN",
                    destination="WAREHOUSE",
                    weight=cylinder_weight
                )

        except ValidationError as error:

            return JsonResponse({
                "success": False,
                "message": get_validation_message(error)
            })

        return JsonResponse({
            "success": True,
            "message": (
                f"{serial_number} successfully received "
                "back into inventory."
            ),
            "cylinder": {
                "id": existing.id,
                "serial_number": existing.serial_number,
                "weight": str(existing.weight),
                "brand": existing.brand,
                "status": existing.status,
            }
        })

    # --------------------------------------------------------
    # NEW CYLINDER
    # --------------------------------------------------------

    try:

        with transaction.atomic():

            cylinder = Cylinder.objects.create(
                serial_number=serial_number,
                barcode=serial_number,
                weight=cylinder_weight,
                brand=brand,
                status=status,
                is_active=True
            )

            # Permanent IN transaction history
            CylinderTransaction.objects.create(
                cylinder=cylinder,
                transaction_type="IN",
                destination="WAREHOUSE",
                weight=cylinder_weight
            )

    except ValidationError as error:

        return JsonResponse({
            "success": False,
            "message": get_validation_message(error)
        })

    return JsonResponse({
        "success": True,
        "message": (
            f"{serial_number} successfully received."
        ),
        "cylinder": {
            "id": cylinder.id,
            "serial_number": cylinder.serial_number,
            "weight": str(cylinder.weight),
            "brand": cylinder.brand,
            "status": cylinder.status,
        }
    })


# ============================================================
# VALIDATION ERROR MESSAGE
# ============================================================

def get_validation_message(error):

    """
    Extract the actual user-friendly validation message
    from Django's ValidationError.
    """

    if hasattr(error, "message_dict"):

        for field_errors in error.message_dict.values():

            if field_errors:

                return str(field_errors[0])

    if hasattr(error, "messages") and error.messages:

        return str(error.messages[0])

    return "Unable to save the cylinder. Please check and try again."


# ============================================================
# INVENTORY
# ============================================================

def inventory_list(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    cylinders = (
        Cylinder.objects
        .filter(is_active=True)
        .order_by("-date_received")
    )

    if search:

        cylinders = (
            cylinders.filter(
                Q(serial_number__icontains=search)
                | Q(barcode__icontains=search)
            )
        )

    return render(
        request,
        "inventory/inventory_list.html",
        {
            "cylinders": cylinders,
            "search": search,
        }
    )


# ============================================================
# MASS SCAN
# ============================================================

def mass_scan(request):

    return render(
        request,
        "inventory/mass_scan.html"
    )


def mass_scan_check(request):

    code = request.GET.get(
        "code",
        ""
    ).strip()

    if not code:

        return JsonResponse({
            "success": False,
            "status": "INVALID",
            "message": "No cylinder number was provided."
        })

    if not code.upper().startswith("GLP"):

        return JsonResponse({
            "success": False,
            "status": "INVALID",
            "message": (
                "Invalid cylinder number. "
                "Cylinder numbers must begin with GLP."
            )
        })

    cylinder = (
        Cylinder.objects
        .filter(
            is_active=True,
            serial_number__iexact=code
        )
        .first()
    )

    if cylinder is None:

        cylinder = (
            Cylinder.objects
            .filter(
                is_active=True,
                barcode__iexact=code
            )
            .first()
        )

    if cylinder is None:

        return JsonResponse({
            "success": False,
            "status": "NOT_FOUND",
            "message": (
                "Cylinder not found in active inventory."
            )
        })

    return JsonResponse({
        "success": True,
        "status": "FOUND",
        "cylinder": {
            "id": cylinder.id,
            "serial_number": cylinder.serial_number,
            "barcode": cylinder.barcode,
            "weight": str(cylinder.weight),
            "brand": cylinder.brand,
            "status": cylinder.status,
        }
    })


@require_POST
def mass_scan_confirm(request):

    cylinder_ids = request.POST.getlist(
        "cylinder_ids"
    )

    if not cylinder_ids:

        messages.error(
            request,
            "No cylinders were selected."
        )

        return redirect("mass_scan")

    successful = 0
    skipped = 0

    for cylinder_id in cylinder_ids:

        try:

            cylinder = Cylinder.objects.get(
                id=cylinder_id,
                is_active=True
            )

        except Cylinder.DoesNotExist:

            skipped += 1
            continue

        with transaction.atomic():

            CylinderTransaction.objects.create(
                cylinder=cylinder,
                transaction_type="OUT",
                destination="MASS SCAN",
                weight=cylinder.weight
            )

            cylinder.is_active = False

            cylinder.save(
                update_fields=[
                    "is_active",
                    "date_updated"
                ]
            )

        successful += 1

    if successful:

        messages.success(
            request,
            f"{successful} cylinder(s) successfully "
            f"removed from inventory."
        )

    if skipped:

        messages.warning(
            request,
            f"{skipped} cylinder(s) were skipped because "
            f"they were already out of inventory or "
            f"no longer exist."
        )

    return redirect("mass_scan")


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def transaction_history(request):

    transactions = (
        CylinderTransaction.objects
        .select_related("cylinder")
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    if search:

        transactions = transactions.filter(
            Q(
                cylinder__serial_number__icontains=search
            )
            |
            Q(
                cylinder__barcode__icontains=search
            )
        )

    return render(
        request,
        "inventory/transaction_history.html",
        {
            "transactions": transactions,
            "search": search,
        }
    )