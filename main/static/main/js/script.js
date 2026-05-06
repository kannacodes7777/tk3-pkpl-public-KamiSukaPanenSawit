document.addEventListener("DOMContentLoaded", function () {

    const isLoggedIn   = !!document.querySelector('.btn-logout');
    const isLoginPage  = !!document.getElementById('login-form');

    if (isLoginPage) {
        const form = document.getElementById('login-form');
        if (form) {
            form.addEventListener('submit', function () {
                sessionStorage.setItem('browser_session_active', '1');
            });
        }
    } else if (isLoggedIn) {
        if (!sessionStorage.getItem('browser_session_active')) {
            window.location.href = '/logout/';
            return;
        }
        sessionStorage.setItem('browser_session_active', '1');
    }

    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.5s ease";
            alert.style.opacity    = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    const allowedPattern = /^[a-zA-Z0-9\s.,-]+$/;
    document.querySelectorAll('input[type="text"]').forEach(input => {
        input.addEventListener('input', function () {
            if (this.value !== "" && !allowedPattern.test(this.value)) {
                this.value = this.value.replace(/[^a-zA-Z0-9\s.,-]/g, '');
                this.classList.add('input-error');
                setTimeout(() => this.classList.remove('input-error'), 800);
            }
        });
    });

    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function (e) {
            const ok = confirm("Apakah Anda yakin ingin keluar dari sistem?");
            if (!ok) {
                e.preventDefault();
            } else {
                sessionStorage.removeItem('browser_session_active');
            }
        });
    }

    document.querySelectorAll('.star-radio input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', function () {
            document.querySelectorAll('.star-radio').forEach(label => {
                label.classList.remove('selected');
            });
            this.closest('.star-radio').classList.add('selected');
        });
    });

    
    document.querySelectorAll('textarea').forEach(t => {
        if (!t.placeholder) {
            t.placeholder = "Ceritakan pengalaman perjalanan Anda...";
        }
    });
    
    document.querySelectorAll('.form-group > label:first-child').forEach(label => {
        if(label.innerHTML.includes('Skor') || label.innerHTML.includes('Ulasan')) {
            label.style.display = 'none';
        }
    });

    const bintangs = document.querySelectorAll('.bintang-item');

    if (bintangs.length > 0) {
        bintangs.forEach(b => {
            b.addEventListener('click', function() {
                bintangs.forEach(item => item.classList.remove('aktif'));
                
                this.classList.add('aktif');

                const val = this.getAttribute('data-val');
                const hiddenRadio = document.querySelector(`input[name="skor"][value="${val}"]`);
                if (hiddenRadio) {
                    hiddenRadio.checked = true;
                }
            });
        });
    }

});