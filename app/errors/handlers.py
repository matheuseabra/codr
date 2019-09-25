from flask import render_template
from app import db
from app.errors import blueprint


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("partials/404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("partials/500.html"), 500
