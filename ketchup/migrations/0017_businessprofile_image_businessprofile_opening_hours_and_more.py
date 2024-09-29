# Generated by Django 4.2.7 on 2024-01-27 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ketchup', '0016_alter_application_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessprofile',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='business_images/'),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='opening_hours',
            field=models.TextField(help_text='Weekly timetable as text', null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='phone_number',
            field=models.CharField(max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='type',
            field=models.CharField(choices=[('retail', 'Retail'), ('service', 'Service'), ('restaurant', 'Restaurant')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='user_avatars/'),
        ),
        migrations.AlterField(
            model_name='businessprofile',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
