"""JSON API for resume upload and AI feedback (consumed by the React pages)."""
from accounts.api import is_profile_complete
from functools import wraps
from pathlib import Path

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ResumeUploadForm, ResumeFieldsForm
from .models import Resume
from .services import ResumeFeedbackError, get_resume_feedback, ResumeParseError, parse_resume_fields


def api_login_required(view):
    """401 JSON instead of a login redirect."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        if not is_profile_complete(request.user):
            return JsonResponse({"detail": "Complete your profile first."}, status=403)
        return view(request, *args, **kwargs)

    return wrapper


def serialize(resume):
    return {
        "id": resume.id,
        "name": Path(resume.file.name).name,
        "url": resume.file.url,
        "uploaded_at": resume.uploaded_at.isoformat(),
        "is_default": resume.is_default,
        "skills": resume.skills,
        "experience": resume.experience,
        "education": resume.education,
    }


@api_login_required
@require_POST
def update_resume_fields(request, resume_id):
    resume = Resume.objects.filter(
        id=resume_id,
        owner=request.user,
    ).first()

    if resume is None:
        return JsonResponse(
            {"detail": "Not found."},
            status=404,
        )

    form = ResumeFieldsForm(
        request.POST,
        instance=resume,
    )

    if not form.is_valid():
        return JsonResponse(
            {
                "detail": "Resume fields could not be saved.",
                "errors": {
                    field: list(errors)
                    for field, errors in form.errors.items()
                },
            },
            status=400,
        )

    updated_resume = form.save()

    return JsonResponse(
        serialize(updated_resume),
        status=200,
    )


@api_login_required
@require_POST
def parse_resume(request, resume_id):
    resume = Resume.objects.filter(
        id=resume_id,
        owner=request.user,
    ).first()

    if resume is None:
        return JsonResponse(
            {"detail": "Not found."},
            status=404,
        )

    try:
        fields = parse_resume_fields(resume)
    except ResumeParseError:
        return JsonResponse(
            {
                "detail": (
                    "Resume parsing is unavailable right now. "
                    "Please try again later."
                )
            },
            status=503,
        )

    resume.skills = fields["skills"]
    resume.experience = fields["experience"]
    resume.education = fields["education"]
    resume.save(
        update_fields=[
            "skills",
            "experience",
            "education",
        ]
    )

    return JsonResponse(
        serialize(resume),
        status=200,
    )


@api_login_required
@require_http_methods(["GET", "POST"])
def resumes(request):
    """GET: the user's resumes. POST (multipart `file`): upload one."""
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse(
                {
                    "detail": "Upload failed.",
                    "errors": {f: list(e) for f, e in form.errors.items()},
                },
                status=400,
            )
        resume = form.save(commit=False)
        resume.owner = request.user  # never trust the client for ownership
        resume.is_default = not request.user.resumes.exists()
        resume.save()
        return JsonResponse(serialize(resume), status=201)

    items = request.user.resumes.order_by("-uploaded_at")
    return JsonResponse({"results": [serialize(r) for r in items]})


@api_login_required
@require_POST
def set_default_resume(request, resume_id):
    resume = Resume.objects.filter(
        id=resume_id,
        owner=request.user,
    ).first()

    if resume is None:
        return JsonResponse(
            {"detail": "Not found."},
            status=404,
        )

    with transaction.atomic():
        request.user.resumes.filter(
            is_default=True,
        ).update(
            is_default=False,
        )

        resume.is_default = True
        resume.save(update_fields=["is_default"])

    return JsonResponse(
        serialize(resume),
        status=200,
    )


@api_login_required
@require_http_methods(["DELETE"])
def delete_resume(request, resume_id):
    """
    Deletes one resume owned by the logged-in user
    """
    resume = Resume.objects.filter(
        id=resume_id,
        owner=request.user,
    ).first()

    if resume is None:
        return JsonResponse(
            {"detail": "Not found."},
            status=404,
        )

    file_name = resume.file.name
    storage = resume.file.storage
    was_default = resume.is_default

    with transaction.atomic():
        resume.delete()

        if was_default:
            next_resume = request.user.resumes.order_by(
                "-uploaded_at",
                "-id",
            ).first()

            if next_resume is not None:
                next_resume.is_default = True
                next_resume.save(update_fields=["is_default"])

    def delete_file():
        storage.delete(file_name)

    transaction.on_commit(delete_file)

    return HttpResponse(status=204)


@api_login_required
@require_POST
def replace_resume(request, resume_id):
    """
    Replaces one resume owned by the logged-in user
    """
    resume = Resume.objects.filter(
        id=resume_id,
        owner=request.user,
    ).first()

    if resume is None:
        return JsonResponse(
            {"detail": "Not found."},
            status=404,
        )
    replacement_file = request.FILES.get("file")

    if replacement_file is None:
        return JsonResponse(
            {
                "detail": "Replacement failed.",
                "errors": {
                    "file": ["Please choose a resume file."],
                },
            },
            status=400,
        )
    old_file_name = resume.file.name
    storage = resume.file.storage

    form = ResumeUploadForm(
        request.POST,
        request.FILES,
        instance=resume,
    )

    if not form.is_valid():
        return JsonResponse(
            {
                "detail": "Replacement failed.",
                "errors": {
                    field: list(errors)
                    for field, errors in form.errors.items()
                },
            },
            status=400,
        )

    updated_resume = form.save()

    if old_file_name != updated_resume.file.name:
        def delete_old_file():
            storage.delete(old_file_name)
        transaction.on_commit(delete_old_file)
    return JsonResponse(
        serialize(updated_resume),
        status=200,
    )


@api_login_required
@require_POST
def resume_feedback(request, resume_id):
    """Generate AI feedback for one of the caller's resumes."""
    resume = Resume.objects.filter(id=resume_id, owner=request.user).first()
    if resume is None:
        return JsonResponse({"detail": "Not found."}, status=404)
    try:
        feedback = get_resume_feedback(resume)
    except ResumeFeedbackError:
        return JsonResponse(
            {"detail": "AI feedback is unavailable right now. Please try again later."},
            status=503,
        )
    # Service returns numbered plain text, one suggestion per line.
    suggestions = [ln.strip() for ln in feedback.splitlines() if ln.strip()]
    return JsonResponse(
        {"resume": serialize(resume), "feedback": feedback, "suggestions": suggestions}
    )
