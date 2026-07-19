"""Admin (authenticated) routes providing full CRUD for every CMS module."""
import csv
import io
import os
from datetime import datetime

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .. import models
from ..forms import (
    AboutContentForm,
    ChangePasswordForm,
    ContactInfoForm,
    DeleteForm,
    DeveloperToggleForm,
    EventForm,
    EventImageForm,
    FacultyForm,
    GalleryAlbumForm,
    GalleryImageEditForm,
    GalleryImageForm,
    HomeCTAForm,
    HomeContentForm,
    HomeFeatureForm,
    HomeStatForm,
    LoginForm,
    NoticeForm,
    SiteSettingForm,
    SocialLinkForm,
)
from ..utils import delete_upload, developer_required, login_required, save_upload

admin_bp = Blueprint("admin", __name__)
db = models.db


def _apply_upload(form_field, model_instance, attr, subfolder):
    """Save an uploaded file (if any) onto `model_instance.attr`, replacing the old one."""
    file_storage = form_field.data
    if file_storage and getattr(file_storage, "filename", ""):
        try:
            new_path = save_upload(file_storage, subfolder)
        except ValueError as exc:
            flash(str(exc), "danger")
            return False
        if new_path:
            delete_upload(getattr(model_instance, attr))
            setattr(model_instance, attr, new_path)
    return True


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = models.AdminUser.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["logged_in"] = True
            session["admin_username"] = user.username
            session["role"] = user.role or "admin"
            session.permanent = True
            flash("Welcome back!", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html", form=form)


@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("public.index"))


