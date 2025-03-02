# Generated by Django 5.1.3 on 2025-02-20 17:03

from django.db import migrations

def create_profiles(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    Profile = apps.get_model('accounts', 'Profile')
    for user in CustomUser.objects.all():
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile'),
    ]

    operations = [
        migrations.RunPython(create_profiles),
    ]
