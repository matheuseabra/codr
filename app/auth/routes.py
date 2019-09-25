from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user
from app import db
from app.models import User
from app.auth import blueprint
from app.auth.forms import (
    LoginForm,
    RegisterForm,
    ResetPasswordForm,
    ForgotPasswordForm,
)
from app.email import send_password_reset_email
from werkzeug.urls import url_parse


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register", form=form)


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password, try again later.")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.feed")
        return redirect(next_page)
    return render_template("auth/login.html", title="Sign In", form=form)


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@blueprint.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for the instructions to reset your password.")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/forgot_password.html", title="Forgot my password", form=form
    )


@blueprint.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("auth.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form)
