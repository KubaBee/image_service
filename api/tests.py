import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Group, Image, Size, Thumbnail, TemporaryLinks
from .serializers import ImageSerializer, GroupSerializer, ThumbnailSerializer
from PIL import Image as Img
from io import BytesIO
import json


class ImageCreateTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testing_user',
            password='testing4321'
        )

        self.image_data: dict = {
            'image': temporary_image()
        }
        self.client.login(username='testing_user', password='testing4321')

    def test_create_image_valid_data(self):
        response = self.client.post('/api/create-image/', self.image_data, format='multipart')
        self.assertEqual(response.data['author'], self.user.username)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_image_user_not_authenticated(self):
        self.client.logout()
        response = self.client.post('/api/create-image/', self.image_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_image_invalid_data(self):
        self.image_data['image'] = ''
        response = self.client.post('/api/create-image/', self.image_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ImageListTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testing_user',
            password='testing4321',
        )

        self.user_no_image_objects = User.objects.create_user(
            username='testing_user_no_images',
            password='testing4321',
        )

        self.image_one = Image.objects.create(image=temporary_image(), author=self.user)
        self.image_two = Image.objects.create(image=temporary_image(), author=self.user)

    def test_non_authenticated_user_access_list_view(self):
        self.client.logout()
        response = self.client.get('/api/get-images-list/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_access_list_view(self):
        self.client.login(username='testing_user', password='testing4321')
        response = self.client.get('/api/get-images-list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        images = Image.objects.filter(author=self.user)
        serializer = ImageSerializer(images, many=True)
        self.assertEqual(response.data, serializer.data)
        self.client.logout()

    def test_authenticated_user_access_list_view_no_objects(self):
        self.client.login(username='testing_user_no_images', password='testing4321')
        response = self.client.get('/api/get-images-list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        images = Image.objects.filter(author=self.user_no_image_objects)
        serializer = ImageSerializer(images, many=True)
        self.assertEqual(response.data, serializer.data)


class ImageDetailTest(APITestCase):

    def setUp(self) -> None:
        self.user_not_owner = User.objects.create_user(
            username='testing_user_not_owner',
            password='testing4321',

        )

        self.valid_user_no_permission = User.objects.create_user(
            username='testing_user_valid',
            password='testing4321',
        )

        self.group_no_permission = Group.objects.create(
            name='Test no permission',
        )

        self.group_with_permission = Group.objects.create(
            name='Test with permission',
            allow_original_image=True
        )

        self.image_one = Image.objects.create(image=temporary_image(), author=self.valid_user_no_permission)

    def test_not_authenticated_user_view_image(self):
        self.client.logout()
        response = self.client.get(f'/api/get-original-image/{self.image_one.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_owner_view_image(self):
        self.client.login(username='testing_user_not_owner', password='testing4321')
        response = self.client.get(f'/api/get-original-image/{self.image_one.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_no_permission_user_view_image(self):
        self.client.login(username='testing_user_valid', password='testing4321')
        self.valid_user_no_permission.groups.clear()
        self.group_no_permission.user_set.add(self.valid_user_no_permission)
        response = self.client.get(f'/api/get-original-image/{self.image_one.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_user_view_image(self):
        self.client.login(username='testing_user_valid', password='testing4321')
        self.valid_user_no_permission.groups.clear()
        self.group_with_permission.user_set.add(self.valid_user_no_permission)
        response = self.client.get(f'/api/get-original-image/{self.image_one.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ImageSerializer(self.image_one)
        self.assertEqual(response.data, serializer.data)


class GetAnySizeThumbnailTest(APITestCase):

    def setUp(self) -> None:
        self.user_not_owner = User.objects.create_user(
            username='testing_user_not_owner',
            password='testing4321',

        )

        self.size_200 = Size.objects.create(height=200)
        self.size_400 = Size.objects.create(height=400)
        self.size_custom = Size.objects.create(height=600)

        self.valid_user = User.objects.create_user(
            username='testing_user_valid',
            password='testing4321',
        )

        self.group_basic = Group.objects.create(
            name='Test Basic',
            allow_original_image=False
        )

        self.group_premium = Group.objects.create(
            name='Test Premium',
            allow_original_image=True

        )

        self.group_enterprise = Group.objects.create(
            name='Test Enterprise',
            allow_original_image=True

        )

        self.group_basic.size.add(self.size_200)
        self.group_premium.size.add(self.size_200, self.size_400)
        self.group_enterprise.size.add(self.size_200, self.size_400)
        self.image_one = Image.objects.create(image=temporary_image(), author=self.valid_user)
        self.thumbnail_200 = Thumbnail.objects.create(original_image=self.image_one, height=self.size_200.height)
        self.thumbnail_400 = Thumbnail.objects.create(original_image=self.image_one, height=self.size_400.height)

    def test_get_thumbnail_200_with_permission(self):
        self.client.login(username='testing_user_valid', password='testing4321')
        self.valid_user.groups.clear()
        self.group_premium.user_set.add(self.valid_user)
        self.group_enterprise.user_set.add(self.valid_user)
        self.group_basic.user_set.add(self.valid_user)
        response = self.client.get(f'/api/get-thumbnail-custom/{self.image_one.pk}/{self.size_200.height}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ThumbnailSerializer(self.thumbnail_200)
        self.assertEqual(response.data, serializer.data)

    def test_get_thumbnail_200_without_permission(self):
        self.client.login(username='testing_user_valid', password='testing4321')
        self.valid_user.groups.clear()
        self.group_basic.user_set.add(self.valid_user)
        response = self.client.get(f'/api/get-thumbnail-custom/{self.image_one.pk}/{self.size_200.height}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_thumbnail_400_without_permission(self):
        self.client.login(username='testing_user_valid', password='testing4321')
        self.valid_user.groups.clear()
        self.group_basic.user_set.add(self.valid_user)
        response = self.client.get(f'/api/get-thumbnail-custom/{self.image_one.pk}/{self.size_400.height}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GroupCreateTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testing_user',
            password='testing4321'
        )

        self.admin = User.objects.create_user(
            username='admin',
            password='testing4321',
            is_staff=True
        )

        self.group_data_valid = {
            "name": "Test_User",
            "size": [100, 500, 102],
            "allow_original_image": False,
            "allow_expiring_link": False
        }

        self.group_data_invalid = {
            'name': 'test group',
        }

    def test_unauthenticated_user_create_group(self):
        self.client.logout()
        response = self.client.post(
            '/api/create-group/',
            data=json.dumps(self.group_data_valid),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_user_create_group(self):
        self.client.login(username='testing_user', password='testing4321')
        response = self.client.post(
            '/api/create-group/',
            data=json.dumps(self.group_data_valid),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_admin_user_create_group(self):
        self.client.login(username='admin', password='testing4321')
        response = self.client.post(
            '/api/create-group/',
            data=json.dumps(self.group_data_valid),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.first()
        self.assertEqual(group.name, self.group_data_valid['name'])
        self.assertEqual(group.size.count(), len(self.group_data_valid['size']))

    def test_upload_image_with_invalid_data(self):
        self.client.login(username='admin', password='testing4321')
        response = self.client.post(
            '/api/create-group/',
            data=json.dumps(self.group_data_invalid),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GroupDetailTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='not_admin',
            password='testing4321'
        )

        self.user = User.objects.create_user(
            username='admin',
            password='testing4321',
            is_staff=True
        )

        size_obj = Size.objects.create(height=500)

        self.group_one = Group.objects.create(
            name="Test",
            allow_original_image=True,
            allow_expiring_link=True,
        )
        self.group_one.size.add(size_obj)

    def test_not_admin_user_view_group(self):
        self.client.login(username='not_admin', password='testing4321')
        response = self.client.get(f'/api/get-group/{self.group_one.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_view_group(self):
        self.client.login(username='admin', password='testing4321')
        response = self.client.get(f'/api/get-group/{self.group_one.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = GroupSerializer(self.group_one)
        self.assertEqual(response.data, serializer.data)


class GroupListTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testing_user',
            password='testing4321'
        )

        self.admin = User.objects.create_user(
            username='admin',
            password='testing4321',
            is_staff=True
        )

        self.not_admin = User.objects.create_user(
            username='not_admin',
            password='testing4321',
        )

        self.group_one = Group.objects.create(
            name='Test one',
            allow_expiring_link=True
        )

        self.group_two = Group.objects.create(
            name='Test two',
            allow_expiring_link=True
        )

        self.group_three = Group.objects.create(
            name='Test three',
            allow_expiring_link=True
        )

    def test_unauthenticated_user_view_group(self):
        self.client.logout()
        response = self.client.get('/api/get-groups-list/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_admin_user_view_group(self):
        self.client.login(username='not_admin', password='testing4321')
        response = self.client.get('/api/get-groups-list/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_view_group(self):
        self.client.login(username='admin', password='testing4321')
        response = self.client.get('/api/get-groups-list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TemporaryImageLinkCreateTest(APITestCase):
    def setUp(self):

        self.user = User.objects.create_user(
            username='testing_user',
            password='testing4321',
        )

        self.group_with_permission = Group.objects.create(
            name='Test with permission',
            allow_expiring_link=True
        )

        self.group_with_permission.user_set.add(self.user)
        self.image_one = Image.objects.create(image='some_image.png', author=self.user)

    def test_create_temporary_link(self):
        self.client.login(username="testing_user", password="testing4321")
        data = {'image_id': self.image_one.id, 'expire_time': 600}
        response = self.client.post("/api/create-expiring-link/", data)
        expire_time = datetime.datetime.now() + datetime.timedelta(seconds=600)
        expire_time_sec = datetime.datetime.timestamp(expire_time)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('id' in response.data)
        self.assertTrue(expire_time_sec - float(response.data['expire_time']) <= 5)
        self.assertEqual(response.data['image_id'], self.image_one.id)

        link = TemporaryLinks.objects.get(id=response.data['id'])
        self.assertEqual(link.image_id, self.image_one)

    def test_create_temporary_link_with_invalid_expire_time(self):
        self.client.login(username="testing_user", password="testing4321")
        data = {'image_id': self.image_one.id, 'expire_time': 100}

        response = self.client.post("/api/create-expiring-link/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data['expire_time'] = 40000
        response = self.client.post("/api/create-expiring-link/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_temporary_link_for_nonexistent_image(self):
        self.client.login(username="testing_user", password="testing4321")

        data = {'image_id': -2202, 'expire_time': 600}

        response = self.client.post("/api/create-expiring-link/", data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_temporary_link_by_unauthorized_user(self):
        self.client.logout()
        data = {'image_id': self.image_one.id, 'expire_time': 600}

        response = self.client.post("/api/create-expiring-link/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TemporaryImageLinkViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testing_user',
            password='testing4321',
        )

        self.image_one = Image.objects.create(image=temporary_image(), author=self.user)

    def test_view_temporary_link_expired(self):
        past_time = timezone.now() + timezone.timedelta(seconds=-400)
        self.temporary_link_past = TemporaryLinks.objects.create(
            expire_time=datetime.datetime.timestamp(past_time),
            image_id=self.image_one
        )
        response = self.client.get(f"/api/get-temporary-image/{self.temporary_link_past.pk}/")
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)

    def test_view_temporary_link_active(self):
        future_time = timezone.now() + timezone.timedelta(seconds=400)

        self.temporary_link_future = TemporaryLinks.objects.create(
            expire_time=datetime.datetime.timestamp(future_time),
            image_id=self.image_one
        )
        response = self.client.get(f"/api/get-temporary-image/{self.temporary_link_future.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


def temporary_image():
    bts = BytesIO()
    img = Img.new("RGB", (100, 100))
    img.save(bts, 'jpeg')
    return SimpleUploadedFile("test.jpg", bts.getvalue())


User = get_user_model()

