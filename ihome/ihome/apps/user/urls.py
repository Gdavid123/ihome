from django.conf.urls import url

from user import views

urlpatterns = [
    url(r'^api/v1.0/user/register/$',views.RegisterView.as_view(),name='register'),
    url(r'^api/v1.0/imagecode/$',views.ImageCodeView.as_view()),
    url(r'^api/v1.0/smscode/$',views.SMSCodeView.as_view()),
    url(r'^api/v1.0/login/$',views.Login.as_view(),name='login'),
    url(r'^api/v1.0/session/$',views.Session.as_view()),
    url(r'^api/v1.0/logout/$',views.Logout.as_view()),
    url(r'^api/v1.0/user/profile/$',views.user_profile.as_view()),
    url(r'^api/v1.0/user/avatar/$',views.avatar.as_view()),
    url(r'^api/v1.0/user/auth/$',views.Auth.as_view()),



]
