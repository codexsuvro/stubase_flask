from datetime import UTC, datetime, timedelta
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import make_msgid
import smtplib
import ssl

from sqlalchemy import and_, or_, select

from app.extensions import db
from app.notifications.models import (
    Notification,
    NotificationDelivery,
)


MAX_DELIVERY_ATTEMPTS = 5
DELIVERY_LOCK_SECONDS = 300
SMTP_TIMEOUT_SECONDS = 20


class NotificationEmailConfigurationError(Exception):
    pass


class NotificationEmailDeliveryError(Exception):
    pass


class NotificationEmailPermanentError(Exception):
    pass


def _now():
    return datetime.now(UTC)


def _mail_settings(config):
    server = config.get("MAIL_SERVER")
    from_address = config.get("MAIL_FROM_ADDRESS")
    if not server or not from_address:
        raise NotificationEmailConfigurationError(
            "MAIL_SERVER and MAIL_FROM_ADDRESS must be configured "
            "before dispatching notification emails."
        )

    try:
        port = int(config.get("MAIL_PORT", 587))
    except (TypeError, ValueError) as exc:
        raise NotificationEmailConfigurationError(
            "MAIL_PORT must be a valid TCP port."
        ) from exc

    if not 1 <= port <= 65535:
        raise NotificationEmailConfigurationError(
            "MAIL_PORT must be between 1 and 65535."
        )

    username = config.get("MAIL_USERNAME")
    password = config.get("MAIL_PASSWORD")
    if bool(username) != bool(password):
        raise NotificationEmailConfigurationError(
            "MAIL_USERNAME and MAIL_PASSWORD must be configured together."
        )

    use_tls = config.get("MAIL_USE_TLS", True)
    if isinstance(use_tls, str):
        normalized_tls = use_tls.strip().lower()
        if normalized_tls not in {
            "1",
            "true",
            "yes",
            "on",
            "0",
            "false",
            "no",
            "off",
        }:
            raise NotificationEmailConfigurationError(
                "MAIL_USE_TLS must be a boolean value."
            )
        use_tls = normalized_tls in {"1", "true", "yes", "on"}

    from_name = config.get("MAIL_FROM_NAME", "StuBase")
    try:
        from_header = Address(
            display_name=from_name,
            addr_spec=from_address,
        )
    except ValueError as exc:
        raise NotificationEmailConfigurationError(
            "MAIL_FROM_ADDRESS or MAIL_FROM_NAME is invalid."
        ) from exc

    return {
        "server": server,
        "port": port,
        "from_address": from_address,
        "from_header": from_header,
        "username": username,
        "password": password,
        "use_tls": bool(use_tls),
    }


