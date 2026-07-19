"""Populate the database with initial content.

`seed_if_empty` runs automatically every time the app starts and only
inserts data the *first* time (when a table is empty), so it is always
safe to leave in place - it will never clobber content an administrator
has since edited through the dashboard.

`seed_all(force=True)` (used by `flask seed-db`) re-seeds the reference
lookup content but never touches modules that already contain admin-made
edits unless explicitly requested.
"""
from datetime import date

from werkzeug.security import generate_password_hash

from . import models
from .utils import list_images

db = models.db


def _seed_images(album_category: str, album_name: str, image_subfolder: str) -> None:
    """Create a gallery album from an existing static/images/<folder> if present."""
    if models.GalleryAlbum.query.filter_by(category=album_category).first():
        return

    filenames = list_images(image_subfolder)
    album = models.GalleryAlbum(name=album_name, category=album_category)
    db.session.add(album)
    db.session.flush()

    for order, filename in enumerate(filenames):
        db.session.add(models.GalleryImage(
            album_id=album.id,
            image=f"images/{image_subfolder}/{filename}",
            display_order=order,
        ))


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Admin@123"


def _seed_admin_user(app) -> None:
    if models.AdminUser.query.filter_by(role="admin").first():
        pass  # An admin already exists - never recreate or overwrite it.
    else:
        # Prefer an explicitly configured hash/username if the operator set
        # one, but this is entirely optional - if nothing is configured we
        # still create a working default account so the app is usable
        # immediately with zero setup.
        username = app.config.get("ADMIN_USERNAME") or DEFAULT_ADMIN_USERNAME
        password_hash = app.config.get("ADMIN_PASSWORD_HASH")

        if not password_hash:
            password_hash = generate_password_hash(DEFAULT_ADMIN_PASSWORD)
            app.logger.warning(
                "No admin account existed, so one was created automatically - "
                "username '%s', password '%s'. Log in and change this password "
                "immediately from the 'Change Password' page.",
                username, DEFAULT_ADMIN_PASSWORD,
            )
        else:
            app.logger.info("Seeded admin user '%s' from ADMIN_PASSWORD_HASH.", username)

        db.session.add(models.AdminUser(username=username, password_hash=password_hash, role="admin"))

    _seed_developer_user(app)


def _seed_developer_user(app) -> None:
    if models.AdminUser.query.filter_by(role="developer").first():
        return

    username = app.config.get("DEVELOPER_USERNAME", "developer")
    password_hash = app.config.get("DEVELOPER_PASSWORD_HASH")

    if password_hash:
        db.session.add(models.AdminUser(username=username, password_hash=password_hash, role="developer"))
        app.logger.info("Seeded developer user '%s' from DEVELOPER_PASSWORD_HASH.", username)
    else:
        app.logger.info(
            "No DEVELOPER_PASSWORD_HASH set - no developer account created. "
            "Run 'flask create-admin' and choose role 'developer' to create one."
        )


def _seed_home(app) -> None:
    if models.HomeContent.query.first():
        return

    db.session.add(models.HomeContent(
        id=1,
        hero_title="Vijayanagara College",
        hero_subtitle="Department of Computer Applications (BCA)",
        hero_cta_text="Contact Us",
        hero_cta_link="#contact",
        banner_image="",
        welcome_title="",
        welcome_message="",
    ))

    db.session.add_all([
        models.HomeFeature(
            title="Quality Education",
            description="Spacious, well-equipped classrooms providing the perfect "
                         "environment for learning.",
            image="images/class.jpg", display_order=0,
        ),
        models.HomeFeature(
            title="Modern Labs",
            description="State-of-the-art computer labs with high-speed internet "
                         "for practical sessions.",
            image="images/lab.jpg", display_order=1,
        ),
    ])

    db.session.add_all([
        models.HomeStat(label="Years of Excellence", value="15+", icon="fa-solid fa-award", display_order=0),
        models.HomeStat(label="Expert Faculty", value="16", icon="fa-solid fa-chalkboard-user", display_order=1),
        models.HomeStat(label="Students Enrolled", value="300+", icon="fa-solid fa-user-graduate", display_order=2),
        models.HomeStat(label="Placement Support", value="100%", icon="fa-solid fa-briefcase", display_order=3),
    ])


