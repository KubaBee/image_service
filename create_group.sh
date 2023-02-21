python manage.py migrate

# Create new group
python manage.py shell << END
from django.contrib.auth.models import Group
from api.models import Size

size200 = Size.objects.create(height=200)
size400 = Size.objects.create(height=400)

basic_group, created_basic = Group.objects.get_or_create(name='Basic')
basic_group.size.add(size200)

premium_group, created_premium = Group.objects.get_or_create(name='Premium', allow_original_image=True)
premium_group.size.add(size200, size400)

enterprise_group, created_enterprise = Group.objects.get_or_create(name='Enterprise', allow_original_image=True, allow_expiring_link=True)
enterprise_group.size.add(size200, size400)

if created_basic and created_premium and created_enterprise:
    print('Groups created successfully!')
else:
    print('Group already may have already existed or there was an error when creating.')
END