def _send_email(delivery_id, notification, recipient_email, settings):
    try:
        recipient_header = Address(addr_spec=recipient_email)
    except ValueError as exc:
        raise NotificationEmailPermanentError(
            "The recipient email address is invalid."
        ) from exc

    try:
        sender_domain = settings["from_address"].rsplit("@", 1)[1]
        message = EmailMessage()
        message["From"] = settings["from_header"]
        message["To"] = recipient_header
        message["Subject"] = notification.title
        message["Message-ID"] = make_msgid(
            idstring=str(delivery_id),
            domain=sender_domain,
        )
        message.set_content(notification.message)

        with smtplib.SMTP(
            settings["server"],
            settings["port"],
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as smtp:
            smtp.ehlo()
            if settings["use_tls"]:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if settings["username"]:
                smtp.login(
                    settings["username"],
                    settings["password"],
                )
            refused = smtp.send_message(message)
            if refused:
                reply = next(iter(refused.values()))
                if reply[0] >= 500:
                    raise NotificationEmailPermanentError(
                        "The email server permanently refused the recipient."
                    )
                raise NotificationEmailDeliveryError(
                    "The email server refused the notification recipient."
                )
    except (OSError, smtplib.SMTPException, ValueError, IndexError) as exc:
        raise NotificationEmailDeliveryError(
            f"Email delivery failed: {exc}"
        ) from exc


def _claim_delivery(now):
    pending = and_(
        NotificationDelivery.status == "PENDING",
        NotificationDelivery.next_attempt_at <= now,
    )
    expired_processing = and_(
        NotificationDelivery.status == "PROCESSING",
        NotificationDelivery.locked_until <= now,
    )
    statement = (
        select(NotificationDelivery)
        .where(
            or_(pending, expired_processing),
        )
        .order_by(
            NotificationDelivery.next_attempt_at.asc(),
            NotificationDelivery.created_at.asc(),
            NotificationDelivery.id.asc(),
        )
        .limit(1)
        .with_for_update(skip_locked=True)
    )

    delivery = db.session.scalar(statement)
    if delivery is None:
        db.session.rollback()
        return None, False

    if delivery.attempt_count >= MAX_DELIVERY_ATTEMPTS:
        delivery.status = "FAILED"
        delivery.locked_until = None
        if not delivery.last_error:
            delivery.last_error = (
                "The delivery lease expired after the maximum attempts."
            )
        db.session.commit()
        return None, True

    delivery.status = "PROCESSING"
    delivery.attempt_count += 1
    delivery.locked_until = now + timedelta(
        seconds=DELIVERY_LOCK_SECONDS
    )
    delivery.last_error = None
    delivery_id = delivery.id
    db.session.commit()
    return delivery_id, False


def _has_due_deliveries(now):
    pending = and_(
        NotificationDelivery.status == "PENDING",
        NotificationDelivery.next_attempt_at <= now,
    )
    expired_processing = and_(
        NotificationDelivery.status == "PROCESSING",
        NotificationDelivery.locked_until <= now,
    )
    statement = (
        select(NotificationDelivery.id)
        .where(or_(pending, expired_processing))
        .limit(1)
    )
    return db.session.scalar(statement) is not None


def _finish_delivery(delivery_id, error=None):
    delivery = db.session.get(NotificationDelivery, delivery_id)
    if delivery is None:
        raise RuntimeError(
            "A claimed notification delivery no longer exists."
        )

    now = _now()
    delivery.locked_until = None
    if error is None:
        delivery.status = "SENT"
        delivery.sent_at = now
        delivery.next_attempt_at = now
        delivery.last_error = None
    elif delivery.attempt_count >= MAX_DELIVERY_ATTEMPTS:
        delivery.status = "FAILED"
        delivery.last_error = str(error)[:500]
    else:
        delay_seconds = min(
            60 * (2 ** (delivery.attempt_count - 1)),
            3600,
        )
        delivery.status = "PENDING"
        delivery.next_attempt_at = now + timedelta(
            seconds=delay_seconds
        )
        delivery.last_error = str(error)[:500]

    db.session.commit()


def _fail_delivery(delivery_id, error):
    delivery = db.session.get(NotificationDelivery, delivery_id)
    if delivery is None:
        raise RuntimeError(
            "A claimed notification delivery no longer exists."
        )

    delivery.status = "FAILED"
    delivery.locked_until = None
    delivery.last_error = str(error)[:500]
    db.session.commit()


def dispatch_pending_email_deliveries(limit=50):
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500.")

    from flask import current_app

    counts = {"sent": 0, "retrying": 0, "failed": 0}
    if not _has_due_deliveries(_now()):
        return counts

    settings = _mail_settings(current_app.config)
    processed = 0

    while processed < limit:
        delivery_id, exhausted = _claim_delivery(_now())
        if exhausted:
            counts["failed"] += 1
            processed += 1
            continue
        if delivery_id is None:
            break

        delivery = db.session.get(
            NotificationDelivery,
            delivery_id,
        )
        if delivery is None:
            raise RuntimeError(
                "A claimed notification delivery could not be loaded."
            )

        notification = db.session.get(
            Notification,
            delivery.notification_id,
        )
        recipient = notification.recipient if notification else None
        if (
            notification is None
            or recipient is None
            or not recipient.is_active
            or not recipient.is_verified
        ):
            _fail_delivery(
                delivery.id,
                "The recipient account is unavailable for email delivery.",
            )
            counts["failed"] += 1
            processed += 1
            continue

        try:
            _send_email(
                delivery.id,
                notification,
                recipient.email,
                settings,
            )
        except NotificationEmailPermanentError as exc:
            _fail_delivery(delivery.id, exc)
            counts["failed"] += 1
            processed += 1
        except NotificationEmailDeliveryError as exc:
            _finish_delivery(delivery.id, error=exc)
            processed += 1
            refreshed = db.session.get(
                NotificationDelivery,
                delivery.id,
            )
            if refreshed is not None and refreshed.status == "FAILED":
                counts["failed"] += 1
            else:
                counts["retrying"] += 1
        else:
            _finish_delivery(delivery.id)
            counts["sent"] += 1
            processed += 1

    return counts
