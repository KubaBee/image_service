from django.shortcuts import reverse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from .models import Image, Thumbnail, Size, TemporaryLinks
from .permissions import IsOwner, CanSeeOriginalImage, CanGenerateExpiringLinks
from .serializers import ImageSerializer, ThumbnailSerializer, GroupSerializer, TemporaryURLSerializer
from django.contrib.auth.models import Group
from rest_framework.response import Response
from django.utils import timezone
import datetime
from django.http import HttpResponse


class ImageList(generics.ListAPIView):
    """
    Return list of images added by a current user
    """
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Image.objects.filter(author=self.request.user)


class ImageDetail(generics.RetrieveAPIView):
    """
    Return image detail link to all the authenticated owners with Premium or Enterprise plan
    """
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated and IsOwner, CanSeeOriginalImage]


class ImageCreate(generics.CreateAPIView):
    """
    Allow authenticated users to upload their images
    """
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class GroupList(generics.ListAPIView):
    """
    Return list of group objects (can be triggered only by admin)
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class GroupDetail(generics.RetrieveAPIView):
    """
    Return detail object of the group
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class GroupCreate(generics.CreateAPIView):
    """
    Allow administrators to create a custom group
    """

    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        # create a mutable copy of the request data
        data = request.data.copy()
        size_data = data.pop('size', [])
        size_objects = []
        for height in size_data:
            size_obj, created = Size.objects.get_or_create(height=height)
            size_objects.append(size_obj)

        # create a new serializer with modified data
        data['size'] = [size_obj.pk for size_obj in size_objects]
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        group_obj = serializer.save()
        group_obj.size.set(size_objects)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)


@api_view(['GET'])
@permission_classes([IsAuthenticated, CanSeeOriginalImage])
def get_any_size_thumbnail(request, pk: int, size: int):
    """
    Allows user to generate a thumbnail of a given height.
    Function is also checking if a user is permitted to perform this action based on assigned groups
    """

    # check user group and height assigned to them
    if not request.user.groups.filter(size__height__icontains=size):
        return Response(status=403)

    # get or generate a thumbnail
    try:
        thumbnail, created = Thumbnail.objects.get_or_create(original_image_id=pk, height=size)
    except Thumbnail.MultipleObjectsReturned:
        multiple_thumbnails: list[(Thumbnail, bool)] = Thumbnail.objects.get_or_create(
            original_image_id=pk,
            height=size)
        thumbnail, created = multiple_thumbnails[0]
    except Image.DoesNotExist:
        return Response(status=404)

    serializer = ThumbnailSerializer(thumbnail)

    return Response(serializer.data)


class TemporaryImageLinkCreate(generics.CreateAPIView):
    """
    Allows user to generate a temporary link to an object.
    Function is also checking if a user is permitted to perform this action based on assigned groups
    (CanGenerateExpiringLinks).
    Expiration date must be higher than 300 sec from now and cant be greater than 30000 sec from now
    """

    serializer_class = TemporaryURLSerializer
    permission_classes = [IsAuthenticated, CanGenerateExpiringLinks]

    def post(self, request, *args, **kwargs):

        try:
            image_obj = Image.objects.get(pk=request.data['image_id'])
        except Image.DoesNotExist:
            return Response(status=404)

        if request.user != image_obj.author:
            return Response(status=403)

        expire_time = int(request.data['expire_time'])
        if not expire_time or expire_time < 300 or expire_time > 30000:
            return Response(status=400)

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        new_time_dt = datetime.datetime.now() + datetime.timedelta(
            seconds=int(serializer.validated_data['expire_time']))
        new_time_dt_to_sec = datetime.datetime.timestamp(new_time_dt)
        serializer.validated_data['expire_time'] = new_time_dt_to_sec
        serializer.save(expire_time=new_time_dt_to_sec)

        # construct the URL of the created temporary image
        url = reverse('temporary-image-detail', args=[serializer.instance.id])

        response_data = serializer.data
        response_data['url'] = self.request.build_absolute_uri(url)


class TemporaryImageDetail(generics.GenericAPIView):
    """
    Returns a temporary image object available without any permission. The temporary image contain information about
    Image ID and the expire_time. Based on expire_time parameter either 200 or 423 is returned
    """
    queryset = TemporaryLinks.objects.all()
    serializer_class = TemporaryURLSerializer

    def get(self, request, pk):
        temporary_link_obj = TemporaryLinks.objects.get(pk=pk)
        if not temporary_link_obj.expire_time or temporary_link_obj.expire_time < datetime.datetime.timestamp(timezone.now()):
            return Response({'error': 'Link has expired'}, status=423)

        image: Image = Image.objects.get(pk=temporary_link_obj.image_id.pk).image
        return HttpResponse(image, content_type='image/jpeg')

