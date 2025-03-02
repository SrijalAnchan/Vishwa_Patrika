from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from news import views as news_views
from vishwa_patrikaa.views import home_view
from accounts.views import register_view

# Password reset URLs
password_reset_patterns = [
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]


urlpatterns = [
    path('', home_view, name='home'),
    path('login/', accounts_views.login_view, name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('profile/', accounts_views.profile_view, name='profile'),
    path('profile/edit/', accounts_views.profile_edit_view, name='profile_edit'),
    path('news/', news_views.news_list, name='news_list'),
    path('update-news/', news_views.update_news, name='update_news'),
    path('populate/', news_views.populate_database, name='populate_database'),
    path('register/', register_view, name='register'),


] + password_reset_patterns



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
