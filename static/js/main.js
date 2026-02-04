$(document).ready(function () {
    // Auto-hide alerts after 5 seconds
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Confirm delete actions
    $('.delete-btn').on('click', function (e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
        }
    });

    // Form loading state
    $('form').on('submit', function (e) {
        const $button = $(this).find('button[type="submit"]');
        const originalHtml = $button.html();

        // Use timeout to allow other submit handlers (validation) to run first
        // and potentially call e.preventDefault()
        setTimeout(() => {
            if (!e.isDefaultPrevented()) {
                $button.prop('disabled', true).html(
                    '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...'
                );
            }
        }, 0);
    });
});
