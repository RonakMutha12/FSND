# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler

from flask_sqlalchemy import SQLAlchemy
from forms import *
from models import Venue, Artist, Show
from sqlalchemy.exc import SQLAlchemyError

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(str(value))
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#
@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------
@app.route("/venues")
def venues():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    venue_query = Venue.query.all()
    data = {}
    for venue in venue_query:
        upcoming_shows = venue.shows.filter(
            Show.start_time > current_time).all()
        city_and_state = venue.city + venue.state
        if city_and_state in data:
            data[city_and_state].get("venues").append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(upcoming_shows),
                }
            )
        else:
            data[city_and_state] = {
                "city": venue.city,
                "state": venue.state,
                "venues": [
                    {
                        "id": venue.id,
                        "name": venue.name,
                        "num_upcoming_shows": len(upcoming_shows),
                    }
                ],
            }
    return render_template("pages/venues.html", areas=data.values())


@app.route("/venues/search", methods=["POST"])
def search_venues():
    venue_query = Venue.query.filter(
        Venue.name.ilike(f"%{request.form.get('search_term')}%")
    )
    venue_list = list(map(Venue.short, venue_query))
    response = {"count": len(venue_list), "data": venue_list}
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if venue:
        venue_details = venue.details()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_shows_query = (
            Show.query.options(db.joinedload(Show.Venue))
            .filter(Show.venue_id == venue_id)
            .filter(Show.start_time > current_time)
            .all()
        )
        new_shows_list = list(map(Show.artist_details, new_shows_query))
        venue_details["upcoming_shows"] = new_shows_list
        venue_details["upcoming_shows_count"] = len(new_shows_list)
        past_shows_query = (
            Show.query.options(db.joinedload(Show.Venue))
            .filter(Show.venue_id == venue_id)
            .filter(Show.start_time <= current_time)
            .all()
        )
        past_shows_list = list(map(Show.artist_details, past_shows_query))
        venue_details["past_shows"] = past_shows_list
        venue_details["past_shows_count"] = len(past_shows_list)
        return render_template("pages/show_venue.html", venue=venue_details)
    return render_template("errors/404.html")


