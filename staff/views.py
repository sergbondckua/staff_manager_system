from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView
from django.utils.translation import gettext_lazy as _

from staff.forms import EmployeeForm


class ProfileView(DetailView):
    """View profile"""

    model = get_user_model()

    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Views update profiles"""

    model = get_user_model()
    form_class = EmployeeForm
    success_message = _("Your profile information has been changed")
    success_url = reverse_lazy("staff:account_profile_update")

    def get_object(self):
        return self.request.user
