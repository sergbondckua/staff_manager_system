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
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from common.enums import StatusRequestChoices
from staff.models import DutyRoster, Employee
from vacation.models import LeaveRequest, VacationUsed
from vacation.forms import LeaveRequestForm
from vacation.serializers import LeaveRequestUserSerializer


class UserLeaveRequestMixin(LoginRequiredMixin):
    """Mixin to filter leave requests by the current user."""

    def get_queryset(self):
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestListView(UserLeaveRequestMixin, ListView):
    """View for displaying a list of leave requests."""

    model = LeaveRequest
    template_name = "vacation/leave_request_list.html"
    context_object_name = "leave_requests"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        duty_now = DutyRoster.objects.order_by("pk").last()  # Current duty
        context["duty_now"] = duty_now if duty_now else None
        return context


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


class IsTelegramUserId(BasePermission):
    """
    Custom permission to grant access if the request contains a 'telegram_id' in
    the GET parameters or if the user is authenticated.
    """

    def has_permission(self, request, view) -> bool:
        """
        Check if the request has a 'telegram_id' parameter or if the user is authenticated.
        """
        return bool(
            request.GET.get("telegram_id")
            or (request.user and request.user.is_authenticated)
        )


class LeaveRequestUserViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestUserSerializer
    permission_classes = [IsTelegramUserId]

    def get_request_user(self) -> Employee | None:
        """
        Returns the Employee object corresponding to the provided telegram_id
        if it exists, otherwise returns the authenticated User.
        """
        telegram_id = self.request.GET.get("telegram_id")

        if telegram_id:
            try:
                user = Employee.objects.get(telegram_id=telegram_id)
                return user
            except Employee.DoesNotExist:
                return None

        return self.request.user

    def get_queryset(self):
        return LeaveRequest.objects.filter(employee=self.get_request_user())

    def perform_create(self, serializer):
        serializer.save(employee=self.get_request_user())

    def perform_update(self, serializer):
        if (
            "status" in serializer.validated_data
            and serializer.validated_data["status"]
            == StatusRequestChoices.PENDING
        ):
            return Response(
                {
                    "detail": _(
                        "You can only edit leave requests with a saved status."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        leave_request = self.get_object()
        if leave_request.status != StatusRequestChoices.SAVED:
            return Response(
                {
                    "detail": _(
                        "You can only delete leave requests with a saved status."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def vacation_days_used(self, request):
        vacation_used = VacationUsed.objects.filter(
            employee=self.get_request_user()
        ).first()
        days_used = vacation_used.days if vacation_used else 0
        return Response({"vacation_days_used": days_used})

    @action(detail=True, methods=["post"])
    def save_and_submit(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.submit_for_approval()
        leave_request.save()
        return Response({"status": _("Leave request submitted for approval")})
