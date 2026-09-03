(function () {
    'use strict';

    // Sidebar toggle (mobile)
    var sidebarToggle = document.getElementById('sidebar-toggle');
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            if (sidebar) sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // User dropdown menu
    var userChip = document.querySelector('.user-chip');
    var userDropdown = document.querySelector('.user-dropdown');
    if (userChip && userDropdown) {
        userChip.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('open');
        });
        document.addEventListener('click', function () {
            userDropdown.classList.remove('open');
        });
    }

    // Dismiss alerts
    document.querySelectorAll('[data-dismiss-alert]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var alert = btn.closest('.alert');
            if (alert) alert.remove();
        });
    });

    // Auto-hide success alerts after 5 seconds
    document.querySelectorAll('.alert-success').forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function () { if (alert.parentNode) alert.parentNode.removeChild(alert); }, 500);
        }, 5000);
    });

    // Confirm dialogs for delete forms handled inline via onsubmit attributes
})();
