from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
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
    success_message = _("Your changes have been successfully saved.")
    success_url = reverse_lazy("vacation:leave_request_list")


    def get_queryset(self):
        # Makes sure that the user can only edit their applications.
        return LeaveRequest.objects.filter(employee=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        # Get the leave request object
        leave_request = self.get_object()
        # Check if the status is not pending
        if leave_request.status != StatusRequestChoices.PENDING:
            # Add a warning message
            messages.warning(
                request,
                _("You can only edit leave requests with a pending status."),
            )
            # Redirect to the leave request list
            return redirect("vacation:leave_request_list")
        # Proceed with the normal dispatch method
        return super().dispatch(request, *args, **kwargs)


class LeaveRequestDeleteView(LoginRequiredMixin, DeleteView):
    """Представлення для видалення заявки на відпустку."""

    model = LeaveRequest
    template_name = "vacation/leave_request_confirm_delete.html"
    success_message = _("Your leave request has been successfully deleted.")
    success_url = reverse_lazy("vacation:leave_request_list")

    def get_queryset(self):
        """Переконується, що користувач може видаляти тільки свої заявки."""
        return LeaveRequest.objects.filter(employee=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        leave_request = self.get_object()

        if leave_request.status != StatusRequestChoices.PENDING:
            messages.warning(
                request,
                _("You can only delete leave requests with a pending status."),
            )
            return redirect("vacation:leave_request_list")
        return super().dispatch(request, *args, **kwargs)
