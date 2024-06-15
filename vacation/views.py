from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum
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
from vacation.models import LeaveRequest, VacationUsed
from vacation.forms import LeaveRequestForm


class UserLeaveRequestMixin(LoginRequiredMixin):
    """Mixin to filter leave requests by the current user."""

    def get_queryset(self):
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestListView(UserLeaveRequestMixin, ListView):
    """View for displaying a list of leave requests."""

    model = LeaveRequest
    template_name = "vacation/leave_request_list.html"
    context_object_name = "leave_requests"


class LeaveRequestDetailView(UserLeaveRequestMixin, DetailView):
    """View to display the details of an individual leave request."""

    model = LeaveRequest
    template_name = "vacation/leave_request_detail.html"
    context_object_name = "leave_request"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["saved"] = StatusRequestChoices.SAVED
        leave_request = self.get_object()
        employee = leave_request.employee
        vacation_days_used = (
            VacationUsed.objects.get(employee=employee).days or 0
        )
        context["vacation_days_used"] = vacation_days_used
        return context


class LeaveRequestFormMixin(UserLeaveRequestMixin):
    """Mixin to set common attributes for create and update views."""

    model = LeaveRequest
    context_object_name = "leave_request"
    form_class = LeaveRequestForm
    template_name = "vacation/leave_request_form.html"
    success_url = reverse_lazy("vacation:leave_request_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vacation_used = VacationUsed.objects.filter(
            employee=self.request.user
        ).first()
        context["vacation_days_used"] = (
            vacation_used.days if vacation_used else 0
        )
        return context

    def form_valid(self, form):
        form.instance.employee = self.request.user
        if "save" in self.request.POST:
            return super().form_valid(form)
        elif "save_and_submit" in self.request.POST:
            response = super().form_valid(form)
            self.object.submit_for_approval()
            return response
        return super().form_invalid(form)


class LeaveRequestCreateView(LeaveRequestFormMixin, CreateView):
    """View for creating a new leave request."""


class LeaveRequestUpdateView(
    LeaveRequestFormMixin, SuccessMessageMixin, UpdateView
):
    """View for editing an existing leave request."""

    success_message = _("Your changes have been successfully saved.")

    def dispatch(self, request, *args, **kwargs):
        leave_request = self.get_object()
        if leave_request.status != StatusRequestChoices.SAVED:
            messages.warning(
                request,
                _("You can only edit leave requests with a pending status."),
            )
            return redirect("vacation:leave_request_list")
        return super().dispatch(request, *args, **kwargs)


class LeaveRequestDeleteView(UserLeaveRequestMixin, DeleteView):
    """View for deleting a leave application."""

    model = LeaveRequest
    context_object_name = "leave_request"
    template_name = "vacation/leave_request_confirm_delete.html"
    success_url = reverse_lazy("vacation:leave_request_list")

    def dispatch(self, request, *args, **kwargs):
        leave_request = self.get_object()
        if leave_request.status != StatusRequestChoices.SAVED:
            messages.warning(
                request,
                _("You can only delete leave requests with a pending status."),
            )
            return redirect("vacation:leave_request_list")
        return super().dispatch(request, *args, **kwargs)
