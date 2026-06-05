# Contributing

Thanks for improving Online BookStore.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

## Before Opening A Pull Request

Run:

```powershell
python manage.py check
python manage.py test store
```

## Notes

- Do not commit `.env`, virtual environments, or local databases.
- Keep migrations committed when models change.
- Keep UI changes responsive for mobile and dark theme.
- Put screenshots used by the README in `output/playwright/` as PNG files.