@admin_bp.route("/admin/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    user = models.AdminUser.query.filter_by(username=session.get("admin_username")).first()

    if form.validate_on_submit():
        if not user or not check_password_hash(user.password_hash, form.current_password.data):
            flash("Current password is incorrect.", "danger")
        elif form.new_password.data != form.confirm_password.data:
            flash("New password and confirmation do not match.", "danger")
        else:
            user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/change_password.html", form=form)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@admin_bp.route("/admin/dashboard")
@login_required
def dashboard():
    counts = {
        "faculty": models.Faculty.query.count(),
        "events": models.Event.query.count(),
        "notices": models.Notice.query.count(),
        "gallery_images": models.GalleryImage.query.count(),
        "messages": models.Message.query.count(),
    }
    return render_template("admin/dashboard.html", counts=counts)


# --------------------------------------------------------------------------
# Home management
# --------------------------------------------------------------------------
@admin_bp.route("/admin/home", methods=["GET", "POST"])
@login_required
def admin_home():
    home = models.HomeContent.get()
    form = HomeContentForm(obj=home)

    if form.validate_on_submit():
        if not _apply_upload(form.banner_image, home, "banner_image", "home"):
            return render_template("admin/home.html", form=form, home=home)
        home.hero_title = form.hero_title.data
        home.hero_subtitle = form.hero_subtitle.data
        home.hero_cta_text = form.hero_cta_text.data
        home.hero_cta_link = form.hero_cta_link.data
        home.welcome_title = form.welcome_title.data
        home.welcome_message = form.welcome_message.data
        db.session.commit()
        flash("Home page content updated.", "success")
        return redirect(url_for("admin.admin_home"))

    return render_template("admin/home.html", form=form, home=home)


@admin_bp.route("/admin/home/stats", methods=["GET", "POST"])
@login_required
def admin_home_stats():
    form = HomeStatForm()
    if form.validate_on_submit():
        stat = models.HomeStat(
            label=form.label.data, value=form.value.data,
            icon=form.icon.data or "fa-solid fa-star",
            display_order=form.display_order.data or 0,
        )
        db.session.add(stat)
        db.session.commit()
        flash("Statistic added.", "success")
        return redirect(url_for("admin.admin_home_stats"))

    stats = models.HomeStat.query.order_by(models.HomeStat.display_order).all()
    return render_template("admin/home_stats.html", form=form, stats=stats, delete_form=DeleteForm())


@admin_bp.route("/admin/home/stats/<int:stat_id>/edit", methods=["GET", "POST"])
@login_required
def edit_home_stat(stat_id):
    stat = models.HomeStat.query.get_or_404(stat_id)
    form = HomeStatForm(obj=stat)
    if form.validate_on_submit():
        form.populate_obj(stat)
        db.session.commit()
        flash("Statistic updated.", "success")
        return redirect(url_for("admin.admin_home_stats"))
    return render_template("admin/home_stat_edit.html", form=form, stat=stat)


@admin_bp.route("/admin/home/stats/<int:stat_id>/delete", methods=["POST"])
@login_required
def delete_home_stat(stat_id):
    stat = models.HomeStat.query.get_or_404(stat_id)
    db.session.delete(stat)
    db.session.commit()
    flash("Statistic deleted.", "danger")
    return redirect(url_for("admin.admin_home_stats"))


@admin_bp.route("/admin/home/features", methods=["GET", "POST"])
@login_required
def admin_home_features():
    form = HomeFeatureForm()
    if form.validate_on_submit():
        feature = models.HomeFeature(
            title=form.title.data, description=form.description.data,
            display_order=form.display_order.data or 0,
        )
        try:
            image_path = save_upload(form.image.data, "home")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.admin_home_features"))
        if image_path:
            feature.image = image_path
        db.session.add(feature)
        db.session.commit()
        flash("Featured section added.", "success")
        return redirect(url_for("admin.admin_home_features"))

    features = models.HomeFeature.query.order_by(models.HomeFeature.display_order).all()
    return render_template("admin/home_features.html", form=form, features=features, delete_form=DeleteForm())


@admin_bp.route("/admin/home/features/<int:feature_id>/edit", methods=["GET", "POST"])
@login_required
def edit_home_feature(feature_id):
    feature = models.HomeFeature.query.get_or_404(feature_id)
    form = HomeFeatureForm(obj=feature)
    if form.validate_on_submit():
        if not _apply_upload(form.image, feature, "image", "home"):
            return render_template("admin/home_feature_edit.html", form=form, feature=feature)
        feature.title = form.title.data
        feature.description = form.description.data
        feature.display_order = form.display_order.data or 0
        db.session.commit()
        flash("Featured section updated.", "success")
        return redirect(url_for("admin.admin_home_features"))
    return render_template("admin/home_feature_edit.html", form=form, feature=feature)


@admin_bp.route("/admin/home/features/<int:feature_id>/delete", methods=["POST"])
@login_required
def delete_home_feature(feature_id):
    feature = models.HomeFeature.query.get_or_404(feature_id)
    delete_upload(feature.image)
    db.session.delete(feature)
    db.session.commit()
    flash("Featured section deleted.", "danger")
    return redirect(url_for("admin.admin_home_features"))


@admin_bp.route("/admin/home/cta", methods=["GET", "POST"])
@login_required
def admin_home_cta():
    form = HomeCTAForm()
    if form.validate_on_submit():
        button = models.HomeCTAButton(
            text=form.text.data, link=form.link.data, display_order=form.display_order.data or 0,
        )
        db.session.add(button)
        db.session.commit()
        flash("CTA button added.", "success")
        return redirect(url_for("admin.admin_home_cta"))

    buttons = models.HomeCTAButton.query.order_by(models.HomeCTAButton.display_order).all()
    return render_template("admin/home_cta.html", form=form, buttons=buttons, delete_form=DeleteForm())


@admin_bp.route("/admin/home/cta/<int:button_id>/delete", methods=["POST"])
@login_required
def delete_home_cta(button_id):
    button = models.HomeCTAButton.query.get_or_404(button_id)
    db.session.delete(button)
    db.session.commit()
    flash("CTA button deleted.", "danger")
    return redirect(url_for("admin.admin_home_cta"))


# --------------------------------------------------------------------------
# Faculty management
# --------------------------------------------------------------------------
@admin_bp.route("/admin/faculty", methods=["GET", "POST"])
@login_required
def admin_faculty():
    form = FacultyForm()
    if form.validate_on_submit():
        member = models.Faculty(
            name=form.name.data, department=form.department.data,
            designation=form.designation.data, qualification=form.qualification.data,
            email=form.email.data, phone=form.phone.data,
            display_order=form.display_order.data or 0, is_leadership=form.is_leadership.data,
        )
        try:
            photo_path = save_upload(form.photo.data, "faculty")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.admin_faculty"))
        if photo_path:
            member.photo = photo_path
        db.session.add(member)
        db.session.commit()
        flash("Faculty member added.", "success")
        return redirect(url_for("admin.admin_faculty"))

    faculty_list = models.Faculty.query.order_by(models.Faculty.display_order).all()
    return render_template("admin/faculty.html", form=form, faculty_list=faculty_list, delete_form=DeleteForm())


@admin_bp.route("/admin/faculty/<int:faculty_id>/edit", methods=["GET", "POST"])
@login_required
def edit_faculty(faculty_id):
    member = models.Faculty.query.get_or_404(faculty_id)
    form = FacultyForm(obj=member)
    if form.validate_on_submit():
        if not _apply_upload(form.photo, member, "photo", "faculty"):
            return render_template("admin/faculty_edit.html", form=form, member=member)
        member.name = form.name.data
        member.department = form.department.data
        member.designation = form.designation.data
        member.qualification = form.qualification.data
        member.email = form.email.data
        member.phone = form.phone.data
        member.display_order = form.display_order.data or 0
        member.is_leadership = form.is_leadership.data
        db.session.commit()
        flash("Faculty member updated.", "success")
        return redirect(url_for("admin.admin_faculty"))
    return render_template("admin/faculty_edit.html", form=form, member=member)


@admin_bp.route("/admin/faculty/<int:faculty_id>/delete", methods=["POST"])
@login_required
def delete_faculty(faculty_id):
    member = models.Faculty.query.get_or_404(faculty_id)
    delete_upload(member.photo)
    db.session.delete(member)
    db.session.commit()
    flash("Faculty member deleted.", "danger")
    return redirect(url_for("admin.admin_faculty"))


# --------------------------------------------------------------------------
# Events management
# --------------------------------------------------------------------------
@admin_bp.route("/admin/events", methods=["GET", "POST"])
@login_required
def admin_events():
    form = EventForm()
    if form.validate_on_submit():
        event = models.Event(
            title=form.title.data, description=form.description.data,
            event_date=form.event_date.data, venue=form.venue.data,
            status=form.status.data,
        )
        try:
            cover_path = save_upload(form.cover_image.data, "events")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.admin_events"))
        if cover_path:
            event.cover_image = cover_path
        db.session.add(event)
        db.session.commit()
        flash("Event added.", "success")
        return redirect(url_for("admin.admin_events"))

    events = models.Event.query.order_by(models.Event.event_date.desc()).all()
    return render_template("admin/events.html", form=form, events=events, delete_form=DeleteForm())


@admin_bp.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = models.Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    image_form = EventImageForm()

    if form.validate_on_submit():
        if not _apply_upload(form.cover_image, event, "cover_image", "events"):
            return render_template(
                "admin/event_edit.html", form=form, event=event,
                image_form=image_form, delete_form=DeleteForm(),
            )
        event.title = form.title.data
        event.description = form.description.data
        event.event_date = form.event_date.data
        event.venue = form.venue.data
        event.status = form.status.data
        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("admin.edit_event", event_id=event.id))

    return render_template(
        "admin/event_edit.html", form=form, event=event,
        image_form=image_form, delete_form=DeleteForm(),
    )


