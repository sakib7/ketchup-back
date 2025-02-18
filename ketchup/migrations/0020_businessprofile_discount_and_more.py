# Generated by Django 4.2.7 on 2024-02-17 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ketchup', '0019_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessprofile',
            name='discount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='starting_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, max_length=5120, null=True),
        ),
    ]
