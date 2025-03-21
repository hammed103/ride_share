# Generated by Django 5.1.7 on 2025-03-16 15:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0003_driver_user_alter_driver_location_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RideRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('EXPIRED', 'Expired')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='matching.driver')),
                ('ride', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='matching.ride')),
            ],
            options={
                'unique_together': {('ride', 'driver')},
            },
        ),
    ]
