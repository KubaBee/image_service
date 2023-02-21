from django.contrib import admin
from .models import Image, Thumbnail, TemporaryLinks


admin.site.register(Image)
admin.site.register(Thumbnail)
admin.site.register(TemporaryLinks)
