from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView

from . import forms


class RegisterView(CreateView):
    form_class = forms.RegisterForm
    template_name = "users/register.html"

    def get_success_url(self):
        messages.success(self.request, _("Your account has been created. You can now log in."))
        return reverse("core:index")
