from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from inventory.views import (
    dashboard,
    scan_in,
    fast_scan_in,
    inventory_list,
    mass_scan,
    mass_scan_check,
    mass_scan_confirm,
    transaction_history,
)


urlpatterns = [

    # Dashboard
    path(
        "",
        dashboard,
        name="dashboard"
    ),

    # Admin
    path(
        "admin/",
        admin.site.urls
    ),

    # Fast Scan IN
    path(
        "scan-in/",
        scan_in,
        name="scan_in"
    ),

    path(
        "scan-in/save/",
        fast_scan_in,
        name="fast_scan_in"
    ),

    # Inventory
    path(
        "inventory/",
        inventory_list,
        name="inventory_list"
    ),

    # Mass Scan
    path(
        "mass-scan/",
        mass_scan,
        name="mass_scan"
    ),

    path(
        "mass-scan/check/",
        mass_scan_check,
        name="mass_scan_check"
    ),

    path(
        "mass-scan/confirm/",
        mass_scan_confirm,
        name="mass_scan_confirm"
    ),

    # History
    path(
        "transaction-history/",
        transaction_history,
        name="transaction_history"
    ),
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )