"""
URL configuration for ketchup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from rest_framework import routers
from ketchup import views
from .views import LoginView, UserRegisterView, KetchEventListCreateAPIView, KetchEventRetrieveAPIView, ApplicationAPIView, ApplicationDecisionAPIView, InterestAPIView, UserDetailView, ProfileView, BusinessUserView, BusinessUserDetailView, ActivateAccount, UserView, MessageAPIView
from django.conf import settings
from django.conf.urls.static import static

# router = routers.DefaultRouter()
# # router.register(r'users', views.UserViewSet)
# router.register(r'groups', views.GroupViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/login', LoginView.as_view(), name='token_obtain_pair'),
    path('api/register', UserRegisterView.as_view(), name='user_register'),
    path('api/ketchups', KetchEventListCreateAPIView.as_view(), name='create_ketchup'),
    path('api/ketchups/<int:id>', KetchEventRetrieveAPIView.as_view(), name='ketchup_detail'),
    path('api/users', UserView.as_view(), name='user_list'),
    path('api/users/<int:id>', UserDetailView.as_view(), name='user_detail'),
    path('api/businesses', BusinessUserView.as_view(), name='business list'),
    path('api/businesses/<int:id>', BusinessUserDetailView.as_view(), name='business_detail'),
    path('api/profile', ProfileView.as_view(), name='profile'),
    path('api/profile/<int:id>/', ProfileView.as_view(), name='other_user_profile'),
    path('api/application', ApplicationAPIView.as_view(), name='application_to_event'),
    path('api/decision', ApplicationDecisionAPIView.as_view(), name='decide_application_status'),
    path('api/interests', InterestAPIView.as_view(), name='interest-list-create'),
    path('api/message', MessageAPIView.as_view(), name='message_send_receive'),
    path('api/activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate_account'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
