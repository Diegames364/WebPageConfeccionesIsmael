from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.register_view, name="register"),
    path("perfil/", views.profile_view, name="profile"),
    path("eliminar/", views.delete_account, name="delete_account"),
]   