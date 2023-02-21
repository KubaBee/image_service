from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from PIL import Image as Img
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib.auth.models import Group
import uuid


class Image(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(
        upload_to='images/',
        validators=[FileExtensionValidator(['jpg', 'png'])]
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='author')

    class Meta:
        ordering = ['created']


class Thumbnail(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    original_image = models.ForeignKey(Image, on_delete=models.CASCADE)
    height = models.PositiveIntegerField(null=False, blank=False)
    thumbnail_image = models.ImageField(upload_to="thumbnails/", null=False, blank=True)

    class Meta:
        ordering = ['created']

    def save(self, *args, **kwargs):
        if not self.make_thumbnail():
            raise Exception("An Error occurred while creating a thumbnail")
        super(Thumbnail, self).save(*args, **kwargs)

    def make_thumbnail(self):
        image = Img.open(self.original_image.image)
        image.thumbnail((self.height, image.height*self.height//image.width))

        thumb_name, thumb_extension = os.path.splitext(self.original_image.image.name)
        thumb_extension = thumb_extension.lower()
        thumb_filename = thumb_name + thumb_extension

        if thumb_extension == '.jpg':
            FTYPE = 'JPEG'
        elif thumb_extension == '.png':
            FTYPE = "PNG"
        else:
            return False

        temp_thumb = BytesIO()
        image.save(temp_thumb, FTYPE)
        temp_thumb.seek(0)

        self.thumbnail_image.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
        temp_thumb.close()

        return True


class Size(models.Model):
    height = models.PositiveIntegerField(blank=False, null=False)

    def __str__(self):
        return f"Height: {self.height}"

    def __repr__(self):
        return str(self.height)


Group.add_to_class('size', models.ManyToManyField(Size, blank=False, null=False))
Group.add_to_class('allow_original_image', models.BooleanField(blank=True, default=False))
Group.add_to_class('allow_expiring_link', models.BooleanField(blank=True, default=False))


class TemporaryLinks(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expire_time = models.FloatField(blank=False)
    image_id = models.ForeignKey(Image, on_delete=models.CASCADE)

