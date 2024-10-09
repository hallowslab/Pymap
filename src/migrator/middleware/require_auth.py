import logging
from django.http.response import HttpResponseRedirect, HttpResponse
from django.http.request import HttpRequest
from django.urls import reverse

logger = logging.getLogger(__name__)


def staff_only(get_response):
    # One-time configuration and initialization.

    def middleware(request: HttpRequest) -> (HttpResponse | HttpResponseRedirect):
        admin_login_url: str = reverse("admin:login")
        admin_logout_url: str = reverse("admin:logout")
        migrator_index: str = reverse("migrator:index")
        logger.debug("Checking path %s", request.path)
        # Check if the request is to the admin page (but not login or logout) and if the user is not a staff member
        if (
            request.path.startswith(reverse("admin:index"))
            and request.path not in [admin_login_url, admin_logout_url, migrator_index]
            and not request.user.is_staff
        ):
            logger.debug("Intercepted path %s, setting cookie" % (request.path))
            # Redirect non-staff users to the migrator:index page
            response = HttpResponseRedirect(reverse("migrator:index"))
            response.set_cookie(
                "privilege_warning", "true", max_age=10
            )  # Set a short-lived cookie
            return response

        # Proceed with the response if the user is staff or not accessing admin page
        response = get_response(request)
        return response

    return middleware
