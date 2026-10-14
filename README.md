# Login System
This is a Django project for signup, login, Django admin, and profile CRUD operations. It uses function-based views, templates, SQLite, and Django's built-in authentication.

## Steps to run

From the project folder, create and activate the virtual environment, then install the requirements:

```bash
python3 -m venv DjangoAssignment
source DjangoAssignment/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate it with `DjangoAssignment\Scripts\Activate.ps1`. On Windows Command Prompt, use `DjangoAssignment\Scripts\activate.bat`.

Create or update the local SQLite database and start Django:

```bash
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser. The checked-in migration creates the `UserDetails` table. 


## Pages

| URL | What it does |
| --- | --- |
| `/hello/` | Returns `Hello, world!` |
| `/signup/` | Signup form; successful signup redirects to login |
| `/login/` | Email and password login; shows the signup confirmation after signup |
| `/success/` | Login success page; requires a signed-in user |
| `/admin/` | Django admin |

To create an admin account, run this command and follow the prompts:

```bash
python manage.py createsuperuser
```

Then visit <http://127.0.0.1:8000/admin/>. Admin accounts use Django's auth system and are separate from accounts created through signup.

## Profile API

The API is for staff accounts. Sign in through the login page or the Postman login request first. Responses include profile names and email addresses, not passwords. Signup is the create operation. The single-profile route looks up by email.

| Method and URL | What it does | Success / common errors |
| --- | --- | --- |
| `GET /api/users/` | List all profiles | `200`; `401` if signed out, `403` if not staff |
| `GET /api/users/<email>/` | Get one profile | `200`; `404` if missing |
| `PUT` or `PATCH /api/users/<email>/update/` | Update `name` and/or `email` using a JSON object | `200`; `400` invalid body, `404` missing, `409` duplicate |
| `DELETE /api/users/<email>/delete/` | Delete a profile and its linked auth account | `204`; `404` missing |

Unsupported methods return `405`. Django CSRF protection stays enabled for changes; an invalid or missing CSRF token returns `403`.

## Screenshots

The `screenshots/templates/` folder has captures of the signup form, signup confirmation, successful login, and admin page. The `screenshots/postman/` folder has Postman request and response captures, including CRUD examples.