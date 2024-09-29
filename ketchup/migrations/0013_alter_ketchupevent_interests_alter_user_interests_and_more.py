# Generated by Django 4.2.7 on 2024-01-20 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ketchup', '0012_interest_ketchupevent_interests_user_interests'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ketchupevent',
            name='interests',
            field=models.ManyToManyField(related_name='interests_of_event', to='ketchup.interest'),
        ),
        migrations.AlterField(
            model_name='user',
            name='interests',
            field=models.ManyToManyField(related_name='interests_of_user', to='ketchup.interest'),
        ),
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100, null=True)),
                ('address', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=5120, null=True)),
                ('interests', models.ManyToManyField(related_name='interests_of_business', to='ketchup.interest')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
