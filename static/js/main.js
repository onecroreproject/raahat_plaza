/* ═══════════════════════════════════════════════════════════════
   Raahat Plaza - Main JavaScript
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ─── Mobile Sidebar Toggle ─────────────────────────────
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (mobileToggle) {
        mobileToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }

    // ─── Auto-dismiss Alerts ────────────────────────────────
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function () {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // ─── Confirm Delete ─────────────────────────────────────
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const message = btn.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // ─── Active Nav Highlight ───────────────────────────────
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function (link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    // ─── File Upload Label ──────────────────────────────────
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            const fileName = this.files[0] ? this.files[0].name : 'Choose file';
            const label = this.closest('.form-group')?.querySelector('.file-label');
            if (label) {
                label.textContent = fileName;
            }
        });
    });

    // ─── Smooth Scroll ──────────────────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ─── Ownership Type Toggle ──────────────────────────────
    const ownershipField = document.getElementById('shop-ownership');
    const ownerField = document.getElementById('shop-owner');
    if (ownershipField && ownerField) {
        function toggleOwnerField() {
            const ownerGroup = ownerField.closest('.form-group');
            if (ownershipField.value === 'admin') {
                ownerGroup.style.display = 'none';
                ownerField.value = '';
            } else {
                ownerGroup.style.display = 'block';
            }
        }
        toggleOwnerField();
        ownershipField.addEventListener('change', toggleOwnerField);
    }

    // ─── CSRF Token Helper ──────────────────────────────────
    window.getCSRFToken = function () {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    };

    // ─── Number Counter Animation ───────────────────────────
    const counters = document.querySelectorAll('[data-count]');
    if (counters.length > 0) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-count'));
                    let current = 0;
                    const increment = Math.ceil(target / 60);
                    const timer = setInterval(function () {
                        current += increment;
                        if (current >= target) {
                            el.textContent = target.toLocaleString();
                            clearInterval(timer);
                        } else {
                            el.textContent = current.toLocaleString();
                        }
                    }, 16);
                    observer.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(function (counter) {
            observer.observe(counter);
        });
    }
});
