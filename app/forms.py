"""Flask-WTF forms.

Every admin form here gives us CSRF protection, server-side validation,
and (for uploads) file-type/size checks, closing the gaps of hand-rolled
`request.form[...]` / `request.files[...]` access.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional, URL

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp"]
DOC_EXTENSIONS = ["pdf"]
IMAGE_MESSAGE = "Images only (jpg, jpeg, png, gif, webp)."
PDF_MESSAGE = "PDF files only."


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=200)])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=200)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired()])


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=4000)])


class DeleteForm(FlaskForm):
    """Empty form used purely to carry a CSRF token on delete buttons."""
    pass


# --------------------------------------------------------------------------
# Home management
# --------------------------------------------------------------------------
class HomeContentForm(FlaskForm):
    hero_title = StringField("Hero Title", validators=[DataRequired(), Length(max=200)])
    hero_subtitle = StringField("Hero Subtitle", validators=[Optional(), Length(max=300)])
    hero_cta_text = StringField("Hero Button Text", validators=[Optional(), Length(max=80)])
    hero_cta_link = StringField("Hero Button Link", validators=[Optional(), Length(max=300)])
    banner_image = FileField("Banner Image", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    welcome_title = StringField("Welcome Title", validators=[Optional(), Length(max=200)])
    welcome_message = TextAreaField("Welcome Message", validators=[Optional(), Length(max=4000)])


class HomeStatForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=100)])
    value = StringField("Value", validators=[DataRequired(), Length(max=40)])
    icon = StringField("Icon (Font Awesome class)", validators=[Optional(), Length(max=60)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


class HomeFeatureForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    image = FileField("Image", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


class HomeCTAForm(FlaskForm):
    text = StringField("Button Text", validators=[DataRequired(), Length(max=60)])
    link = StringField("Button Link", validators=[DataRequired(), Length(max=300)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


# --------------------------------------------------------------------------
# Faculty
# --------------------------------------------------------------------------
class FacultyForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=150)])
    department = StringField("Department", validators=[Optional(), Length(max=150)])
    designation = StringField("Designation", validators=[Optional(), Length(max=150)])
    qualification = StringField("Qualification", validators=[Optional(), Length(max=200)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=200)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    photo = FileField("Photo", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])
    is_leadership = BooleanField("Show in Leadership section on Home page")


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------
class EventForm(FlaskForm):
    title = StringField("Event Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=4000)])
    event_date = DateField("Event Date", validators=[DataRequired()])
    venue = StringField("Venue", validators=[Optional(), Length(max=200)])
    cover_image = FileField("Cover Image", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    status = SelectField(
        "Status",
        choices=[("upcoming", "Upcoming"), ("completed", "Completed")],
        validators=[DataRequired()],
    )


class EventImageForm(FlaskForm):
    image = FileField("Gallery Image", validators=[DataRequired(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    caption = StringField("Caption", validators=[Optional(), Length(max=200)])


# --------------------------------------------------------------------------
# Notices
# --------------------------------------------------------------------------
class NoticeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=4000)])
    pdf_attachment = FileField("PDF Attachment", validators=[Optional(), FileAllowed(DOC_EXTENSIONS, PDF_MESSAGE)])
    publish_date = DateField("Publish Date", validators=[DataRequired()])
    expiry_date = DateField("Expiry Date", validators=[Optional()])
    pinned = BooleanField("Pin this notice")


# --------------------------------------------------------------------------
# About college
# --------------------------------------------------------------------------
class AboutContentForm(FlaskForm):
    vision = TextAreaField("Vision", validators=[Optional(), Length(max=3000)])
    mission = TextAreaField("Mission", validators=[Optional(), Length(max=3000)])
    principal_name = StringField("Principal's Name", validators=[Optional(), Length(max=150)])
    principal_message = TextAreaField("Principal's Message", validators=[Optional(), Length(max=4000)])
    principal_photo = FileField("Principal's Photo", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    about_text = TextAreaField("About Text", validators=[Optional(), Length(max=6000)])
    image1 = FileField("Image 1", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    image2 = FileField("Image 2", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])


# --------------------------------------------------------------------------
# Contact
# --------------------------------------------------------------------------
class ContactInfoForm(FlaskForm):
    address = TextAreaField("Address", validators=[Optional(), Length(max=1000)])
    phone1 = StringField("Primary Phone", validators=[Optional(), Length(max=30)])
    phone2 = StringField("Secondary Phone", validators=[Optional(), Length(max=30)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=200)])
    maps_link = StringField("Google Maps Link", validators=[Optional(), URL(), Length(max=500)])


class SocialLinkForm(FlaskForm):
    platform = StringField("Platform", validators=[DataRequired(), Length(max=50)])
    url = StringField("URL", validators=[DataRequired(), URL(), Length(max=500)])
    icon = StringField("Icon (Font Awesome class)", validators=[Optional(), Length(max=60)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


# --------------------------------------------------------------------------
# Gallery
# --------------------------------------------------------------------------
class GalleryAlbumForm(FlaskForm):
    name = StringField("Album Name", validators=[DataRequired(), Length(max=150)])
    category = StringField(
        "Category Slug (letters, numbers, hyphens)",
        validators=[DataRequired(), Length(max=80)],
    )
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


class GalleryImageForm(FlaskForm):
    album_id = SelectField("Album", coerce=int, validators=[DataRequired()])
    image = FileField("Image", validators=[DataRequired(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    caption = StringField("Caption", validators=[Optional(), Length(max=200)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


class GalleryImageEditForm(FlaskForm):
    caption = StringField("Caption", validators=[Optional(), Length(max=200)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


# --------------------------------------------------------------------------
# Website settings
# --------------------------------------------------------------------------
class SiteSettingForm(FlaskForm):
    college_name = StringField("College Name", validators=[DataRequired(), Length(max=200)])
    logo = FileField("Logo", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)])
    favicon = FileField("Favicon", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS + ["ico"], "Image or .ico file only.")])
    footer_text = StringField("Footer Text", validators=[Optional(), Length(max=300)])
    copyright_text = StringField("Copyright Text", validators=[Optional(), Length(max=300)])
    developer_name = StringField("Developer Name", validators=[Optional(), Length(max=150)])
    developer_url = StringField(
        "Developer Website Link", validators=[Optional(), URL(), Length(max=500)],
    )
    meta_description = StringField(
        "SEO Meta Description", validators=[Optional(), Length(max=300)],
    )
    meta_keywords = StringField(
        "SEO Meta Keywords (comma-separated)", validators=[Optional(), Length(max=300)],
    )
    og_image = FileField(
        "Social Share Image (Open Graph)", validators=[Optional(), FileAllowed(IMAGE_EXTENSIONS, IMAGE_MESSAGE)],
    )


class DeveloperToggleForm(FlaskForm):
    """Developer-only: controls whether the developer credit button shows at all.
    Deliberately excluded from SiteSettingForm so a regular admin cannot touch it."""
    show_developer_button = BooleanField("Show the developer credit button on the site")
