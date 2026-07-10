# Generated migration for slot type and booking status fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parking_app', '0014_eticket'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingslot',
            name='preferred_slot_type',
            field=models.CharField(choices=[('Open', 'Open'), ('Reserved', 'Reserved'), ('EV', 'EV')], default='Open', max_length=20),
        ),
        migrations.AddField(
            model_name='parkingslot',
            name='booking_status',
            field=models.CharField(choices=[('Available', 'Available'), ('Booked', 'Booked')], default='Available', max_length=20),
        ),
    ]
