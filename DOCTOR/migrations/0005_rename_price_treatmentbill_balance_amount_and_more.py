# Generated by Django 5.1.7 on 2025-03-20 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DOCTOR', '0004_alter_dentalexamination_selected_teeth_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='treatmentbill',
            old_name='price',
            new_name='balance_amount',
        ),
        migrations.AddField(
            model_name='treatmentbill',
            name='paid_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='treatmentbill',
            name='total_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
