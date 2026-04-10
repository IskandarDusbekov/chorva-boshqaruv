import json
import tempfile
from calendar import monthrange
from datetime import timedelta
from pathlib import Path
from urllib import request as urlrequest
from smtplib import SMTPException
from urllib.error import URLError

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.dashboard.excel import build_general_report_workbook


class Command(BaseCommand):
    help = "Haftalik yoki oylik ferma hisobotini Excel qilib Telegram yoki emailga yuboradi."

    def add_arguments(self, parser):
        parser.add_argument("--period", choices=["weekly", "monthly"], default="weekly")
        parser.add_argument("--channel", choices=["telegram", "email", "gmail", "both"], default="both")

    def handle(self, *args, **options):
        channel = "email" if options["channel"] == "gmail" else options["channel"]
        today = timezone.now().date()
        if options["period"] == "monthly":
            first_day = today.replace(day=1)
            last_day = today.replace(day=monthrange(today.year, today.month)[1])
            date_from, date_to = first_day, last_day
        else:
            date_from, date_to = today - timedelta(days=6), today

        workbook = build_general_report_workbook(date_from=date_from, date_to=date_to)
        filename = f"ferma-hisobot-{options['period']}-{date_from}-{date_to}.xlsx"
        temp_path = Path(tempfile.gettempdir()) / filename
        workbook.save(temp_path)

        sent = []
        can_send_telegram = bool(settings.BOT_TOKEN and settings.REPORT_TELEGRAM_CHAT_ID)
        can_send_email = bool(settings.REPORT_EMAIL_TO)

        if channel in {"telegram", "both"} and can_send_telegram:
            self._send_telegram(temp_path, filename)
            sent.append("Telegram")
        if channel in {"email", "both"} and can_send_email:
            self._send_email(temp_path, filename, date_from, date_to)
            sent.append("email")
        if not sent:
            raise CommandError("Hisobot yuborish uchun REPORT_TELEGRAM_CHAT_ID yoki REPORT_EMAIL_TO sozlang.")

        self.stdout.write(self.style.SUCCESS(f"Hisobot yuborildi: {', '.join(sent)}"))

    def _send_telegram(self, path, filename):
        if not settings.BOT_TOKEN or not settings.REPORT_TELEGRAM_CHAT_ID:
            raise CommandError("Telegram yuborish uchun BOT_TOKEN va REPORT_TELEGRAM_CHAT_ID kerak.")

        boundary = "----BotGateReportBoundary"
        fields = {
            "chat_id": settings.REPORT_TELEGRAM_CHAT_ID,
            "caption": "Ferma avtomatik Excel hisoboti",
        }
        body = bytearray()
        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode())
        body.extend(b"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n")
        body.extend(path.read_bytes())
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        req = urlrequest.Request(
            f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendDocument",
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            raise CommandError(f"Telegramga ulanishda xatolik: {exc}") from exc
        if not data.get("ok"):
            raise CommandError(f"Telegram hisobotni qabul qilmadi: {data}")

    def _send_email(self, path, filename, date_from, date_to):
        if not settings.REPORT_EMAIL_TO:
            raise CommandError("Email yuborish uchun REPORT_EMAIL_TO kerak.")
        missing = []
        if not settings.EMAIL_HOST_USER:
            missing.append("EMAIL_HOST_USER")
        if not settings.EMAIL_HOST_PASSWORD:
            missing.append("EMAIL_HOST_PASSWORD")
        if missing:
            raise CommandError(f"Gmail/email yuborish uchun .env ichida {', '.join(missing)} kerak.")

        message = EmailMessage(
            subject=f"Ferma hisoboti: {date_from} - {date_to}",
            body="Ilovada ferma bo'yicha avtomatik Excel hisoboti yuborildi.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=settings.REPORT_EMAIL_TO,
        )
        message.attach(
            filename,
            path.read_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        try:
            message.send(fail_silently=False)
        except (OSError, SMTPException) as exc:
            raise CommandError(
                "Email yuborilmadi. Gmail ishlatish uchun .env ichida EMAIL_HOST_USER va "
                "EMAIL_HOST_PASSWORD app password bilan sozlangan bo'lishi kerak."
            ) from exc
