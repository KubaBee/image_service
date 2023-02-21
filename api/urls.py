from django.urls import path
from api import views


urlpatterns = [
    path('get-original-image/<int:pk>/', views.ImageDetail.as_view()),
    path('get-images-list/', views.ImageList.as_view()),
    path('create-image/', views.ImageCreate.as_view()),
    path('get-thumbnail-custom/<int:pk>/<int:size>/', views.get_any_size_thumbnail),
    path('get-group/<int:pk>/', views.GroupDetail.as_view()),
    path('get-groups-list/', views.GroupList.as_view()),
    path('create-group/', views.GroupCreate.as_view()),
    path('create-expiring-link/', views.TemporaryImageLinkCreate.as_view()),
    path('get-temporary-image/<uuid:pk>/', views.TemporaryImageDetail.as_view(), name='temporary-image-detail')
]

