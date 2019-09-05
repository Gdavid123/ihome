from django.conf.urls import url

from house import views

urlpatterns = [
    url(r'^api/v1.0/houses/search/$',views.Search.as_view()),
    url(r'^api/v1.0/houses/index/$',views.Index.as_view()),
    url(r'^api/v1.0/user/houses/$', views.MyHouses.as_view()),
    url(r'^api/v1.0/houses/$', views.HousesView.as_view()),
    url(r'^api/v1.0/houses/(?P<house_id>\d+)/$', views.HousesView.as_view()),
    url(r'^api/v1.0/houses/(?P<house_id>\d+)/images/$', views.HousesImageView.as_view(), name='houses_img'),




]
