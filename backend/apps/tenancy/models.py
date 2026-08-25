from django.db import models

from apps.common.models import BaseModel


class Merchant(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    vertical = models.CharField(max_length=20, default="ICE_CREAM")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
