from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('',         views.login_view,  name='login'),
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('pesan/',   views.buat_pesanan, name='buat_pesanan'),
    path('riwayat/', views.riwayat,      name='riwayat'),
    path('rating/',             views.rating_list,   name='rating_list'),
    path('rating/<int:pk>/',    views.beri_rating,   name='beri_rating'),

    path('pesanan-masuk/',              views.pesanan_masuk,  name='pesanan_masuk'),
    path('ambil-pesanan/<int:pk>/',     views.ambil_pesanan,  name='ambil_pesanan'),
    path('selesai-pesanan/<int:pk>/',   views.selesai_pesanan, name='selesai_pesanan'),
    path('rating-saya/',                views.rating_saya,    name='rating_saya'),

    path('semua-transaksi/', views.semua_transaksi,  name='semua_transaksi'),
    path('rating-review/',   views.rating_review,    name='rating_review'),
    path('rating/',             views.rating_list,   name='rating_list'),
    path('rating/<int:pk>/',    views.beri_rating,   name='beri_rating'),
]