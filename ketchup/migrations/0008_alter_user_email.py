# Generated by Django 4.2.7 on 2023-12-06 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ketchup', '0007_application'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=100, unique=True),
        ),
    ]