@admin_bp.route("/admin/events/<int:event_id>/images", methods=["POST"])
@login_required
def add_event_image(event_id):
    event = models.Event.query.get_or_404(event_id)
    form = EventImageForm()
    if form.validate_on_submit():
        try:
            image_path = save_upload(form.image.data, "events")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.edit_event", event_id=event.id))
        db.session.add(models.EventImage(event_id=event.id, image=image_path, caption=form.caption.data))
        db.session.commit()
        flash("Gallery image added.", "success")
    else:
        flash("Please choose a valid image to upload.", "danger")
    return redirect(url_for("admin.edit_event", event_id=event.id))


@admin_bp.route("/admin/events/images/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_event_image(image_id):
    image = models.EventImage.query.get_or_404(image_id)
    event_id = image.event_id
    delete_upload(image.image)
    db.session.delete(image)
    db.session.commit()
    flash("Gallery image deleted.", "danger")
    return redirect(url_for("admin.edit_event", event_id=event_id))


@admin_bp.route("/admin/events/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id):
    event = models.Event.query.get_or_404(event_id)
    delete_upload(event.cover_image)
    for image in event.images:
        delete_upload(image.image)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "danger")
    return redirect(url_for("admin.admin_events"))


# --------------------------------------------------------------------------
# Notices management
# --------------------------------------------------------------------------
@admin_bp.route("/admin/notices", methods=["GET", "POST"])
@login_required
def admin_notices():
    form = NoticeForm()
    if form.validate_on_submit():
        notice = models.Notice(
            title=form.title.data, description=form.description.data,
            publish_date=form.publish_date.data, expiry_date=form.expiry_date.data,
            pinned=form.pinned.data,
        )
        try:
            pdf_path = save_upload(form.pdf_attachment.data, "notices", allowed={"pdf"})
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.admin_notices"))
        if pdf_path:
            notice.pdf_path = pdf_path
        db.session.add(notice)
        db.session.commit()
        flash("Notice added successfully!", "success")
        return redirect(url_for("admin.admin_notices"))

    notices_list = models.Notice.query.order_by(models.Notice.pinned.desc(), models.Notice.publish_date.desc()).all()
    return render_template("admin/notices.html", notices=notices_list, form=form, delete_form=DeleteForm())


@admin_bp.route("/admin/notices/edit/<int:notice_id>", methods=["GET", "POST"])
@login_required
def edit_notice(notice_id):
    notice = models.Notice.query.get_or_404(notice_id)
    form = NoticeForm(obj=notice)

    if form.validate_on_submit():
        file_storage = form.pdf_attachment.data
        if file_storage and getattr(file_storage, "filename", ""):
            try:
                new_pdf = save_upload(file_storage, "notices", allowed={"pdf"})
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("admin/notice_edit.html", form=form, notice=notice)
            if new_pdf:
                delete_upload(notice.pdf_path)
                notice.pdf_path = new_pdf
        notice.title = form.title.data
        notice.description = form.description.data
        notice.publish_date = form.publish_date.data
        notice.expiry_date = form.expiry_date.data
        notice.pinned = form.pinned.data
        db.session.commit()
        flash("Notice updated successfully!", "success")
        return redirect(url_for("admin.admin_notices"))

    return render_template("admin/notice_edit.html", form=form, notice=notice)


@admin_bp.route("/admin/notices/delete/<int:notice_id>", methods=["POST"])
@login_required
def delete_notice(notice_id):
    notice = models.Notice.query.get_or_404(notice_id)
    delete_upload(notice.pdf_path)
    db.session.delete(notice)
    db.session.commit()
    flash("Notice deleted.", "danger")
    return redirect(url_for("admin.admin_notices"))


# --------------------------------------------------------------------------
# About college
# --------------------------------------------------------------------------
@admin_bp.route("/admin/about", methods=["GET", "POST"])
@login_required
def admin_about():
    about = models.AboutContent.get()
    form = AboutContentForm(obj=about)

    if form.validate_on_submit():
        ok = True
        ok &= _apply_upload(form.principal_photo, about, "principal_photo", "about")
        ok &= _apply_upload(form.image1, about, "image1", "about")
        ok &= _apply_upload(form.image2, about, "image2", "about")
        if not ok:
            return render_template("admin/about.html", form=form, about=about)

        about.vision = form.vision.data
        about.mission = form.mission.data
        about.principal_name = form.principal_name.data
        about.principal_message = form.principal_message.data
        about.about_text = form.about_text.data
        db.session.commit()
        flash("About College content updated.", "success")
        return redirect(url_for("admin.admin_about"))

    return render_template("admin/about.html", form=form, about=about)


# --------------------------------------------------------------------------
# Contact management
# --------------------------------------------------------------------------
@admin_bp.route("/admin/contact", methods=["GET", "POST"])
@login_required
def admin_contact():
    contact_info = models.ContactInfo.get()
    form = ContactInfoForm(obj=contact_info)

    if form.validate_on_submit():
        contact_info.address = form.address.data
        contact_info.phone1 = form.phone1.data
        contact_info.phone2 = form.phone2.data
        contact_info.email = form.email.data
        contact_info.maps_link = form.maps_link.data
        db.session.commit()
        flash("Contact information updated.", "success")
        return redirect(url_for("admin.admin_contact"))

    social_form = SocialLinkForm()
    social_links = models.SocialLink.query.order_by(models.SocialLink.display_order).all()
    return render_template(
        "admin/contact.html", form=form, contact_info=contact_info,
        social_form=social_form, social_links=social_links, delete_form=DeleteForm(),
    )


@admin_bp.route("/admin/contact/social", methods=["POST"])
@login_required
def add_social_link():
    form = SocialLinkForm()
    if form.validate_on_submit():
        link = models.SocialLink(
            platform=form.platform.data, url=form.url.data,
            icon=form.icon.data or "fa-solid fa-link", display_order=form.display_order.data or 0,
        )
        db.session.add(link)
        db.session.commit()
        flash("Social link added.", "success")
    else:
        flash("Please provide a valid platform name and URL.", "danger")
    return redirect(url_for("admin.admin_contact"))


@admin_bp.route("/admin/contact/social/<int:link_id>/delete", methods=["POST"])
@login_required
def delete_social_link(link_id):
    link = models.SocialLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash("Social link deleted.", "danger")
    return redirect(url_for("admin.admin_contact"))


# --------------------------------------------------------------------------
# Gallery management
# --------------------------------------------------------------------------
@admin_bp.route("/admin/gallery", methods=["GET", "POST"])
@login_required
def admin_gallery():
    album_form = GalleryAlbumForm()
    if album_form.validate_on_submit():
        album = models.GalleryAlbum(
            name=album_form.name.data,
            category=album_form.category.data.strip().lower().replace(" ", "-"),
            display_order=album_form.display_order.data or 0,
        )
        db.session.add(album)
        try:
            db.session.commit()
            flash("Album created.", "success")
        except Exception:
            db.session.rollback()
            flash("An album with that category slug already exists.", "danger")
        return redirect(url_for("admin.admin_gallery"))

    albums = models.GalleryAlbum.query.order_by(models.GalleryAlbum.display_order).all()

    image_form = GalleryImageForm()
    image_form.album_id.choices = [(a.id, a.name) for a in albums]

    return render_template(
        "admin/gallery.html", album_form=album_form, image_form=image_form,
        albums=albums, delete_form=DeleteForm(),
    )


@admin_bp.route("/admin/gallery/albums/<int:album_id>/delete", methods=["POST"])
@login_required
def delete_gallery_album(album_id):
    album = models.GalleryAlbum.query.get_or_404(album_id)
    for image in album.images:
        delete_upload(image.image)
    db.session.delete(album)
    db.session.commit()
    flash("Album and its images deleted.", "danger")
    return redirect(url_for("admin.admin_gallery"))


@admin_bp.route("/admin/gallery/images", methods=["POST"])
@login_required
def add_gallery_image():
    albums = models.GalleryAlbum.query.order_by(models.GalleryAlbum.display_order).all()
    form = GalleryImageForm()
    form.album_id.choices = [(a.id, a.name) for a in albums]

    if form.validate_on_submit():
        try:
            image_path = save_upload(form.image.data, "gallery")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.admin_gallery"))
        db.session.add(models.GalleryImage(
            album_id=form.album_id.data, image=image_path,
            caption=form.caption.data, display_order=form.display_order.data or 0,
        ))
        db.session.commit()
        flash("Image uploaded.", "success")
    else:
        flash("Please choose a valid image and album.", "danger")
    return redirect(url_for("admin.admin_gallery"))


@admin_bp.route("/admin/gallery/images/<int:image_id>/edit", methods=["GET", "POST"])
@login_required
def edit_gallery_image(image_id):
    image = models.GalleryImage.query.get_or_404(image_id)
    form = GalleryImageEditForm(obj=image)
    if form.validate_on_submit():
        image.caption = form.caption.data
        image.display_order = form.display_order.data or 0
        db.session.commit()
        flash("Caption updated.", "success")
        return redirect(url_for("admin.admin_gallery"))
    return render_template("admin/gallery_image_edit.html", form=form, image=image)


@admin_bp.route("/admin/gallery/images/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_gallery_image(image_id):
    image = models.GalleryImage.query.get_or_404(image_id)
    delete_upload(image.image)
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted.", "danger")
    return redirect(url_for("admin.admin_gallery"))


# --------------------------------------------------------------------------
# Website settings
# --------------------------------------------------------------------------
@admin_bp.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    settings = models.SiteSetting.get()
    form = SiteSettingForm(obj=settings)

    if form.validate_on_submit():
        ok = True
        ok &= _apply_upload(form.logo, settings, "logo", "settings")
        ok &= _apply_upload(form.favicon, settings, "favicon", "settings")
        ok &= _apply_upload(form.og_image, settings, "og_image", "settings")
        if not ok:
            return render_template("admin/settings.html", form=form, settings=settings)

        settings.college_name = form.college_name.data
        settings.footer_text = form.footer_text.data
        settings.copyright_text = form.copyright_text.data
        settings.developer_name = form.developer_name.data
        settings.developer_url = form.developer_url.data
        settings.meta_description = form.meta_description.data
        settings.meta_keywords = form.meta_keywords.data
        db.session.commit()
        flash("Website settings updated.", "success")
        return redirect(url_for("admin.admin_settings"))

    return render_template("admin/settings.html", form=form, settings=settings)


@admin_bp.route("/admin/developer-tools", methods=["GET", "POST"])
@developer_required
def admin_developer_tools():
    settings = models.SiteSetting.get()
    form = DeveloperToggleForm(show_developer_button=settings.show_developer_button)

    if form.validate_on_submit():
        settings.show_developer_button = form.show_developer_button.data
        db.session.commit()
        flash("Developer button visibility updated.", "success")
        return redirect(url_for("admin.admin_developer_tools"))

    return render_template("admin/developer_tools.html", form=form, settings=settings)


# --------------------------------------------------------------------------
# Contact messages
# --------------------------------------------------------------------------
@admin_bp.route("/admin/messages")
@login_required
def admin_messages():
    messages = models.Message.query.order_by(models.Message.created_at.desc()).all()
    return render_template("admin/messages.html", messages=messages, delete_form=DeleteForm())


@admin_bp.route("/admin/messages/delete/<int:message_id>", methods=["POST"])
@login_required
def delete_message(message_id):
    message = models.Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted.", "danger")
    return redirect(url_for("admin.admin_messages"))


# --------------------------------------------------------------------------
# Database backup
# --------------------------------------------------------------------------
@admin_bp.route("/admin/backup")
@login_required
def download_backup():
    db_path = current_app.config.get("DATABASE_PATH")
    is_sqlite = current_app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite")

    if not is_sqlite or not db_path or db_path == ":memory:" or not os.path.exists(db_path):
        flash(
            "One-click backup download is only available for the default SQLite "
            "database. If you're using Postgres/MySQL, back it up with your "
            "provider's own tools (e.g. Railway's database snapshots).",
            "danger",
        )
        return redirect(url_for("admin.dashboard"))

    db.session.commit()  # flush any pending writes before copying the file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return send_file(db_path, as_attachment=True, download_name=f"vnc_bca_backup_{timestamp}.db")


# --------------------------------------------------------------------------
# CSV import / export - Faculty
# --------------------------------------------------------------------------
FACULTY_CSV_COLUMNS = [
    "name", "department", "designation", "qualification",
    "email", "phone", "display_order", "is_leadership",
]


@admin_bp.route("/admin/faculty/export.csv")
@login_required
def export_faculty_csv():
    faculty_list = models.Faculty.query.order_by(models.Faculty.display_order).all()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FACULTY_CSV_COLUMNS)
    writer.writeheader()
    for member in faculty_list:
        writer.writerow({col: getattr(member, col) for col in FACULTY_CSV_COLUMNS})

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=faculty_export.csv"},
    )


