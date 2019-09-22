from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.models import User, Post
from app.forms import LoginForm, RegisterForm, EditProfileForm, PostForm
from werkzeug.urls import url_parse
from datetime import datetime


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route("/", methods=["GET", "POST"])
@app.route("/feed", methods=["GET", "POST"])
@login_required
def feed():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("feed"))
    page = request.args.get("page", 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config["PAGINATION_LIMIT"], False
    )
    return render_template("feed.html", title="Feed", form=form, posts=posts.items)


@app.route("/explore", methods=["GET"])
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config["PAGINATION_LIMIT"], False
    )
    next_url = url_for("explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("explore", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "explore.html",
        title="Explore",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password, try again later.")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("feed")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("profile.html", user=user)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.bio.data = current_user.bio
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@app.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} was not found".format(username))
        return redirect(url_for("index"))
    if user == current_user:
        flash("You cannot follow yourself!")
        return redirect(url_for("user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash("You are following {}".format(username))
    return redirect(url_for("user", username=username))


@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for("index"))
    if user == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for("user", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash("You are not following {}.".format(username))
    return redirect(url_for("user", username=username))
