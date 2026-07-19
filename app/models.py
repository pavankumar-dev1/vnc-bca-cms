"""SQLAlchemy models backing the CMS.

Every piece of editable website content lives in one of these tables so
that administrators can manage it from the admin dashboard without ever
touching a template or a Python file.
"""
from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _singleton_get(model):
    """Return the single settings-style row for a model, creating it if needed."""
    row = model.query.get(1)
    if row is None:
        row = model(id=1)
        db.session.add(row)
        db.session.commit()
    return row


# --------------------------------------------------------------------------
# Admin user
# --------------------------------------------------------------------------
class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin")  # "admin" or "developer"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --------------------------------------------------------------------------
# Home page
# --------------------------------------------------------------------------
class HomeContent(db.Model):
    __tablename__ = "home_content"

    id = db.Column(db.Integer, primary_key=True)
    hero_title = db.Column(db.String(200), default="")
    hero_subtitle = db.Column(db.String(300), default="")
    hero_cta_text = db.Column(db.String(80), default="")
    hero_cta_link = db.Column(db.String(300), default="")
    banner_image = db.Column(db.String(300), default="")
    welcome_title = db.Column(db.String(200), default="")
    welcome_message = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        return _singleton_get(HomeContent)


class HomeStat(db.Model):
    __tablename__ = "home_stats"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(40), nullable=False)
    icon = db.Column(db.String(60), default="fa-solid fa-star")
    display_order = db.Column(db.Integer, default=0)


class HomeFeature(db.Model):
    __tablename__ = "home_features"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    image = db.Column(db.String(300), default="")
    display_order = db.Column(db.Integer, default=0)


class HomeCTAButton(db.Model):
    __tablename__ = "home_cta_buttons"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(60), nullable=False)
    link = db.Column(db.String(300), nullable=False)
    display_order = db.Column(db.Integer, default=0)


# --------------------------------------------------------------------------
# Faculty
# --------------------------------------------------------------------------
class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(150), default="")
    designation = db.Column(db.String(150), default="")
    qualification = db.Column(db.String(200), default="")
    email = db.Column(db.String(200), default="")
    phone = db.Column(db.String(30), default="")
    photo = db.Column(db.String(300), default="")
    display_order = db.Column(db.Integer, default=0)
    is_leadership = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------
class Event(db.Model):
    __tablename__ = "events"

    STATUS_UPCOMING = "upcoming"
    STATUS_COMPLETED = "completed"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    event_date = db.Column(db.Date, default=date.today)
    venue = db.Column(db.String(200), default="")
    cover_image = db.Column(db.String(300), default="")
    status = db.Column(db.String(20), default=STATUS_UPCOMING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship(
        "EventImage", backref="event", cascade="all, delete-orphan",
        order_by="EventImage.display_order",
    )


class EventImage(db.Model):
    __tablename__ = "event_images"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    image = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(200), default="")
    display_order = db.Column(db.Integer, default=0)


# --------------------------------------------------------------------------
# Notices
# --------------------------------------------------------------------------
class Notice(db.Model):
    __tablename__ = "notices"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    pdf_path = db.Column(db.String(300), default="")
    publish_date = db.Column(db.Date, default=date.today)
    expiry_date = db.Column(db.Date, nullable=True)
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())


# --------------------------------------------------------------------------
# About college
# --------------------------------------------------------------------------
class AboutContent(db.Model):
    __tablename__ = "about_content"

    id = db.Column(db.Integer, primary_key=True)
    vision = db.Column(db.Text, default="")
    mission = db.Column(db.Text, default="")
    principal_name = db.Column(db.String(150), default="")
    principal_message = db.Column(db.Text, default="")
    principal_photo = db.Column(db.String(300), default="")
    about_text = db.Column(db.Text, default="")
    image1 = db.Column(db.String(300), default="")
    image2 = db.Column(db.String(300), default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        return _singleton_get(AboutContent)


# --------------------------------------------------------------------------
# Contact
# --------------------------------------------------------------------------
class ContactInfo(db.Model):
    __tablename__ = "contact_info"

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.Text, default="")
    phone1 = db.Column(db.String(30), default="")
    phone2 = db.Column(db.String(30), default="")
    email = db.Column(db.String(200), default="")
    maps_link = db.Column(db.String(500), default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        return _singleton_get(ContactInfo)


class SocialLink(db.Model):
    __tablename__ = "social_links"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(60), default="fa-solid fa-link")
    display_order = db.Column(db.Integer, default=0)


# --------------------------------------------------------------------------
# Gallery
# --------------------------------------------------------------------------
class GalleryAlbum(db.Model):
    __tablename__ = "gallery_albums"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), unique=True, nullable=False)
    display_order = db.Column(db.Integer, default=0)

    images = db.relationship(
        "GalleryImage", backref="album", cascade="all, delete-orphan",
        order_by="GalleryImage.display_order",
    )


class GalleryImage(db.Model):
    __tablename__ = "gallery_images"

    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey("gallery_albums.id"), nullable=False)
    image = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(200), default="")
    display_order = db.Column(db.Integer, default=0)


# --------------------------------------------------------------------------
# Site settings
# --------------------------------------------------------------------------
class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(200), default="VNC BCA")
    logo = db.Column(db.String(300), default="")
    favicon = db.Column(db.String(300), default="")
    footer_text = db.Column(db.String(300), default="")
    copyright_text = db.Column(db.String(300), default="")
    developer_name = db.Column(db.String(150), default="")
    developer_url = db.Column(db.String(500), default="")
    # Only a "developer" role account may flip this off - see routes/admin.py
    show_developer_button = db.Column(db.Boolean, default=True)
    meta_description = db.Column(db.String(300), default="")
    meta_keywords = db.Column(db.String(300), default="")
    og_image = db.Column(db.String(300), default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        return _singleton_get(SiteSetting)


# --------------------------------------------------------------------------
# Contact messages (unchanged behaviour, ported to the ORM)
# --------------------------------------------------------------------------
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db(app) -> None:
    """Attach SQLAlchemy to the app and make sure tables exist."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