@admin_bp.route("/admin/faculty/import", methods=["POST"])
@login_required
def import_faculty_csv():
    file_storage = request.files.get("csv_file")
    if not file_storage or not file_storage.filename.lower().endswith(".csv"):
        flash("Please choose a valid .csv file to import.", "danger")
        return redirect(url_for("admin.admin_faculty"))

    try:
        stream = io.StringIO(file_storage.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)
        created = 0
        for row in reader:
            if not row.get("name"):
                continue
            db.session.add(models.Faculty(
                name=row.get("name", "").strip(),
                department=row.get("department", "").strip(),
                designation=row.get("designation", "").strip(),
                qualification=row.get("qualification", "").strip(),
                email=row.get("email", "").strip(),
                phone=row.get("phone", "").strip(),
                display_order=int(row.get("display_order") or 0),
                is_leadership=str(row.get("is_leadership", "")).strip().lower() in ("1", "true", "yes"),
            ))
            created += 1
        db.session.commit()
        flash(f"Imported {created} faculty member(s) from CSV. Add photos individually by editing each entry.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Could not import that file: {exc}", "danger")

    return redirect(url_for("admin.admin_faculty"))


# --------------------------------------------------------------------------
# CSV import / export - Notices
# --------------------------------------------------------------------------
NOTICE_CSV_COLUMNS = ["title", "description", "publish_date", "expiry_date", "pinned"]