def _seed_faculty() -> None:
    if models.Faculty.query.first():
        return

    roster = [
        ("Sri N Mallikarjun Metri", "Chairman", "chairman.jpg", True),
        ("Dr. M. Prabhu Gouda", "Principal", "prabhugouda.jpg", True),
        ("Sri Shashank V", "Head of the Department", "hod.jpg", True),
        ("Dr. Ramangouda T", "Senior HOD", "senior.jpg", False),
        ("Smt. Shwetha B", "Lecturer", "swetha.jpg", False),
        ("Sri Upendra Kumar V", "Lecturer", "uppi.jpg", False),
        ("Smt. Soumya K", "Lecturer", "wd.jpg", False),
        ("Smt. Nagamma R", "Lecturer", "nagamma.jpg", False),
        ("Smt. Lakshmi R", "Lecturer", "ds.jpg", False),
        ("Smt. Tasneem B", "Lecturer", "tasneem.jpg", False),
        ("Miss Srujana S", "Lecturer", "srujana.jpg", False),
        ("Miss Deepa", "Lecturer", "deepa.jpg", False),
        ("Sri Shreekanth Akula", "Lecturer", "sri.jpg", False),
        ("Sri Md Aslam", "Lecturer", "aslam.jpg", False),
        ("Smt. Annapurna Lali", "Lecturer", "annapurna.jpg", False),
        ("Sri Rakesh U", "Lecturer", "rakesh.jpg", False),
        ("Sri Manjanna", "", "manjanna.jpg", False),
    ]

    for order, (name, designation, photo, leadership) in enumerate(roster):
        db.session.add(models.Faculty(
            name=name, department="BCA", designation=designation,
            photo=f"images/staff/{photo}", display_order=order, is_leadership=leadership,
        ))


def _seed_notices() -> None:
    if models.Notice.query.first():
        return

    db.session.add_all([
        models.Notice(
            title="Final Year Project Submission",
            description="All final year BCA students must submit their project "
                         "synopsis by Feb 5th to their respective guides.",
            publish_date=date(2026, 1, 28), pinned=True,
        ),
        models.Notice(
            title="Campus Recruitment Drive",
            description="Infosys and Wipro will be visiting the campus on Feb 20th. "
                         "Pre-placement talk at 10:00 AM in the Seminar Hall.",
            publish_date=date(2026, 1, 25),
        ),
        models.Notice(
            title="Internal Assessment 1",
            description="The first internal assessment for 2nd, 4th, and 6th "
                         "semesters will commence from Feb 10th. Check the notice "
                         "board for the detailed timetable.",
            publish_date=date(2026, 1, 20),
        ),
    ])


def _seed_about() -> None:
    if models.AboutContent.query.first():
        return

    db.session.add(models.AboutContent(
        id=1,
        vision="To be a premier institution nurturing globally competent computer "
               "applications professionals through quality education, research, "
               "and ethical values.",
        mission="To provide a strong foundation in computer applications through "
                "modern infrastructure, industry exposure, and dedicated mentorship, "
                "empowering students to excel in their careers.",
        principal_name="Dr. M. Prabhu Gouda",
        principal_message="It gives me immense pleasure to welcome you to the "
                           "Department of Computer Applications. We are committed to "
                           "providing an environment that fosters academic excellence, "
                           "innovation, and holistic development of every student.",
        principal_photo="images/staff/prabhugouda.jpg",
        about_text="Vijayanagara College's Department of Computer Applications (BCA) "
                    "offers a comprehensive undergraduate program combining strong "
                    "theoretical foundations with hands-on practical training in "
                    "modern computer labs, preparing students for careers in the "
                    "IT industry.",
        image1="images/building/opening.jpg",
        image2="images/class.jpg",
    ))


def _seed_contact() -> None:
    if models.ContactInfo.query.first():
        return

    db.session.add(models.ContactInfo(
        id=1,
        address="Vijayanagara College Campus, Bellary Road, Karnataka, India",
        phone1="", phone2="", email="", maps_link="",
    ))


def _seed_settings() -> None:
    if models.SiteSetting.query.first():
        return

    db.session.add(models.SiteSetting(
        id=1,
        college_name="Vijayanagara College - BCA Department",
        logo="", favicon="",
        footer_text="Designed by Pavan Kumar",
        copyright_text="\u00a9 2026 Vijayanagara College of Computer Applications.",
        developer_name="Pavan Kumar",
        developer_url="",
        show_developer_button=True,
        meta_description="Department of Computer Applications (BCA), Vijayanagara College - "
                          "quality education, modern labs, and dedicated faculty.",
        meta_keywords="VNC BCA, Vijayanagara College, Computer Applications, BCA Karnataka",
        og_image="",
    ))


def _seed_gallery() -> None:
    _seed_images("event", "Event Gallery", "event")
    _seed_images("etnic", "Ethnic Day", "etnic")
    _seed_images("building", "Campus & Building", "building")
    if not models.GalleryAlbum.query.filter_by(category="gallery").first():
        db.session.add(models.GalleryAlbum(name="Photo Gallery", category="gallery"))


def seed_if_empty(app) -> None:
    _seed_admin_user(app)
    _seed_home(app)
    _seed_faculty()
    _seed_notices()
    _seed_about()
    _seed_contact()
    _seed_settings()
    _seed_gallery()
    db.session.commit()


def seed_all(app, force: bool = False) -> None:
    """Used by the `flask seed-db` CLI command. Currently idempotent, same as
    seed_if_empty - kept as a distinct entry point so a future admin-facing
    "reset demo content" action has somewhere to hook in."""
    seed_if_empty(app)
