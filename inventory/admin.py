from django.contrib import admin
from .models import Cylinder


@admin.register(Cylinder)
class CylinderAdmin(admin.ModelAdmin):

    list_display = (
        'serial_number',
        'barcode',
        'weight',
        'brand',
        'status',
        'date_received',
        'date_updated',
    )

    search_fields = (
        'serial_number',
        'barcode',
    )

    list_filter = (
        'brand',
        'status',
    )

    readonly_fields = (
        'qr_code',
        'date_received',
        'date_updated',
    )