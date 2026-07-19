"""Small shared helpers used across routes."""
import os
import uuid
from functools import wraps

from flask import current_app, flash, redirect, session, url_for
from werkzeug.utils import secure_filename

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
DOC_EXTENSIONS = {"pdf"}


def login_required(view):
    """Redirect anonymous visitors to the login page before running `view`."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to continue.", "danger")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


def developer_required(view):
    """Restrict a view to the single developer-role account.

    Requires login_required (or an equivalent session check) to already
    have run - this only adds the role check on top of it.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to continue.", "danger")
            return redirect(url_for("admin.login"))
        if session.get("role") != "developer":
            flash("That page is reserved for the site developer account.", "danger")
            return redirect(url_for("admin.dashboard"))
        return view(*args, **kwargs)

    return wrapped


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def allowed_file(filename: str, allowed: set) -> bool:
    return bool(filename) and _extension(filename) in allowed


def save_upload(file_storage, subfolder: str, allowed: set = IMAGE_EXTENSIONS):
    """Validate and save an uploaded file under static/uploads/<subfolder>/.

    Returns the path stored in the DB, relative to the static folder
    (e.g. "uploads/faculty/ab12cd34.jpg"), or None if no file was given.
    Raises ValueError if the file's extension is not allowed.
    """
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not allowed_file(filename, allowed):
        raise ValueError("That file type is not allowed.")

    ext = _extension(filename)
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.static_folder, "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    destination = os.path.join(upload_dir, unique_name)
    file_storage.save(destination)

    if ext in IMAGE_EXTENSIONS:
        _try_compress_image(destination, ext)

    return f"uploads/{subfolder}/{unique_name}"


def _try_compress_image(path: str, ext: str, max_dimension: int = 1600, quality: int = 82) -> None:
    """Best-effort downsize/re-encode of an uploaded image to save space.

    No-ops silently if Pillow isn't installed or the file can't be
    processed - the original upload is left untouched either way, so
    this is purely an optional size optimization, never a hard
    requirement for uploads to work.
    """
    try:
        from PIL import Image
    except ImportError:
        return

    try:
        with Image.open(path) as img:
            img.thumbnail((max_dimension, max_dimension))
            save_kwargs = {"optimize": True}
            if ext in ("jpg", "jpeg"):
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                save_kwargs["quality"] = quality
            img.save(path, **save_kwargs)
    except Exception:
        pass  # Keep the original file if anything goes wrong


def delete_upload(relative_path: str) -> None:
    """Best-effort removal of a previously uploaded file.

    Only touches files inside static/uploads/ - never removes bundled
    theme assets that live directly under static/images/.
    """
    if not relative_path or not relative_path.startswith("uploads/"):
        return
    full_path = os.path.join(current_app.static_folder, relative_path)
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
    except OSError:
        current_app.logger.warning("Could not delete upload: %s", full_path)


def list_images(subfolder: str) -> list[str]:
    """Return image filenames inside static/images/<subfolder>, if present.

    Kept for backward compatibility with legacy static-folder image
    browsing; the CMS gallery module is now the primary source of truth.
    """
    folder = os.path.join(current_app.static_folder, "images", subfolder)
    if not os.path.isdir(folder):
        return []
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    return sorted(
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in allowed_ext
    )
