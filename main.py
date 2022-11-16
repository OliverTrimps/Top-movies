from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, HiddenField
from wtforms.validators import DataRequired
import requests

API_KEY = "3e0acf6324ac4883462fd4d13e2a3c02"
API_ENDPOINT = "https://api.themoviedb.org/3/search/movie?"
API_MOVIE_ENDPOINT = "https://api.themoviedb.org/3/movie/"
TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'
# example api request = https://api.themoviedb.org/3/movie/550?api_key=3e0acf6324ac4883462fd4d13e2a3c02
# api read access token v4 auth = eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzZTBhY2Y2MzI0YWM0ODgzNDYyZmQ0ZDEzZTJhM2MwMiIsInN1YiI6IjYzNzE0MzRhMjE2MjFiMDA3NzdkZjBmYyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.pxsN0hvmsbhSUA4_r5-Mxwf4aORUpmsLPvQOxB2m1lw

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Create DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-books-collection.db"
db = SQLAlchemy(app)


class RateMovieForm(FlaskForm):
    id = HiddenField(validators=[DataRequired()])
    rating = FloatField(label="Your Rating Out of 10, e.g. 7.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


# Create Table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()
# Testing to see if the database works
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()


@app.route("/")
def home():
    with app.app_context():
        movies = Movie.query.order_by(Movie.rating).all()  # This line creates a list of all the movies sorted by rating
        for i in range(len(movies)):  # This line loops through all the movies
            movies[i].ranking = len(movies) - i  # This line gives each movie a new ranking reversed from their order in all_movies
    return render_template("index.html", movie_list=movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    form = RateMovieForm(id=movie_id)
    # data = request.form
    if form.validate_on_submit():
        with app.app_context():
            # movie_id_input = data['id']
            movie_selected = Movie.query.get(movie_id)
            movie_selected.rating = form.rating.data
            movie_selected.review = form.review.data
            db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie)


@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    # movie = Movie.query.get(movie_id)
    with app.app_context():
        movie_selected = Movie.query.get(movie_id)
        db.session.delete(movie_selected)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(url=API_ENDPOINT, params={'api_key': API_KEY, 'query': movie_title})
        data = response.json()['results']
        # print(movie_title)
        # print(data)
        return render_template('select.html', options=data)
    return render_template("add.html", form=form)


@app.route('/find')
def find():
    movie_api_id = request.args.get('id')
    if movie_api_id:
        response = requests.get(url=f"{API_MOVIE_ENDPOINT}/{movie_api_id}", params={'api_key': API_KEY, 'language': 'en-US'})
        data = response.json()
        with app.app_context():
            new_movie = Movie(title=data['title'],
                              year=data['release_date'].split('-')[0],
                              img_url=f"{TMDB_IMAGE_URL}{data['poster_path']}",
                              description=data['overview'])
            db.session.add(new_movie)
            db.session.commit()
            movie_id = new_movie.id
            db.session.commit()
        # print(movie_api_id, movie_id)
        # with app.app_context():
        #     movie = Movie.query.filter_by(title=data['title'])
        #     movie_id = movie.id
        #     db.session.commit()
        # print(movie_id)
        # form = RateMovieForm(id=Movie.query.get(new_movie.id))
        # print(form.id.data)
        return redirect(url_for('edit', id=movie_id))
        # return render_template('edit.html', id=form)


if __name__ == '__main__':
    app.run(debug=True)
