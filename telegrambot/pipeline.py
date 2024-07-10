import logging

from allauth.socialaccount.models import SocialLogin
from django.contrib.auth import get_user_model
from django.db import transaction

from telegrambot.adapters import CustomSocialAccountAdapter

User = get_user_model()
logger = logging.getLogger(__name__)


class SocialLoginPipeline:
    """
    Pipeline for handling social logins and ensuring consistency in user data.
    """

    @classmethod
    def run(cls, request, sociallogin: SocialLogin):
        """
        Run the pipeline steps for processing social login.

        Args:
            request (HttpRequest): HTTP request that caused the login.
            sociallogin (SocialLogin): Information about the social login.
        """
        cls._link_social_login_to_user(request, sociallogin)
        cls._update_user_data_from_social(sociallogin)
        cls._finalize_social_login(request, sociallogin)

    @staticmethod
    def _link_social_login_to_user(request, sociallogin):
        """
        Link the social login to an existing user or create a new user.

        Args:
            request (HttpRequest): HTTP request that caused the login.
            sociallogin (SocialLogin): Information about the social login.
        """
        adapter = CustomSocialAccountAdapter()
        adapter.pre_social_login(request, sociallogin)

    @staticmethod
    def _update_user_data_from_social(sociallogin):
        """
        Update the user's data from the social login information.

        Args:
            sociallogin (SocialLogin): Information about the social login.
        """
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data

        user.email = extra_data.get("email", user.email)
        user.first_name = extra_data.get("first_name", user.first_name)
        user.last_name = extra_data.get("last_name", user.last_name)
        user.username = extra_data.get("username", user.username)

        try:
            with transaction.atomic():
                user.save()
                logger.info(f"User {user.username} updated from social login.")
        except Exception as e:
            logger.error(f"Error saving user {user.username}: {e}")
            raise

    @staticmethod
    def _finalize_social_login(request, sociallogin):
        """
        Finalize the social login process.

        Args:
            sociallogin (SocialLogin): Information about the social login.
        """
        try:
            sociallogin.save(request)
            logger.info(f"Social login for user {sociallogin.user.username} finalized.")
        except Exception as e:
            logger.error(f"Error finalizing social login for user {sociallogin.user.username}: {e}")
            raise
