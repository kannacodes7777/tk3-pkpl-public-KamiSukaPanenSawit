import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Avg
from django.db.models import Q

from .models import Pesanan, Rating, CustomUser
from .forms import PesananForm, RegisterForm, RatingForm



def register_view(request):
    if request.user.is_authenticated:
        return redirect('main:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Akun {user.username} berhasil dibuat! Silakan login.")
            return redirect('main:login')
        else:
            messages.error(request, "Registrasi gagal. Pastikan data valid.")
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        cache_key = f'login_attempts_{username}'
        attempts  = cache.get(cache_key, 0)

        if attempts >= 5:
            messages.error(request, "Terlalu banyak percobaan gagal. Akun dikunci sementara.")
            return render(request, 'main/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            cache.delete(cache_key)
            login(request, user)
            return redirect('main:dashboard')
        else:
            cache.set(cache_key, attempts + 1, timeout=300)
            messages.error(request, f"Kredensial salah. Sisa percobaan: {4 - attempts}")

    return render(request, 'main/login.html')


def logout_view(request):
    logout(request)
    return redirect('main:login')



@login_required(login_url='/login/')
def dashboard(request):
    ctx = {}

    if request.user.role == 'penumpang':
        semua = Pesanan.objects.filter(penumpang=request.user).order_by('-waktu_pesan')
        ctx['pesanan_aktif'] = semua.filter(
            status__in=['Menunggu Pengemudi', 'Sedang Diantar']
        ).first()
        ctx['riwayat_singkat'] = semua.filter(status='Selesai')[:5]
        ctx['total_pesanan']   = semua.count()
        ctx['pesanan_berjalan'] = semua.filter(
            status__in=['Menunggu Pengemudi', 'Sedang Diantar']
        ).count()
        ctx['avg_rating_driver'] = Rating.objects.filter(
            penumpang=request.user
        ).aggregate(avg=Avg('skor'))['avg']

    elif request.user.role == 'pengemudi':
        semua_antar = Pesanan.objects.filter(
            pengemudi=request.user
        ).order_by('-waktu_pesan')
        ctx['antar_hari_ini'] = semua_antar.filter(status='Selesai').count()
        ctx['pesanan_masuk_count'] = Pesanan.objects.filter(
            status='Menunggu Pengemudi'
        ).count()
        ctx['pesanan_masuk_preview'] = Pesanan.objects.filter(
            status='Menunggu Pengemudi'
        ).order_by('-waktu_pesan')[:3]
        ctx['rating_saya'] = Rating.objects.filter(
            pengemudi=request.user
        ).aggregate(avg=Avg('skor'))['avg']
        ctx['jumlah_ulasan'] = Rating.objects.filter(pengemudi=request.user).count()
        ctx['ulasan_terbaru'] = Rating.objects.filter(
            pengemudi=request.user
        ).order_by('-waktu')[:3]

    elif request.user.role == 'penyedia':
        semua = Pesanan.objects.all()
        ctx['stats'] = {
            'total'      : semua.count(),
            'menunggu'   : semua.filter(status='Menunggu Pengemudi').count(),
            'selesai'    : semua.filter(status='Selesai').count(),
            'dibatalkan' : semua.filter(status='Dibatalkan').count(),
        }
        ctx['riwayat_singkat'] = semua.order_by('-waktu_pesan')[:5]

    return render(request, 'main/dashboard.html', ctx)



@login_required(login_url='/login/')
def buat_pesanan(request):
    if request.user.role != 'penumpang':
        messages.error(request, "Hanya penumpang yang dapat membuat pesanan.")
        return redirect('main:dashboard')

    if request.method == 'POST':
        form = PesananForm(request.POST)
        if form.is_valid():
            pesanan = form.save(commit=False)
            pesanan.penumpang = request.user
            pesanan.save()
            messages.success(request, "Pesanan berhasil dibuat!")
            return redirect('main:dashboard')
        else:
            messages.error(request, "Gagal memproses pesanan. Periksa kembali input Anda.")
    else:
        form = PesananForm()

    return render(request, 'main/buat_pesanan.html', {'form': form})


@login_required(login_url='/login/')
def riwayat(request):
    if request.user.role == 'penumpang':
        data = Pesanan.objects.filter(penumpang=request.user).order_by('-waktu_pesan')
    elif request.user.role == 'pengemudi':
        data = Pesanan.objects.filter(pengemudi=request.user).order_by('-waktu_pesan')
    else:
        return redirect('main:dashboard')

    search_query = request.GET.get('q', '').strip()

    if search_query:
        if not re.match(r'^[a-zA-Z0-9\s.,\-]+$', search_query):
            messages.error(request, "Pencarian dibatalkan: Input mengandung karakter tidak valid.")
            data = data.none()
        else:
            data = data.filter(
                Q(titik_jemput__icontains=search_query) |
                Q(titik_tujuan__icontains=search_query)
            )

    return render(request, 'main/riwayat.html', {
        'data_pesanan': data,
        'search_query': search_query
    })

@login_required(login_url='/login/')
def rating_list(request):
    """Penumpang: daftar pesanan selesai yang belum diberi rating."""
    if request.user.role != 'penumpang':
        return redirect('main:dashboard')

    selesai_tanpa_rating = Pesanan.objects.filter(
        penumpang=request.user,
        status='Selesai',
    ).exclude(rating__isnull=False).order_by('-waktu_pesan')

    sudah_dirating = Rating.objects.filter(
        penumpang=request.user
    ).order_by('-waktu')

    return render(request, 'main/rating_penumpang.html', {
        'selesai_tanpa_rating': selesai_tanpa_rating,
        'sudah_dirating'       : sudah_dirating,
    })


@login_required(login_url='/login/')
def beri_rating(request, pk):
    """Penumpang: form beri rating untuk satu pesanan."""
    if request.user.role != 'penumpang':
        return redirect('main:dashboard')

    pesanan = get_object_or_404(
        Pesanan, pk=pk, penumpang=request.user, status='Selesai'
    )

    if hasattr(pesanan, 'rating'):
        messages.info(request, "Pesanan ini sudah diberi rating.")
        return redirect('main:rating_list')

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.pesanan   = pesanan
            rating.penumpang = request.user
            rating.pengemudi = pesanan.pengemudi
            rating.save()
            messages.success(request, "Terima kasih! Rating berhasil dikirim.")
            return redirect('main:rating_list')
    else:
        form = RatingForm()

    return render(request, 'main/beri_rating.html', {
        'pesanan': pesanan,
        'form'   : form,
    })



@login_required(login_url='/login/')
def pesanan_masuk(request):
    if request.user.role != 'pengemudi':
        return redirect('main:dashboard')
    data = Pesanan.objects.filter(
        status='Menunggu Pengemudi'
    ).order_by('-waktu_pesan')
    return render(request, 'main/pesanan_masuk.html', {'data_pesanan': data})


@login_required(login_url='/login/')
def ambil_pesanan(request, pk):
    if request.user.role != 'pengemudi':
        return redirect('main:dashboard')
    pesanan = get_object_or_404(Pesanan, pk=pk, status='Menunggu Pengemudi')
    pesanan.pengemudi = request.user
    pesanan.status    = 'Sedang Diantar'
    pesanan.save()
    messages.success(request, "Pesanan berhasil diambil!")
    return redirect('main:pesanan_masuk')


@login_required(login_url='/login/')
def selesai_pesanan(request, pk):
    if request.user.role != 'pengemudi':
        return redirect('main:dashboard')
    pesanan = get_object_or_404(
        Pesanan, pk=pk, pengemudi=request.user, status='Sedang Diantar'
    )
    pesanan.status = 'Selesai'
    pesanan.save()
    messages.success(request, "Pesanan selesai!")
    return redirect('main:dashboard')


@login_required(login_url='/login/')
def rating_saya(request):
    if request.user.role != 'pengemudi':
        return redirect('main:dashboard')
    semua_rating = Rating.objects.filter(
        pengemudi=request.user
    ).order_by('-waktu')
    avg = semua_rating.aggregate(avg=Avg('skor'))['avg']
    return render(request, 'main/rating_saya.html', {
        'semua_rating': semua_rating,
        'avg_rating'  : avg,
        'jumlah'      : semua_rating.count(),
    })



@login_required(login_url='/login/')
def semua_transaksi(request):
    if request.user.role != 'penyedia':
        return redirect('main:dashboard')
    data = Pesanan.objects.all().order_by('-waktu_pesan')
    return render(request, 'main/semua_transaksi.html', {'data_pesanan': data})


@login_required(login_url='/login/')
def rating_review(request):
    if request.user.role != 'penyedia':
        return redirect('main:dashboard')

    drivers = CustomUser.objects.filter(role='pengemudi')
    driver_stats = []
    for d in drivers:
        stats = Rating.objects.filter(pengemudi=d).aggregate(avg=Avg('skor'))
        driver_stats.append({
            'driver'      : d,
            'avg_rating'  : stats['avg'],
            'jumlah'      : Rating.objects.filter(pengemudi=d).count(),
            'total_antar' : Pesanan.objects.filter(
                                pengemudi=d, status='Selesai'
                            ).count(),
        })

    semua_rating = Rating.objects.all().order_by('-waktu')
    avg_platform = semua_rating.aggregate(avg=Avg('skor'))['avg']

    return render(request, 'main/rating_review.html', {
        'driver_stats' : driver_stats,
        'semua_rating' : semua_rating,
        'avg_platform' : avg_platform,
        'total_review' : semua_rating.count(),
        'driver_aktif' : drivers.count(),
    })