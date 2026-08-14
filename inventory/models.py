from django.db import models
from django.core.exceptions import ValidationError
import qrcode
from io import BytesIO
from django.core.files import File


class Cylinder(models.Model):

    STATUS_CHOICES = [
        ('FULL', 'Full'),
        ('EMPTY', 'Empty'),
    ]

    serial_number = models.CharField(
        max_length=50,
        unique=True
    )

    barcode = models.CharField(
        max_length=100,
        unique=True
    )

    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    brand = models.CharField(
        max_length=50
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    is_active = models.BooleanField(
        default=True
    )

    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True
    )

    date_received = models.DateTimeField(
        auto_now_add=True
    )

    date_updated = models.DateTimeField(
        auto_now=True
    )

    def clean(self):
        """
        Validate the cylinder.

        Every cylinder serial number must begin with GLP.
        """

        if not self.serial_number.upper().startswith('GLP'):
            raise ValidationError(
                'Invalid cylinder serial number. '
                'Cylinder numbers must begin with GLP.'
            )

    def save(self, *args, **kwargs):
        """
        Validate the cylinder and automatically
        generate a QR code if one does not exist.
        """

        self.full_clean()

        if not self.qr_code:

            qr_image = qrcode.make(
                self.serial_number
            )

            buffer = BytesIO()

            qr_image.save(
                buffer,
                format='PNG'
            )

            file_name = f'{self.serial_number}.png'

            self.qr_code.save(
                file_name,
                File(buffer),
                save=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.serial_number


class CylinderTransaction(models.Model):

    TRANSACTION_TYPES = [
        ('IN', 'Scan In'),
        ('OUT', 'Scan Out'),
    ]

    DESTINATION_CHOICES = [
        ('FIELD', 'Field'),
        ('WAREHOUSE', 'Warehouse'),
        ('MASS SCAN', 'Mass Scan'),
    ]

    cylinder = models.ForeignKey(
        Cylinder,
        on_delete=models.PROTECT,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    destination = models.CharField(
        max_length=20,
        choices=DESTINATION_CHOICES,
        blank=True,
        null=True
    )

    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f'{self.cylinder.serial_number} - '
            f'{self.get_transaction_type_display()}'
        )