from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)

    # Fix clashes by setting related_name
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",
        blank=True
    )

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created:
            Profile.objects.create(user=self)

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'
