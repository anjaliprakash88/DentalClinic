# Generated by Django 5.1.7 on 2025-03-19 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SUPERADMIN', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='specialization',
            field=models.CharField(choices=[('General Dentist', 'General Dentist'), ('Pediatric Dentist', 'Pediatric Dentist'), ('Orthodontist', 'Orthodontist'), ('Periodontist', 'Periodontist'), ('Endodontist', 'Endodontist'), ('Oral Pathologist', 'Oral Pathologist'), ('Prosthodontist', 'Prosthodontist')], max_length=100),
        ),
    ]
