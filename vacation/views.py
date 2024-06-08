from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _

from common.enums import StatusRequestChoices
from .models import LeaveRequest
from .forms import LeaveRequestForm


class LeaveRequestListView(LoginRequiredMixin, ListView):
    """Представлення для відображення списку заявок на відпустку."""

    model = LeaveRequest
    template_name = "vacation/leave_request_list.html"
    context_object_name = "leave_requests"

    def get_queryset(self):
        """Повертає список заявок тільки для поточного користувача."""
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestDetailView(LoginRequiredMixin, DetailView):
    """Представлення для відображення деталей окремої заявки на відпустку."""

    model = LeaveRequest
    template_name = "vacation/leave_request_detail.html"
    context_object_name = "leave_request"

    def get_queryset(self):
        """Переконується, що користувач може бачити тільки свої заявки."""
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    """Представлення для створення нової заявки на відпустку."""

    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "vacation/leave_request_form.html"
    success_url = reverse_lazy("vacation:leave_request_list")

    def form_valid(self, form):
        """Встановлює поточного користувача як автора заявки."""
        form.instance.employee = self.request.user
        return super().form_valid(form)


class LeaveRequestUpdateView(
    LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Editing an existing leave request."""

    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "vacation/leave_request_form.html"
    success_message = _("Your information has been changed")
    success_url = reverse_lazy("vacation:leave_request_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_full_name"] = (
            f"{self.request.user.first_name} {self.request.user.last_name}"
        )
        return context

    def get_queryset(self):
        """Переконується, що користувач може редагувати тільки свої заявки."""
        return LeaveRequest.objects.filter(
            employee=self.request.user, status=StatusRequestChoices.PENDING
        )


class LeaveRequestDeleteView(LoginRequiredMixin, DeleteView):
    """Представлення для видалення заявки на відпустку."""

    model = LeaveRequest
    template_name = "leave_request_confirm_delete.html"
    success_url = reverse_lazy("leave_request_list")

    def get_queryset(self):
        """Переконується, що користувач може видаляти тільки свої заявки."""
        return LeaveRequest.objects.filter(employee=self.request.user)
