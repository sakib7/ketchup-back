# Generated by Django 4.2.7 on 2024-02-23 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ketchup', '0023_ketchupevent_business_alter_ketchupevent_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='ketchupevent',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='ketchup_events_images/'),
        ),
    ]
