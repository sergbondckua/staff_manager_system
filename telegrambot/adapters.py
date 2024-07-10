import requests
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from common.logger import logger

User = get_user_model()


class TelegramAccountAdapter(DefaultSocialAccountAdapter):
    """Adapter for handling Telegram social account login."""

    def pre_social_login(self, request, sociallogin):
        """
        Handle pre-social login process.
        Connects an existing user or creates a new one based on Telegram ID.
        """
        extra_data = sociallogin.account.extra_data
        telegram_id = extra_data.get("id")
        first_name = extra_data.get("first_name", "")
        last_name = extra_data.get("last_name", "")
        username = extra_data.get("username", "")
        photo_url = extra_data.get("photo_url")

        user = self._get_or_create_user(
            telegram_id,
            first_name,
            last_name,
            username,
            photo_url,
            sociallogin,
        )
        sociallogin.user = user

        return user

    def save_user(self, request, sociallogin, form=None):
        """Save the user associated with the social login."""
        self.populate_user(
            request, sociallogin, sociallogin.account.extra_data
        )
        user = sociallogin.user

        if not user.pk:
            user.set_unusable_password()
            self._save_new_user(user)
        else:
            user.save()
            logger.info("Existing user updated: %s", user)

        return user

    def _get_or_create_user(
        self,
        telegram_id,
        first_name,
        last_name,
        username,
        photo_url,
        sociallogin,
    ):
        """Get an existing user or create a new one."""
        try:
            user = User.objects.get(telegram_id=telegram_id)
            self._update_existing_user(user, first_name, last_name, photo_url)
            logger.info(
                "Existing user found for telegram_id %s: %s", telegram_id, user
            )
            sociallogin.connect(request=self.request, user=user)
        except User.DoesNotExist:
            logger.info(
                "No user found for telegram_id %s, creating a new one.",
                telegram_id,
            )
            user = self._create_new_user(
                sociallogin,
                telegram_id,
                first_name,
                last_name,
                username,
                photo_url,
            )

        return user

    def _update_existing_user(self, user, first_name, last_name, photo_url):
        """Update the user associated with the social login."""
        user.first_name = user.first_name or first_name
        user.last_name = user.last_name or last_name

        if photo_url and not user.photo:
            self._download_user_photo(user, photo_url)

    def _create_new_user(
        self,
        sociallogin,
        telegram_id,
        first_name,
        last_name,
        username,
        photo_url,
    ):
        """Create a new user with the given data."""
        user = sociallogin.user
        user.telegram_id = telegram_id
        user.first_name = first_name
        user.last_name = last_name
        user.username = self._get_unique_username(username)

        if photo_url:
            self._download_user_photo(user, photo_url)

        return user

    @staticmethod
    def _download_user_photo(user, photo_url):
        """Download and save the user's profile photo from the given URL."""
        try:
            response = requests.get(photo_url)
            response.raise_for_status()
            user.photo.save(
                f"{user.username}_photo.jpg",
                ContentFile(response.content),
                save=False,
            )
        except Exception as e:
            logger.error("Error downloading photo: %s", e)

    def _save_new_user(self, user):
        """Save a new user to the database, ensuring a unique username."""
        try:
            user.save()
            logger.info("New user created: %s", user)
        except IntegrityError:
            user.username = self._get_unique_username(user.username)
            user.save()
            logger.info("New user created with unique username: %s", user)

    @staticmethod
    def _get_unique_username(username):
        """Generate a unique username by appending a counter if the username already exists."""
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
        return username
