from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^project_conf$', views.get_project_conf, name='get_project_conf'),
    url(r'^deploy_to_jenkins$', views.deploy_to_jenkins, name='deploy_to_jenkins'),
]