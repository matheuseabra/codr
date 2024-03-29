from flask import (
    request,
    render_template,
    flash,
    redirect,
    url_for,
    g,
    jsonify,
    current_app,
)
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import _, get_locale
from app import db
from app.models import User, Post
from app.email import send_password_reset_email
from werkzeug.urls import url_parse
from datetime import datetime
from app.main.forms import EditProfileForm, PostForm
from app.main import blueprint


@blueprint.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.locale = str(get_locale())


@blueprint.route("/", methods=["GET"])
def index():
    return render_template("landing.html", title="Home")


@blueprint.route("/feed", methods=["GET", "POST"])
@login_required
def feed():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("main.feed"))
    page = request.args.get("page", 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config["PAGINATION_LIMIT"], False
    )
    return render_template("feed.html", title="Feed", form=form, posts=posts.items)


@blueprint.route("/explore", methods=["GET"])
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config["PAGINATION_LIMIT"], False
    )
    next_url = url_for("main.explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.explore", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "explore.html",
        title="Explore",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@blueprint.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("profile.html", user=user)


@blueprint.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        print(form.bio.data)
        current_user.bio = form.bio.data
        current_user.username = form.username.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.bio.data = current_user.bio
    return render_template("edit_profile.html", title=_("Edit Profile"), form=form)


@blueprint.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("User %(username)s not found.", username=username))
        return redirect(url_for("main.feed"))
    if user == current_user:
        flash("You cannot follow yourself!")
        return redirect(url_for("main.user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash("You are following {}".format(username))
    return redirect(url_for("main.user", username=username))


@blueprint.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for("main.feed"))
    if user == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for("main.user", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash("You are not following {}.".format(username))
    return redirect(url_for("main.user", username=username))
