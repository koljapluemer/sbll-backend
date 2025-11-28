from django.urls import path

from . import views

urlpatterns = [
    path("", views.redirect_home, name="home"),
    path("languages/", views.language_list, name="language_list"),
    path("languages/add/", views.language_create, name="language_create"),
    path("languages/<str:pk>/edit/", views.language_update, name="language_update"),
    path("languages/<str:pk>/delete/", views.language_delete, name="language_delete"),
    path("glosses/", views.gloss_list, name="gloss_list"),
    path("glosses/add/", views.gloss_create, name="gloss_create"),
    path("glosses/<int:pk>/edit/", views.gloss_update, name="gloss_update"),
    path("glosses/<int:pk>/delete/", views.gloss_delete, name="gloss_delete"),
    path("situations/", views.situation_list, name="situation_list"),
    path("situations/add/", views.situation_create, name="situation_create"),
    path("situations/<str:pk>/edit/", views.situation_update, name="situation_update"),
    path("situations/<str:pk>/delete/", views.situation_delete, name="situation_delete"),
    path("situations/download-all/", views.situation_download_all, name="situation_download_all"),
    path("api/glosses/search/", views.api_gloss_search, name="api_gloss_search"),
    path("api/glosses/create/", views.api_gloss_create, name="api_gloss_create"),
]
