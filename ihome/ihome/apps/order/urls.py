from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^api/v1.0/orders/$', views.OrderReservationView.as_view()),
    url(r'^api/v1.0/orders/comment/$', views.OrderCommentView.as_view()),

]
