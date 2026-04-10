# Production tayyorgarlik

Bu loyiha serverda `git pull` bilan yangilanadi. Shuning uchun qoida oddiy:

- Kod va umumiy sozlama repoda turadi.
- Token, parol, domain, database paroli faqat serverdagi `.env` ichida turadi.
- Serverda `nano` bilan tracked fayllarni o'zgartirmang: `settings.py`, `prod.py`, `urls.py`, template yoki Python fayllarni serverda qo'lda tahrirlash keyingi `git pull`da conflict beradi.

## Serverdagi bir martalik sozlash

1. Repodan kodni oling.
2. `.env.example`dan nusxa qiling:

```bash
cp .env.example .env
chmod 600 .env
```

3. Faqat `.env`ni to'ldiring.
4. `ADMIN_URL`ni oddiy `/admin/` qilmay, taxmin qilish qiyinroq path qiling.
5. Production commandlarda settingsni aniq ko'rsating:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
python manage.py collectstatic --noinput
```

## Git pull conflict bo'lmasligi uchun

Serverda hech qachon tracked fayllarni o'zgartirmang. Tekshirish:

```bash
git status --short
```

Toza serverda bu bo'sh chiqishi kerak. Agar `.env` ko'rinsa, demak `.gitignore` noto'g'ri ishlayapti yoki fayl avval commit qilingan.

Yangilash tartibi:

```bash
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart chorva-web
sudo systemctl restart chorva-bot
```

## Gmail yuborish

`EMAIL_HOST_PASSWORD` oddiy Gmail parol emas. Google Account ichidan `App password` yarating va `.env`ga qo'ying.

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=google-app-password
REPORT_EMAIL_TO=admin@example.com
```

## Avtomatik Excel backup hisobot

Haftalik:

```bash
python manage.py send_periodic_report --period weekly --channel both
```

Oylik:

```bash
python manage.py send_periodic_report --period monthly --channel both
```

Buni cron yoki systemd timerga qo'ying. Excel ichida dashboard, sut, moliya, xodimlar, ishchilar hisobi, barcha amallar va kunlik jamlanma bor.

## Eng ko'p uchraydigan hujumlar

- Token o'g'irlanishi: `.env`, bot token, email app password yoki DB paroli oshkor bo'lishi.
- Brute force: username/parolni qayta-qayta urinish.
- Session hijack: cookie yoki temporary linkni o'g'irlash.
- Replay attack: eski signed link yoki Telegram WebApp `initData`ni qayta ishlatish.
- CSRF: login bo'lgan user nomidan so'rov yuborish.
- XSS: izoh/note maydoniga script kiritish.
- SQL injection: raw SQL yoki string concat query ishlatilsa.
- SSRF/file upload: tashqi URL/file bilan ishlaydigan joylar qo'shilsa.
- Admin panelga public brute force: `/admin/` ochiq qolsa.
- Dependency attack: eski paketlarda vulnerability bo'lishi.

## Minimal production himoya checklist

- `DEBUG=False`.
- `SECRET_KEY` kuchli va server `.env`da.
- `ALLOWED_HOSTS` faqat real domainlar.
- `CSRF_TRUSTED_ORIGINS` faqat HTTPS domainlar.
- HTTPS majburiy.
- Secure cookie yoqilgan.
- PostgreSQL ishlatiladi.
- `.env` commit qilinmaydi.
- Bot token leak bo'lsa BotFather orqali darhol rotate qilinadi.
- Server firewall: faqat 80/443 va SSH kerakli IPga.
- `ADMIN_URL` maxfiyroq path bo'lsin, masalan `botgate-admin-9284/`.
- Database port public internetga ochilmaydi.
- Backup Excel hisobot haftalik/oylik yuboriladi.
