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

    // Form validation
    $('form').on('submit', function () {
        $(this).find('button[type="submit"]').prop('disabled', true).html(
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...'
        );
    });
});
