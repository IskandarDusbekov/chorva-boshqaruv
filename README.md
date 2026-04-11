# BotGate Panel

Telegram-first chorvachilik boshqaruv tizimi. Foydalanuvchi ham, admin ham avval Telegram bot orqali tekshiriladi, web panel esa faqat vaqtinchalik signed link yoki xavfsiz Mini App oqimi orqali ochiladi.

## Asosiy imkoniyatlar

- Telegram bot orqali kirish, kontakt tekshirish va bir martalik login ulash
- Whitelist asosidagi foydalanuvchi boshqaruvi
- Admin, manager va oddiy user rollari
- Sut boshqaruvi: ertalabki/kechki yozuv, sut narxi, kutilayotgan sut puli
- Moliya: kirim, chiqim, ichki hisob, tashqi hisob, kategoriya bo'yicha jamlanma
- Xodimlar: ishchi qo'shish, avans, ish haqi, oylik qoldiq va oylar bo'yicha hisobot
- Dashboard: progress, o'sish tahlili, oxirgi loglar va tez ko'rinadigan muhim kartalar
- Excel hisobotlar va davriy avtomatik yuborish

## Papka tuzilmasi

- `apps/accounts/`: auth, whitelist, telegram bind, access link, audit log
- `apps/dashboard/`: sut, moliya, ishchilar, hisobotlar, dashboard sahifalari
- `bot/`: aiogram dispatcher, tugmalar, state'lar va bot oqimlari
- `config/settings/`: umumiy, lokal va production sozlamalari
- `templates/`: web panel sahifalari
- `static/`: css, js, rasmlar

## Sozlamalar bo'linishi

- `config.settings.base`: hamma muhitlar uchun umumiy skelet
- `config.settings.dev`: lokal ishlash uchun qulay, `DEBUG=True`
- `config.settings.prod`: server uchun xavfsizroq, `DEBUG=False`, HTTPS va secure cookie

## Lokal ishga tushirish

1. Virtual environment yarating:

```bash
python -m venv venv
```

2. Aktiv qiling:

```bash
venv\Scripts\activate
```

3. Kutubxonalarni o'rnating:

```bash
pip install -r requirements.txt
```

4. `.env` yarating:

```bash
copy .env.example .env
```

5. Migratsiyalarni qo'llang:

```bash
python manage.py migrate
```

6. Admin yarating:

```bash
python manage.py createsuperuser
```

7. Serverni ishga tushiring:

```bash
python manage.py runserver
```

8. Botni alohida ishga tushiring:

```bash
python .\bot\main.py
```

## Muhim `.env` maydonlari

- `BOT_TOKEN`: Telegram bot tokeni
- `SITE_BASE_URL`: lokalda `http://127.0.0.1:8000`, productionda `https://domeningiz`
- `ADMIN_URL`: standart `/admin/` o'rniga yashirin admin yo'li
- `SECRET_KEY`: production uchun maxfiy kalit
- `POSTGRES_*`: production baza sozlamalari
- `REPORT_TELEGRAM_CHAT_ID`: avtomatik hisobot yuboriladigan chat
- `EMAIL_*`: email yuborish sozlamalari
- `DJANGO_LOG_LEVEL`: umumiy log darajasi, odatda `INFO`
- `DJANGO_ERROR_LOG_LEVEL`: xatolik log darajasi, odatda `ERROR`

## Auth oqimi

1. Admin user yoki whitelist yozuvini kiritadi.
2. Foydalanuvchi botda `/start` bosadi.
3. Kontakt yuboradi va whitelist bilan mosligi tekshiriladi.
4. Birinchi kirishda username/parol orqali tekshiriladi.
5. Telegram account user bilan bog'lanadi.
6. Keyingi kirishlarda bot userni avtomatik taniydi.
7. Web panelga faqat qisqa muddatli signed link bilan yoki xavfsiz Mini App orqali kiriladi.

## Production eslatma

Tracked kod fayllarni serverda `nano` bilan tahrirlamang. Productionga xos hamma sozlama faqat `.env` ichida tursin. Shunda keyingi `git pull` paytida conflict kam bo'ladi.

- Namuna: [`.env.example`](.env.example)
- Qo'llanma: [`docs/PRODUCTION.md`](docs/PRODUCTION.md)
- Production settings: [`config/settings/prod.py`](config/settings/prod.py)

## Asosiy kommandalar

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py send_periodic_report --period weekly --channel both
python manage.py send_periodic_report --period monthly --channel both
```

## Texnik eslatma

- Lokal uchun SQLite qulay
- Production uchun PostgreSQL tavsiya qilinadi
- Mini App tugmasi faqat `https://` bo'lsa chiqadi, chunki Telegram oddiy `http://` ni qabul qilmaydi
- Default sut puli darhol ichki hisobga tushmaydi, avval pending bo'ladi, keyin qabul qilinganda ichki yoki tashqi hisobga o'tadi
- `logs/app.log` ichida umumiy Django va ilova loglari yoziladi
- `logs/error.log` ichida xatoliklar alohida yoziladi
