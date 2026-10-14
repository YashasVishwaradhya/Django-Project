"""Function-based views for signup, login, and profile CRUD."""
import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import LoginForm, SignupForm
from .models import UserDetails

User = get_user_model()


def hello_world(request):
    return HttpResponse("Hello, world!")


def signup(request):
    # Bind submitted values to the form and stop if any field is invalid.
    form = SignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"].strip()
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        # Check both profile and auth records because email is stored in both.
        if UserDetails.objects.filter(username__iexact=name).exists():
            form.add_error("name", "That username is already taken.")
        elif User.objects.filter(email__iexact=email).exists() or UserDetails.objects.filter(
            email__iexact=email
        ).exists():
            form.add_error("email", "An account with this email already exists.")
        else:
            candidate_user = User(username=email, email=email)
            try:
                validate_password(password, user=candidate_user)
            except ValidationError as error:
                form.add_error("password", error)
            else:
                try:
                    # Save both records together so a partial signup is not left behind.
                    with transaction.atomic():
                        auth_user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=password,
                        )
                        UserDetails.objects.create(
                            username=name,
                            email=email,
                            related_user=auth_user,
                        )
                except IntegrityError:
                    form.add_error(
                        None,
                        "An account with that name or email already exists. Please try again.",
                    )
                else:
                    # Show confirmation on login while keeping the required redirect.
                    return redirect(f"{reverse('login')}?registered=1")

    return render(request, "Loginify/signup.html", {"form": form})


def login_view(request):
    # Validate the email and password before checking the linked Django account.
    form = LoginForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]
        auth_user_record = User.objects.filter(email__iexact=email).first()
        authenticated_user = None
        if auth_user_record is not None:
            authenticated_user = authenticate(
                request,
                username=auth_user_record.get_username(),
                password=password,
            )

        if authenticated_user is None:
            form.add_error(None, "The email or password is incorrect.")
        else:
            # Django checks the stored password hash and starts the session.
            login(request, authenticated_user)
            messages.success(request, "You are now signed in.")
            return redirect("success")

    context = {"form": form, "show_confirmation": request.GET.get("registered") == "1"}
    return render(request, "Loginify/login.html", context)


@login_required
def success(request):
    return render(request, "Loginify/success.html")


def api_methods(*allowed_methods):
    """Return a JSON 405 response for unsupported API methods."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method not in allowed_methods:
                response = JsonResponse(
                    {
                        "error": "Method not allowed.",
                        "allowed_methods": list(allowed_methods),
                    },
                    status=405,
                )
                response["Allow"] = ", ".join(allowed_methods)
                return response
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def staff_api_required(view):
    """Keep private profile data and account changes available to staff only."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        # Check sign-in first, then make sure the account is staff.
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication is required."}, status=401)
        if not request.user.is_staff:
            return JsonResponse({"error": "Staff access is required."}, status=403)
        return view(request, *args, **kwargs)

    return wrapped


def profile_json(profile):
    """Expose public profile fields only; never serialize credentials."""
    return {"username": profile.username, "email": profile.email}


@api_methods("GET")
@staff_api_required
def get_all_user_details(request):
    profiles = UserDetails.objects.order_by("username")
    return JsonResponse({"users": [profile_json(profile) for profile in profiles]})


@api_methods("GET")
@staff_api_required
def get_user_by_email(request, email):
    profile = UserDetails.objects.filter(email__iexact=email).first()
    if profile is None:
        return JsonResponse({"error": "User not found."}, status=404)
    return JsonResponse({"user": profile_json(profile)})


def read_json_object(request):
    # Reject requests that are not valid JSON objects before updating a profile.
    if request.content_type != "application/json":
        return None, "Send a JSON request body with Content-Type: application/json."
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "The request body is not valid JSON."
    if not isinstance(payload, dict):
        return None, "The JSON body must be an object."
    return payload, None


@api_methods("PUT", "PATCH")
@staff_api_required
def update_user_details(request, email):
    # Read and validate the JSON fields before making any database changes.
    payload, error = read_json_object(request)
    if error:
        return JsonResponse({"error": error}, status=400)
    allowed_fields = {"name", "email"}
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        return JsonResponse(
            {"error": "Only name and email can be updated."}, status=400
        )
    if not payload:
        return JsonResponse({"error": "Provide a name or email to update."}, status=400)

    profile = UserDetails.objects.filter(email__iexact=email).first()
    if profile is None:
        return JsonResponse({"error": "User not found."}, status=404)
    new_name = profile.username
    new_email = profile.email
    if "name" in payload:
        if not isinstance(payload["name"], str) or not payload["name"].strip():
            return JsonResponse({"error": "Name must be a non-empty string."}, status=400)
        new_name = payload["name"].strip()
        if len(new_name) > 50:
            return JsonResponse({"error": "Name must be 50 characters or fewer."}, status=400)
        if UserDetails.objects.filter(username__iexact=new_name).exclude(
            pk=profile.pk
        ).exists():
            return JsonResponse({"error": "That username is already taken."}, status=409)

    if "email" in payload:
        if not isinstance(payload["email"], str):
            return JsonResponse({"error": "Email must be a string."}, status=400)
        new_email = payload["email"].strip().lower()
        if len(new_email) > 254:
            return JsonResponse({"error": "Email must be 254 characters or fewer."}, status=400)
        try:
            validate_email(new_email)
        except ValidationError:
            return JsonResponse({"error": "Enter a valid email address."}, status=400)
        if UserDetails.objects.filter(email__iexact=new_email).exclude(
            pk=profile.pk
        ).exists() or User.objects.filter(email__iexact=new_email).exclude(
            pk=profile.related_user_id
        ).exists() or User.objects.filter(username__iexact=new_email).exclude(
            pk=profile.related_user_id
        ).exists():
            return JsonResponse({"error": "An account with this email already exists."}, status=409)

    try:
        # Update the profile and its login account together to keep their emails in sync.
        with transaction.atomic():
            if new_name != profile.username:
                UserDetails.objects.filter(pk=profile.pk).update(username=new_name)
                # Keep the model instance's primary key in sync for the later reload.
                profile.username = new_name
            if new_email != profile.email:
                UserDetails.objects.filter(pk=profile.pk).update(email=new_email)
                profile.related_user.email = new_email
                profile.related_user.username = new_email
                profile.related_user.save(update_fields=("email", "username"))
    except IntegrityError:
        return JsonResponse(
            {"error": "That name or email is already in use."}, status=409
        )

    profile.refresh_from_db()
    return JsonResponse({"user": profile_json(profile)})


@api_methods("DELETE")
@staff_api_required
def delete_user_by_email(request, email):
    profile = UserDetails.objects.filter(email__iexact=email).first()
    if profile is None:
        return JsonResponse({"error": "User not found."}, status=404)
    # Deleting the auth user cascades to its linked profile.
    profile.related_user.delete()
    return HttpResponse(status=204)


def csrf_failure(request, reason=""):
    if request.path.startswith("/api/"):
        return JsonResponse(
            {"error": "CSRF verification failed. Fetch the login page and send its token."},
            status=403,
        )
    return render(
        request,
        "Loginify/login.html",
        {"form": LoginForm(), "csrf_error": True},
        status=403,
    )
