# BotGate Panel

Telegram-first secure management system where all users, including admins, access the platform only through a Telegram bot. The web panel is protected by temporary signed links, with role-based access for users, managers, and admins.

## Architecture

- `apps.accounts`: authentication, whitelist, Telegram bind, temporary access links, sessions, audit logs
- `apps.dashboard`: user entries, reports, admin and manager views, role-based panel pages
- `bot/`: aiogram bot bootstrap, keyboards, middleware, FSM states
- `config/settings/`: `base.py`, `dev.py`, `prod.py`

## MVP scope

- Admin whitelist management
- First login with username/password and Telegram binding
- Signed one-time access links for web panel
- Daily entry creation
- Basic reports and admin dashboard

## Admin UI

- Uzbekcha admin bo'limlari va sarlavhalar
- `Jazzmin` bilan soddaroq va tozaroq boshqaruv paneli

## Production

Production sozlamalari `.env` orqali boshqariladi. Serverda tracked fayllarni `nano` bilan o'zgartirmang, aks holda keyingi `git pull` conflict beradi.

- Namuna: `.env.example`
- To'liq qo'llanma: `docs/PRODUCTION.md`
- Production settings: `config.settings.prod`

## Suggested alternate names

- BotGate Panel
- TGMate Panel
- LinkGate Admin
- Secure Herd Panel
- TeleGate Dashboard
