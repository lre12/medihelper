from django.urls import path
from . import views

urlpatterns = [
	path('',views.index, name='medindex'),
	path('result',views.result, name='result'),
	path('list',views.list),
]