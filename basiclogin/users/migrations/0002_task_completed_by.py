# Generated by Django 5.2.1 on 2025-05-15 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='completed_by',
            field=models.ManyToManyField(blank=True, related_name='completed_tasks', to='users.user'),
        ),
    ]
