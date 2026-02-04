// Admin Panel JavaScript

$(document).ready(function () {
    // Sidebar Toggle
    $('#sidebarToggle').on('click', function () {
        $('#sidebar').toggleClass('collapsed');
        $('#mainContent').toggleClass('expanded');

        // Save state to localStorage
        const isCollapsed = $('#sidebar').hasClass('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    });

    // Restore sidebar state from localStorage
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed');
    if (sidebarCollapsed === 'true') {
        $('#sidebar').addClass('collapsed');
        $('#mainContent').addClass('expanded');
    }

    // Mobile: Close sidebar when clicking outside
    $(document).on('click', function (e) {
        if ($(window).width() <= 768) {
            if (!$(e.target).closest('#sidebar, #sidebarToggle').length) {
                $('#sidebar').removeClass('show');
            }
        }
    });

    // Mobile: Show sidebar on toggle
    if ($(window).width() <= 768) {
        $('#sidebarToggle').on('click', function (e) {
            e.stopPropagation();
            $('#sidebar').toggleClass('show');
        });
    }

    // Keep submenu open if current page is in submenu
    $('.sidebar-subitem').each(function () {
        if ($(this).attr('href') === window.location.pathname) {
            $(this).closest('.collapse').addClass('show');
            $(this).addClass('active');
        }
    });

    // Highlight active menu item
    $('.sidebar-item').each(function () {
        const href = $(this).attr('href');
        if (href && href !== '#' && window.location.pathname.startsWith(href)) {
            $(this).addClass('active');
        }
    });

    // Smooth scroll for anchor links
    $('a[href^="#"]').on('click', function (e) {
        const target = $(this).attr('href');
        if (target !== '#' && $(target).length) {
            e.preventDefault();
            $('html, body').animate({
                scrollTop: $(target).offset().top - 100
            }, 500);
        }
    });

    // Confirmation dialogs for delete actions
    $('.delete-action').on('click', function (e) {
        const itemName = $(this).data('item-name') || 'this item';
        if (!confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
            e.preventDefault();
            return false;
        }
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Form submission loading state
    $('form').on('submit', function () {
        const submitBtn = $(this).find('button[type="submit"]');
        if (!submitBtn.prop('disabled')) {
            submitBtn.prop('disabled', true);
            const originalText = submitBtn.html();
            submitBtn.html('<span class="loading-spinner"></span> Processing...');

            // Re-enable after 5 seconds as fallback
            setTimeout(function () {
                submitBtn.prop('disabled', false);
                submitBtn.html(originalText);
            }, 5000);
        }
    });

    // Tooltip initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Popover initialization
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // DataTable-like search functionality
    $('#tableSearch').on('keyup', function () {
        const value = $(this).val().toLowerCase();
        $('#dataTable tbody tr').filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Counter animation for stats
    $('.stat-card-value').each(function () {
        const $this = $(this);
        const countTo = parseInt($this.text());

        if (!isNaN(countTo)) {
            $({ countNum: 0 }).animate({
                countNum: countTo
            }, {
                duration: 1000,
                easing: 'swing',
                step: function () {
                    $this.text(Math.floor(this.countNum));
                },
                complete: function () {
                    $this.text(this.countNum);
                }
            });
        }
    });

    // Refresh page data without full reload
    $('.refresh-data').on('click', function (e) {
        e.preventDefault();
        const $btn = $(this);
        const originalHtml = $btn.html();

        $btn.html('<span class="loading-spinner"></span>');
        $btn.prop('disabled', true);

        setTimeout(function () {
            location.reload();
        }, 500);
    });

    // Copy to clipboard functionality
    $('.copy-to-clipboard').on('click', function () {
        const text = $(this).data('clipboard-text');
        navigator.clipboard.writeText(text).then(function () {
            // Show success message
            const $btn = $(this);
            const originalText = $btn.text();
            $btn.text('Copied!');
            setTimeout(function () {
                $btn.text(originalText);
            }, 2000);
        });
    });

    // Prevent double submission
    let formSubmitting = false;
    $('form').on('submit', function (e) {
        if (formSubmitting) {
            e.preventDefault();
            return false;
        }
        formSubmitting = true;

        // Reset after 3 seconds
        setTimeout(function () {
            formSubmitting = false;
        }, 3000);
    });

    // Auto-resize textareas
    $('textarea').each(function () {
        this.setAttribute('style', 'height:' + (this.scrollHeight) + 'px;overflow-y:hidden;');
    }).on('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Sidebar submenu persistence
    $('.sidebar-item[data-bs-toggle="collapse"]').on('click', function () {
        const target = $(this).attr('href');
        const isExpanded = $(target).hasClass('show');

        // Save state
        localStorage.setItem('submenu_' + target, !isExpanded);
    });

    // Restore submenu states
    $('.sidebar-submenu').each(function () {
        const id = '#' + $(this).attr('id');
        const wasExpanded = localStorage.getItem('submenu_' + id);

        if (wasExpanded === 'true') {
            $(this).addClass('show');
        }
    });
});

// Window resize handler
$(window).on('resize', function () {
    if ($(window).width() > 768) {
        $('#sidebar').removeClass('show');
    }
});

// Keyboard shortcuts
$(document).on('keydown', function (e) {
    // Ctrl/Cmd + B to toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        $('#sidebarToggle').click();
    }

    // Escape to close sidebar on mobile
    if (e.key === 'Escape' && $(window).width() <= 768) {
        $('#sidebar').removeClass('show');
    }
});
