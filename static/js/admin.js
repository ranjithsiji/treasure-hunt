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

    // ──────────────────────────────────────────────────────────
    // Sidebar: active item detection, submenu & scroll persistence,
    //          search, expand-all / collapse-all.
    // ──────────────────────────────────────────────────────────
    const SUBMENU_KEY = 'sidebarSubmenuState_v2';
    const SCROLL_KEY = 'sidebarScrollTop';

    function getSubmenuState() {
        try { return JSON.parse(localStorage.getItem(SUBMENU_KEY)) || {}; }
        catch (_) { return {}; }
    }
    function setSubmenuState(state) {
        localStorage.setItem(SUBMENU_KEY, JSON.stringify(state));
    }

    // Mark the active page (exact-match on pathname) on a sub-item and
    // force its containing submenu open — this overrides a previously-saved
    // "collapsed" state so you never land on a hidden active item.
    const currentPath = window.location.pathname;
    $('.sidebar-subitem').each(function () {
        if ($(this).attr('href') === currentPath) {
            $(this).addClass('active');
            $(this).closest('.sidebar-submenu').addClass('show');
        }
    });
    $('.sidebar-item').each(function () {
        // Only exact-match top-level (non-toggle) items
        const href = $(this).attr('href');
        if (href && href !== '#' && !$(this).attr('data-bs-toggle') && href === currentPath) {
            $(this).addClass('active');
        }
    });

    // Restore submenu open/closed states from localStorage (but never
    // close a submenu that contains the current active page).
    const savedState = getSubmenuState();
    $('.sidebar-submenu').each(function () {
        const id = this.id;
        if (!id) return;
        const hasActive = $(this).find('.sidebar-subitem.active').length > 0;
        if (hasActive) return;
        if (savedState[id] === true) $(this).addClass('show');
        else if (savedState[id] === false) $(this).removeClass('show');
    });

    // Track state via Bootstrap's collapse events (these fire AFTER the
    // transition — the old click-handler fired BEFORE and was racy).
    $('.sidebar-submenu').on('shown.bs.collapse', function () {
        const state = getSubmenuState();
        state[this.id] = true;
        setSubmenuState(state);
    }).on('hidden.bs.collapse', function () {
        const state = getSubmenuState();
        state[this.id] = false;
        setSubmenuState(state);
    });

    // Persist and restore sidebar scroll position across navigations.
    // Note: the scrollable element is #sidebarMenu (flex child with overflow),
    // not #sidebar itself — the outer element hides overflow.
    const $sidebarScroll = $('#sidebarMenu');
    const savedScroll = parseInt(sessionStorage.getItem(SCROLL_KEY), 10);
    if (!isNaN(savedScroll)) $sidebarScroll.scrollTop(savedScroll);

    let scrollSaveTimer = null;
    $sidebarScroll.on('scroll', function () {
        clearTimeout(scrollSaveTimer);
        scrollSaveTimer = setTimeout(function () {
            sessionStorage.setItem(SCROLL_KEY, $sidebarScroll.scrollTop());
        }, 50);
    });
    $(window).on('beforeunload', function () {
        sessionStorage.setItem(SCROLL_KEY, $sidebarScroll.scrollTop());
    });

    // Expand all / Collapse all
    function forEachSubmenu(fn) {
        $('.sidebar-submenu').each(function () {
            const inst = bootstrap.Collapse.getOrCreateInstance(this, { toggle: false });
            fn(inst, this);
        });
    }
    $('#sidebarExpandAll').on('click', function () {
        forEachSubmenu(function (inst) { inst.show(); });
    });
    $('#sidebarCollapseAll').on('click', function () {
        forEachSubmenu(function (inst) { inst.hide(); });
    });

    // Search / filter menu items.
    // A match: the text of a top-level item, OR of a sub-item (which also
    // opens its parent group). Non-matching rows are hidden.
    const $search = $('#sidebarSearch');
    const $searchClear = $('#sidebarSearchClear');
    const $noResults = $('#sidebarNoResults');
    const submenuStateBeforeSearch = {};

    function normaliseText(el) {
        return (el.textContent || '').trim().toLowerCase();
    }

    function applyFilter(query) {
        query = query.trim().toLowerCase();
        const $menu = $('#sidebarMenu');
        const filtering = query.length > 0;
        $menu.toggleClass('sidebar-filtering', filtering);

        if (!filtering) {
            // Restore pre-search submenu state
            forEachSubmenu(function (inst, el) {
                if (submenuStateBeforeSearch[el.id]) inst.show();
                else inst.hide();
            });
            $('#sidebarMenu .sidebar-item, #sidebarMenu .sidebar-subitem, #sidebarMenu .sidebar-item-group, #sidebarMenu .sidebar-divider, #sidebarMenu .sidebar-section-title')
                .removeClass('sidebar-hidden');
            $noResults.prop('hidden', true);
            $searchClear.prop('hidden', true);
            return;
        }
        $searchClear.prop('hidden', false);

        // Snapshot current open-state the first time we begin filtering.
        if (Object.keys(submenuStateBeforeSearch).length === 0) {
            $('.sidebar-submenu').each(function () {
                submenuStateBeforeSearch[this.id] = $(this).hasClass('show');
            });
        }

        let anyMatch = false;

        // Top-level direct items (not group toggles): match on own text.
        $('#sidebarMenu > .sidebar-item').each(function () {
            const match = normaliseText(this).includes(query);
            $(this).toggleClass('sidebar-hidden', !match);
            if (match) anyMatch = true;
        });

        // Groups: show group if parent text matches OR any sub-item matches.
        $('#sidebarMenu > .sidebar-item-group').each(function () {
            const $group = $(this);
            const $toggle = $group.children('.sidebar-item');
            const $submenu = $group.children('.sidebar-submenu');
            const toggleText = normaliseText($toggle[0]);
            const toggleMatch = toggleText.includes(query);

            let subMatchCount = 0;
            $submenu.find('.sidebar-subitem').each(function () {
                const match = normaliseText(this).includes(query) || toggleMatch;
                $(this).toggleClass('sidebar-hidden', !match);
                if (match) subMatchCount++;
            });

            const groupVisible = toggleMatch || subMatchCount > 0;
            $group.toggleClass('sidebar-hidden', !groupVisible);

            const inst = bootstrap.Collapse.getOrCreateInstance($submenu[0], { toggle: false });
            if (groupVisible) {
                anyMatch = true;
                inst.show();
            } else {
                inst.hide();
            }
        });

        // Hide purely decorative rows while filtering
        $('#sidebarMenu .sidebar-divider, #sidebarMenu .sidebar-section-title')
            .addClass('sidebar-hidden');

        $noResults.prop('hidden', anyMatch);
    }

    $search.on('input', function () { applyFilter(this.value); });
    $searchClear.on('click', function () {
        $search.val('').trigger('input').focus();
    });

    // Ctrl/Cmd + K focuses the search
    $(document).on('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            $search.focus().select();
        }
    });

    // Smooth scroll for anchor links — skip Bootstrap toggles (collapse, tab,
    // modal, dropdown, etc.) so we don't fight their handlers on the sidebar.
    $('a[href^="#"]').not('[data-bs-toggle]').on('click', function (e) {
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