#  Create Venue
#  ----------------------------------------------------------------
@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    try:
        seeking_talent = False
        seeking_description = ""
        if "seeking_talent" in request.form:
            seeking_talent = request.form.get("seeking_talent") == "y"
        if "seeking_description" in request.form:
            seeking_description = request.form.get("seeking_description")
        new_venue = Venue(
            name=request.form.get("name"),
            genres=request.form.getlist("genres"),
            address=request.form.get("address"),
            city=request.form.get("city"),
            state=request.form.get("state"),
            phone=request.form.get("phone"),
            website=request.form.get("website"),
            facebook_link=request.form.get("facebook_link"),
            image_link=request.form.get("image_link"),
            seeking_talent=seeking_talent,
            seeking_description=seeking_description,
        )
        Venue.insert(new_venue)
        flash("Venue " + request.form.get("name") + " was successfully listed!")
    except SQLAlchemyError as e:
        flash(
            "An error occurred. Venue "
            + request.form.get("name")
            + " could not be listed."
        )
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    venue_data = Venue.query.get(venue_id)
    if venue_data:
        Venue.delete(venue_data)
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artist_query = Artist.query.all()
    artist_list = list(map(Artist.short, artist_query))
    return render_template("pages/artists.html", artists=artist_list)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    artist_query = Artist.query.filter(
        Artist.name.ilike("%" + request.form["search_term"] + "%")
    )
    artist_list = list(map(Artist.short, artist_query))
    response = {"count": len(artist_list), "data": artist_list}
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist_query = Artist.query.get(artist_id)
    if artist_query:
        artist_details = Artist.details(artist_query)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_shows_query = (
            Show.query.options(db.joinedload(Show.Artist))
            .filter(Show.artist_id == artist_id)
            .filter(Show.start_time > current_time)
            .all()
        )
        new_shows_list = list(map(Show.venue_details, new_shows_query))
        artist_details["upcoming_shows"] = new_shows_list
        artist_details["upcoming_shows_count"] = len(new_shows_list)
        past_shows_query = (
            Show.query.options(db.joinedload(Show.Artist))
            .filter(Show.artist_id == artist_id)
            .filter(Show.start_time <= current_time)
            .all()
        )
        past_shows_list = list(map(Show.venue_details, past_shows_query))
        artist_details["past_shows"] = past_shows_list
        artist_details["past_shows_count"] = len(past_shows_list)
        return render_template("pages/show_artist.html", artist=artist_details)
    return render_template("errors/404.html")


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_query = Artist.query.get(artist_id)
    if artist_query:
        artist_details = Artist.details(artist_query)
        form.name.data = artist_details.get("name")
        form.genres.data = artist_details.get("genres")
        form.city.data = artist_details.get("city")
        form.state.data = artist_details.get("state")
        form.phone.data = artist_details.get("phone")
        form.website.data = artist_details.get("website")
        form.facebook_link.data = artist_details.get("facebook_link")
        form.seeking_venue.data = artist_details.get("seeking_venue")
        form.seeking_description.data = artist_details.get(
            "seeking_description")
        form.image_link.data = artist_details.get("image_link")
        return render_template(
            "forms/edit_artist.html", form=form, artist=artist_details
        )
    return render_template("errors/404.html")


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    artist_data = Artist.query.get(artist_id)
    if artist_data:
        if form.validate():
            seeking_venue = False
            seeking_description = ""
            if "seeking_venue" in request.form:
                seeking_venue = request.form.get("seeking_venue") == "y"
            if "seeking_description" in request.form:
                seeking_description = request.form.get("seeking_description")
            artist_data.name = request.form.get("name")
            artist_data.genres = request.form.get("genres")
            artist_data.city = request.form.get("city")
            artist_data.state = request.form.get("state")
            artist_data.phone = request.form.get("phone")
            artist_data.website = request.form.get("website")
            artist_data.facebook_link = request.form.get("facebook_link")
            artist_data.image_link = request.form.get("image_link")
            artist_data.seeking_description = seeking_description
            artist_data.seeking_venue = seeking_venue
            Artist.update(artist_data)
            return redirect(url_for("show_artist", artist_id=artist_id))
        else:
            print(form.errors)
    return render_template("errors/404.html"), 404


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if venue:
        venue_details = venue.details()
        form.name.data = venue_details["name"]
        form.genres.data = venue_details["genres"]
        form.address.data = venue_details["address"]
        form.city.data = venue_details["city"]
        form.state.data = venue_details["state"]
        form.phone.data = venue_details["phone"]
        form.website.data = venue_details["website"]
        form.facebook_link.data = venue_details["facebook_link"]
        form.seeking_talent.data = venue_details["seeking_talent"]
        form.seeking_description.data = venue_details["seeking_description"]
        form.image_link.data = venue_details["image_link"]
        return render_template("forms/edit_venue.html", form=form, venue=venue_details)
    return render_template("errors/404.html")


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    venue_data = Venue.query.get(venue_id)
    if venue_data:
        if form.validate():
            seeking_talent = False
            seeking_description = ""
            if "seeking_talent" in request.form:
                seeking_talent = request.form.get("seeking_talent") == "y"
            if "seeking_description" in request.form:
                seeking_description = request.form.get("seeking_description")
            venue_data.name = request.form.get("name")
            venue_data.genres = request.form.get("genres")
            venue_data.address = request.form.get("address")
            venue_data.city = request.form.get("city")
            venue_data.state = request.form.get("state")
            venue_data.phone = request.form.get("phone")
            venue_data.website = request.form.get("website")
            venue_data.facebook_link = request.form.get("facebook_link")
            venue_data.image_link = request.form.get("image_link")
            venue_data.name = seeking_description
            venue_data.name = seeking_talent
            Venue.update(venue_data)
            return redirect(url_for("show_venue", venue_id=venue_id))
        else:
            print(form.errors)
    return render_template("errors/404.html"), 404


#  Create Artist
#  ----------------------------------------------------------------
@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    try:
        seeking_venue = False
        seeking_description = ""
        if "seeking_venue" in request.form:
            seeking_venue = request.form.get("seeking_venue") == "y"
        if "seeking_description" in request.form:
            seeking_description = request.form.get("seeking_description")
        new_artist = Artist(
            name=request.form.get("name"),
            genres=request.form.getlist("genres"),
            city=request.form.get("city"),
            state=request.form.get("state"),
            phone=request.form.get("phone"),
            website=request.form.get("website"),
            facebook_link=request.form.get("facebook_link"),
            image_link=request.form.get("image_link"),
            seeking_venue=seeking_venue,
            seeking_description=seeking_description,
        )
        Artist.insert(new_artist)
        flash("Artist " + request.form.get("name") + " was successfully listed!")
    except SQLAlchemyError as e:
        flash(
            "An error occurred. Artist "
            + request.form.get("name")
            + " could not be listed."
        )

    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    shows_query = Show.query.options(
        db.joinedload(Show.Venue), db.joinedload(Show.Artist)
    ).all()
    shows_list = list(map(Show.details, shows_query))
    return render_template("pages/shows.html", shows=shows_list)


@app.route("/shows/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    try:
        new_show = Show(
            venue_id=request.form.get("venue_id"),
            artist_id=request.form.get("artist_id"),
            start_time=request.form.get("start_time"),
        )
        Show.insert(new_show)
        flash("Show was successfully listed!")
    except SQLAlchemyError as e:
        flash("An error occurred. Show could not be listed.")
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#
# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
