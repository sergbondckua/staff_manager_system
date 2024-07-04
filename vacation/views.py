from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
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
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from common.enums import StatusRequestChoices
from common.env import env
from staff.models import DutyRoster, Employee
from staff.services import check_telegram_auth
from vacation.models import LeaveRequest, VacationUsed, LeaveType
from vacation.forms import LeaveRequestForm
from vacation.serializers import (
    LeaveRequestUserSerializer,
    VacationLeaveTypeSerializer,
)


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["employee"] = self.request.user
        return kwargs

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
            request.data.get("telegram_id")
            or (request.user and request.user.is_authenticated)
        )


class LeaveTypeViewSet(viewsets.ModelViewSet):
    serializer_class = VacationLeaveTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Get all LeaveTypes with an additional subtypes_count field.
        Only those LeaveTypes that have a parent or no subtypes are returned.
        """
        try:
            queryset = LeaveType.objects.annotate(subtypes_count=Count("subtypes"))
            filtered_queryset = queryset.filter(
                Q(parent__isnull=False) | Q(parent__isnull=True, subtypes_count=0)
            )
            return filtered_queryset
        except LeaveType.DoesNotExist:
            return LeaveType.objects.none()


class LeaveRequestUserViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestUserSerializer
    permission_classes = [IsTelegramUserId]

    def get_request_user(self) -> Employee | None:
        """
        Returns the Employee object corresponding to the provided telegram_id
        if it exists, otherwise returns the authenticated User.
        """

        user = (
            self.request.user if self.request.user.is_authenticated else None
        )
        telegram_id = self.request.data.get("telegram_id")
        auth_date = self.request.data.get("auth_date")
        hash_data = self.request.data.get("hash")

        if telegram_id and auth_date and hash_data:
            if check_telegram_auth(self.request.data, env.str("BOT_TOKEN")):
                try:
                    user = Employee.objects.get(telegram_id=telegram_id)
                    return user
                except Employee.DoesNotExist:
                    return None
        return user

    def get_queryset(self):
        request_user = self.get_request_user()
        if not request_user:
            # Return an empty queryset if no user is found
            return LeaveRequest.objects.none()
        return LeaveRequest.objects.filter(employee=request_user)

    def create(self, request, *args, **kwargs):
        """Handle the creation of a new vacation record with validation."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Check if start_date is in the past
        start_date = validated_data.get("start_date", "0000-00-00")
        if start_date < timezone.now().date():
            return Response(
                {
                    "status": _(
                        "Start date cannot be earlier than the current date."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if start_date is after end_date
        end_date = validated_data.get("end_date", "0000-00-00")
        if start_date >= end_date:
            return Response(
                {
                    "status": _(
                        "Start date cannot be later than or equal to end date."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        """Save the new vacation record with the current user as the employee."""

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

    @action(detail=False, methods=["get"])
    def telegram_is_employee(self, request):
        try:
            Employee.objects.get(telegram_id=request.data.get("telegram_id"))
            return Response({"status": True})
        except Employee.DoesNotExist:
            return Response({"status": False})

    @action(detail=False, methods=["get"])
    def check_overlap(self, request):
        telegram_id = request.data.get("telegram_id")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        overlapping_requests = LeaveRequest.objects.filter(
            employee__telegram_id=telegram_id,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        overlap = overlapping_requests.exists()
        overlapping_dates = (
            ",\n".join(
                f"#{req.pk}: {req.start_date} - {req.end_date}"
                for req in overlapping_requests
            )
            if overlap
            else None
        )
        return Response(
            {"overlap": overlap, "leave_request": overlapping_dates}
        )

    @action(detail=True, methods=["post"])
    def save_and_submit(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.submit_for_approval()
        leave_request.save()
        return Response({"status": _("Leave request submitted for approval")})
