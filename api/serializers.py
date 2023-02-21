from rest_framework import serializers
from .models import Image, Thumbnail, TemporaryLinks
from django.contrib.auth.models import Group
from django.shortcuts import reverse


class ImageSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Image
        fields = ['id', 'created', 'image', 'author']


class ThumbnailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Thumbnail
        fields = ['id', 'thumbnail_image', 'height']

# TODO: Fix to show full url for thumbnails


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'size', 'allow_original_image', 'allow_expiring_link']

    def validate_size(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Size must be a list of integers')
        return value


class TemporaryURLSerializer(serializers.ModelSerializer):
    expire_time = serializers.FloatField()
    image_id = serializers.PrimaryKeyRelatedField(queryset=Image.objects.all())
    url = serializers.SerializerMethodField()

    class Meta:
        model = TemporaryLinks
        fields = ['id', 'expire_time', 'image_id', 'url']

    def get_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            url = reverse('temporary-image-detail', args=[obj.id])
            return request.build_absolute_uri(url)
