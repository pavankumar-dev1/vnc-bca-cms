"""Public (visitor-facing) routes.

Every value rendered by these views comes from the database - there is
no hardcoded website copy left in the templates or here.
"""
import calendar
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import models
from ..forms import ContactForm

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    form = ContactForm()
    home = models.HomeContent.get()
    stats = models.HomeStat.query.order_by(models.HomeStat.display_order).all()
    features = models.HomeFeature.query.order_by(models.HomeFeature.display_order).all()
    cta_buttons = models.HomeCTAButton.query.order_by(models.HomeCTAButton.display_order).all()
    leaders = (
        models.Faculty.query.filter_by(is_leadership=True)
        .order_by(models.Faculty.display_order)
        .all()
    )
    contact_info = models.ContactInfo.get()
    social_links = models.SocialLink.query.order_by(models.SocialLink.display_order).all()

    return render_template(
        "index.html",
        form=form,
        home=home,
        stats=stats,
        features=features,
        cta_buttons=cta_buttons,
        leaders=leaders,
        contact_info=contact_info,
        social_links=social_links,
    )


@public_bp.route("/staff")
def staff():
    faculty = models.Faculty.query.order_by(models.Faculty.display_order).all()
    return render_template("staff.html", faculty=faculty)


@public_bp.route("/about")
def about():
    about_content = models.AboutContent.get()
    return render_template("about.html", about=about_content)


@public_bp.route("/gallery")
def gallery():
    albums = models.GalleryAlbum.query.order_by(models.GalleryAlbum.display_order).all()
    return render_template("gallery.html", albums=albums, title="Gallery")


@public_bp.route("/gallery/<category>")
def gallery_album(category):
    album = models.GalleryAlbum.query.filter_by(category=category).first_or_404()
    return render_template("gallery_album.html", album=album)


@public_bp.route("/event")
def event():
    events = models.Event.query.order_by(models.Event.event_date.desc()).all()
    legacy_album = models.GalleryAlbum.query.filter_by(category="event").first()
    return render_template("event.html", events=events, legacy_album=legacy_album)


@public_bp.route("/event/<int:event_id>")
def event_detail(event_id):
    event_obj = models.Event.query.get_or_404(event_id)
    return render_template("event_detail.html", event=event_obj)


@public_bp.route("/event/calendar")
def event_calendar():
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    cal = calendar.Calendar(firstweekday=6)  # weeks start on Sunday
    weeks = cal.monthdayscalendar(year, month)

    events_by_day = {}
    for event_obj in models.Event.query.all():
        if event_obj.event_date and event_obj.event_date.year == year and event_obj.event_date.month == month:
            events_by_day.setdefault(event_obj.event_date.day, []).append(event_obj)

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    return render_template(
        "event_calendar.html",
        year=year, month=month, month_name=calendar.month_name[month],
        weeks=weeks, events_by_day=events_by_day, today=today,
        prev_year=prev_year, prev_month=prev_month, next_year=next_year, next_month=next_month,
    )


@public_bp.route("/etnic")
def etnic():
    album = models.GalleryAlbum.query.filter_by(category="etnic").first()
    return render_template("etnic.html", album=album)


@public_bp.route("/building")
def building():
    album = models.GalleryAlbum.query.filter_by(category="building").first()
    return render_template("building.html", album=album)


@public_bp.route("/developer")
def developer():
    return render_template("developer.html")


@public_bp.route("/notices")
def notices():
    show_all = request.args.get("all") == "1"
    query = models.Notice.query
    if not show_all:
        today = date.today()
        query = query.filter(
            models.db.or_(models.Notice.expiry_date.is_(None), models.Notice.expiry_date >= today)
        )
    notices_list = query.order_by(models.Notice.pinned.desc(), models.Notice.publish_date.desc()).all()
    return render_template("notices.html", notices=notices_list, show_all=show_all)


@public_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    results = {"faculty": [], "events": [], "notices": [], "albums": []}

    if q:
        like = f"%{q}%"
        results["faculty"] = models.Faculty.query.filter(
            models.db.or_(
                models.Faculty.name.ilike(like),
                models.Faculty.designation.ilike(like),
                models.Faculty.department.ilike(like),
            )
        ).all()
        results["events"] = models.Event.query.filter(
            models.db.or_(models.Event.title.ilike(like), models.Event.description.ilike(like))
        ).all()
        results["notices"] = models.Notice.query.filter(
            models.db.or_(models.Notice.title.ilike(like), models.Notice.description.ilike(like))
        ).all()
        results["albums"] = models.GalleryAlbum.query.filter(models.GalleryAlbum.name.ilike(like)).all()

    total = sum(len(v) for v in results.values())
    return render_template("search_results.html", q=q, results=results, total=total)
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        message = models.Message(
            name=form.name.data, email=form.email.data, message=form.message.data
        )
        models.db.session.add(message)
        models.db.session.commit()
        flash("Message sent! We will get back to you soon.", "success")
    else:
        flash("Please fill in all fields with a valid email address.", "danger")
    return redirect(url_for("public.index") + "#contact")