@admin_bp.route("/admin/notices/export.csv")
@login_required
def export_notices_csv():
    notices_list = models.Notice.query.order_by(models.Notice.publish_date.desc()).all()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=NOTICE_CSV_COLUMNS)
    writer.writeheader()
    for notice in notices_list:
        writer.writerow({
            "title": notice.title,
            "description": notice.description,
            "publish_date": notice.publish_date.isoformat() if notice.publish_date else "",
            "expiry_date": notice.expiry_date.isoformat() if notice.expiry_date else "",
            "pinned": notice.pinned,
        })

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=notices_export.csv"},
    )


@admin_bp.route("/admin/notices/import", methods=["POST"])
@login_required
def import_notices_csv():
    file_storage = request.files.get("csv_file")
    if not file_storage or not file_storage.filename.lower().endswith(".csv"):
        flash("Please choose a valid .csv file to import.", "danger")
        return redirect(url_for("admin.admin_notices"))

    def _parse_date(value):
        value = (value or "").strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    try:
        stream = io.StringIO(file_storage.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)
        created = 0
        for row in reader:
            if not row.get("title"):
                continue
            db.session.add(models.Notice(
                title=row.get("title", "").strip(),
                description=row.get("description", "").strip(),
                publish_date=_parse_date(row.get("publish_date")) or datetime.utcnow().date(),
                expiry_date=_parse_date(row.get("expiry_date")),
                pinned=str(row.get("pinned", "")).strip().lower() in ("1", "true", "yes"),
            ))
            created += 1
        db.session.commit()
        flash(f"Imported {created} notice(s) from CSV.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Could not import that file: {exc}", "danger")

    return redirect(url_for("admin.admin_notices"))
