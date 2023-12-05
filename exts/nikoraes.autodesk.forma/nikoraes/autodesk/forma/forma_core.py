import omni.kit.notification_manager as notification_manager
import carb

from .forma_data import SEVERITY


def log(
    msg: str,
    severity: SEVERITY,
    notify: bool = False,
    hide_after_timeout: bool = True,
):
    if severity == SEVERITY.INFO:
        carb.log_info(msg)
        if notify is True:
            notification_manager.post_notification(
                msg,
                status=notification_manager.NotificationStatus.INFO,
                hide_after_timeout=hide_after_timeout,
            )

    elif severity == SEVERITY.WARNING:
        carb.log_warn(msg)
        if notify is True:
            notification_manager.post_notification(
                msg,
                status=notification_manager.NotificationStatus.WARNING,
                hide_after_timeout=hide_after_timeout,
            )

    elif severity == SEVERITY.ERROR:
        carb.log_error(msg)
        if notify is True:
            notification_manager.post_notification(
                msg,
                status=notification_manager.NotificationStatus.WARNING,
                hide_after_timeout=hide_after_timeout,
            )
