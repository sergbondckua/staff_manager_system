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
from vacation.models import LeaveRequest
from vacation.forms import LeaveRequestForm


class LeaveRequestListView(LoginRequiredMixin, ListView):
    """A view for displaying a list of leave requests."""

    model = LeaveRequest
    template_name = "vacation/leave_request_list.html"
    context_object_name = "leave_requests"

    def get_queryset(self):
        # Returns a list of applications for the current user only.
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestDetailView(LoginRequiredMixin, DetailView):
    """A representation to display the details of an individual leave request."""

    model = LeaveRequest
    template_name = "vacation/leave_request_detail.html"
    context_object_name = "leave_request"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending"] = StatusRequestChoices.PENDING
        return context

    def get_queryset(self):
        # Makes sure that the user can see only his applications.
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    """Presentation for creating a new leave request."""

    model = LeaveRequest
    context_object_name = "leave_request"
    form_class = LeaveRequestForm
    template_name = "vacation/leave_request_form.html"
    success_url = reverse_lazy("vacation:leave_request_list")

    def form_valid(self, form):
        # Sets the current user as the submitter.
        form.instance.employee = self.request.user
        return super().form_valid(form)


class LeaveRequestUpdateView(
    LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Editing an existing leave request."""

    model = LeaveRequest
    context_object_name = "leave_request"
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
    """Submission to delete leave application."""

    model = LeaveRequest
    context_object_name = "leave_request"
    template_name = "vacation/leave_request_confirm_delete.html"
    success_url = reverse_lazy("vacation:leave_request_list")

    def get_queryset(self):
        # Makes sure that the user can only delete their applications.
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
