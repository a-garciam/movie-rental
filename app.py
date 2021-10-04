from flask import Flask, render_template, request
import datetime
import requests
import random
from iso_dict import full_lang

app = Flask(__name__)
wishlist = []
rented_list = []


class Movie:
    """
    Movie class to define Movie Objects
    """

    def __init__(self, id, title, overview, poster, vote_average, vote_count, release_date, genre, status,
                 lang, adult, face, fcolor, rented):
        self.id = id
        self.title = title
        self.overview = overview
        self.poster = poster
        self.vote_average = vote_average
        self.vote_count = vote_count
        self.release_date = release_date
        self.genre = genre
        self.status = status
        self.lang = lang
        self.adult = adult
        self.face = face
        self.fcolor = fcolor
        self.rented = rented


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/home")
def index():
    configure_request(app)
    db = get_movies(1, "trending/movie/day", "", 1)
    h1 = "Today's Editor's Choice - just for you!"
    h2 = "- Our recommendations change daily, add them to your wishlist before we update it."
    return render_template("table.html", movies=db, h1=h1, h2=h2)


@app.route("/search")
def search():
    q = request.args.get("q")
    results = search_movie(q)
    return render_template("search.html", results=results, q=q)


@app.route("/random")
def rand():
    x = random.randint(5, 779599)
    result = get_movie(x)
    while result.poster == "" or result.adult:
        x = random.randint(5, 779599)
        result = get_movie(x)
    return render_template("display_movie.html", movie=result)


@app.route("/movie/<int:id>")
def movie(id):
    movie = get_movie(id)
    if movie is None:
        return render_template("error.html")
    else:
        return render_template("display_movie.html", movie=movie)


@app.route("/test")
def test():
    return render_template("solid.html")


@app.route("/my_wishlist")
def my_wishlist():
    db = []
    if wishlist == []:
        h3 = "It looks like your wishlist is empty.."
        return render_template("empty_wishlist.html", h3=h3)
    for id in wishlist:
        db.append(get_movie(id))
    db = process_results(db, False)
    h1 = "This is your wishlist."
    h2 = "All your saved movies are here, rent one now :)"
    return render_template("wishlist.html", movies=db, h1=h1, h2=h2)


@app.route("/my_movies")
def my_movies():
    rented = []
    if rented_list == []:
        h3 = "You haven't rented anything yet..."
        return render_template("empty_wishlist.html", h3=h3)
    for id in rented_list:
        rented.append(get_movie(id))
    result = process_results(rented, False)
    return render_template("rented_movies.html", popular=result, list="Your rented movies.")


@app.route("/popular/<int:page>")
def popular(page):
    if page in range(1, 1001):
        route = "/popular/"
        one = get_movies(1, "trending/movie/day", "", page)
        if page == 1:
            return render_template("show_movies_poster_1.html", popular=one, list="Trending", route=route,
                                   page_num=page)
        return render_template("show_movies_poster.html", popular=one, list="Trending", route=route, page_num=page)
    else:
        return render_template("error.html")


@app.route("/best/<int:page>")
def best(page):
    if page in range(1, 29):
        route = "/best/"
        one = get_movies(0, "discover/movie", "sort_by=vote_average.desc&vote_count.gte=5000", page)
        if page == 1:
            return render_template("show_movies_poster_1.html", popular=one, list="All-Time Bests", route=route,
                                   page_num=page)
        return render_template("show_movies_poster.html", popular=one, list="All-Time Bests", route=route,
                               page_num=page)
    else:
        return render_template("error.html")


@app.route("/new/<int:page>")
def new(page):
    if page in range(1, 1001):
        route = "/new/"
        one = get_movies(1, "movie/now_playing", "", page)
        if page == 1:
            return render_template("show_movies_poster_1.html", popular=one, list="Latest Releases", route=route,
                                   page_num=page)
        return render_template("show_movies_poster.html", popular=one, list="Latest Releases", route=route,
                               page_num=page)
    else:
        return render_template("error.html")


@app.route("/upcoming/<int:page>")
def coming_soon(page):
    if page in range(1, 1001):
        route = "/upcoming/"
        one = get_movies(0, "discover/movie", "primary_release_date.gte=2021-01-20&primary_release_date.lte=2021-06-20",
                         page)
        if page == 1:
            return render_template("show_movies_poster_1.html", popular=one, list="Upcoming Movies", route=route,
                                   page_num=page)
        return render_template("show_movies_poster.html", popular=one, list="Upcoming Movies", route=route,
                               page_num=page)
    else:
        return render_template("error.html")


@app.route("/year")
def year():
    return render_template("year_search.html")


@app.route("/year/<string:year>/<int:page>")
def year_opt(year, page):
    if page in range(1, 300):
        # req_year = request.args.get("my_year")
        route = "/year/" + year + "/"
        one = get_movies(0, "discover/movie", "sort_by=vote_count.desc&primary_release_year=" + year, page)
        if page == 1:
            return render_template("show_movies_poster_1.html", popular=one, list="Best Movies of " + year, route=route,
                                   page_num=page)
        return render_template("show_movies_poster.html", popular=one, list="Best Movies of " + year, route=route,
                               page_num=page)
    else:
        return render_template("error.html")


@app.route("/year/")
def year_first():
    req_year = request.args.get("my_year")
    route = "/year/" + req_year + "/"
    one = get_movies(0, "discover/movie", "sort_by=vote_count.desc&primary_release_year=" + req_year, 1)
    return render_template("show_movies_poster_1.html", popular=one, list="Best Movies of " + req_year, route=route,
                           page_num=1)


@app.route("/category")
def category():
    return render_template("category_search.html")


@app.route("/category/<string:cat>")
def category_opt(cat):
    results = search_category(cat)
    if results:
        h1 = "Today's most popular movies for this category."
        h2 = "Add your favs to the wishlist or rent them now!"
        return render_template("table.html", movies=results, h1=h1, h2=h2)
    else:
        return render_template("error.html")


@app.route("/home/<int:quack>")
def add_to_wishlist(quack):
    wishlist.append(quack)
    return '', 204


@app.route("/home/r/<int:rent_id>")
def add_to_rent_list(rent_id):
    rented_list.append(rent_id)
    get_movie(rent_id).rented = 1
    return '', 204


@app.route("/my_wishlist/<int:quack>")
def delete_from_wishlist(quack):
    wishlist.remove(quack)
    db = []
    for id in wishlist:
        db.append(get_movie(id))
    db = process_results(db, False)
    h1 = "This is your wishlist."
    h2 = "All your saved movies are here, rent one now :)"
    return render_template("wishlist.html", movies=db, h1=h1, h2=h2)


def configure_request(app):
    global api_key, base_url
    api_key = "42f5e47bc0d20e958e0dfc2d6d006353"
    base_url = "https://api.themoviedb.org/3/movie/{}?api_key={}"


def get_movies(basic, command, query, page):
    """
    Function that gets the json response to our url request
    """
    movie_results = []
    if basic:
        base_url = "https://api.themoviedb.org/3/{}?api_key={}&language=en-US&page={}"
        get_movies_url = base_url.format(command, api_key, page)
    else:
        base_url = "https://api.themoviedb.org/3/{}?api_key={}&{}&language=en-US&page={}"
        get_movies_url = base_url.format(command, api_key, query, page)
    get_movies_response = requests.get(get_movies_url).json()
    if get_movies_response['results']:
        movie_results_list = get_movies_response['results']
        movie_results = process_results(movie_results_list, True)
    return movie_results


def process_results(movie_list, json):
    """
    Function  that processes the movie result and transform them to a list of Objects
    Args:
        movie_list: A list of dictionaries that contain movie details
    Returns :
        movie_results: A list of movie objects
    """
    movie_results = []
    for movie_item in movie_list:
        if json:
            movie = get_movie(movie_item.get('id'))
        else:
            movie = movie_item
        id = movie.id
        title = movie.title
        overview = movie.overview
        poster = movie.poster
        vote_average = movie.vote_average
        vote_count = movie.vote_count
        release_date = movie.release_date
        genres = movie.genre
        gen_list = []
        for obj in genres:
            gen_list.append(obj['name'])
        gen_str = ', '.join([str(elem) for elem in gen_list])
        gen_str.replace("'", "")
        gen_str.replace("[", "")
        gen_str.replace("]", "")
        genre = gen_str
        status = movie.status
        lang = movie.lang
        adult = movie.adult
        rented = movie.rented
        if vote_average <= 4.99:
            face = "fa fa-frown-open"
            fcolor = "#FF3333"
        elif vote_average <= 5.99:
            face = "fa fa-meh"
            fcolor = "#FFCE33"
        elif vote_average <= 7.99:
            face = "fa fa-smile-beam"
            fcolor = "#38D30A"
        else:
            face = "fa fa-grin-beam"
            fcolor = "#158928"
        if poster != "":
            movie_object = Movie(id, title, overview, poster, vote_average, vote_count, release_date, genre, status,
                                 lang, adult, face, fcolor, rented)
            movie_results.append(movie_object)
    return movie_results


def check_rent_list(id):
    if id in rented_list:
        return 1
    else:
        return 0


def get_movie(id):
    configure_request(app)
    get_movie_details_url = base_url.format(id, api_key)
    movie_details_response = requests.get(get_movie_details_url).json()
    if movie_details_response:
        id = movie_details_response.get('id')
        title = movie_details_response.get('title')
        overview = movie_details_response.get('overview')
        poster = movie_details_response.get('poster_path')
        vote_average = movie_details_response.get('vote_average')
        vote_count = movie_details_response.get('vote_count')
        release_date = movie_details_response.get('release_date')
        rented = check_rent_list(id)
        if release_date:
            release_date = datetime.datetime.strptime(release_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        else:
            release_date = "Unknown Release Date"
        genre = movie_details_response.get('genres')
        status = movie_details_response.get('status')
        lang = movie_details_response.get('original_language')
        lang = full_lang(lang)
        adult = movie_details_response.get('adult')
        face = ""
        fcolor = ""
        if poster:
            movie_object = Movie(id, title, overview, 'https://image.tmdb.org/t/p/w500/' + poster, vote_average,
                                 vote_count, release_date, genre, status, lang, adult, face, fcolor, rented)
        else:
            movie_object = Movie(id, title, overview, "", vote_average, vote_count, release_date, genre, status, lang,
                                 adult, face, fcolor, rented)
        return movie_object
    else:
        return None


def search_movie(movie_name):
    search_movie_results = []
    search_movie_url = 'https://api.themoviedb.org/3/search/movie?api_key={}&query={}'.format(api_key, movie_name)
    search_movie_response = requests.get(search_movie_url).json()
    if search_movie_response['results']:
        search_movie_list = search_movie_response['results']
        search_movie_results = process_results(search_movie_list, True)
    return search_movie_results


def search_category(cat):
    search_cat_url = 'https://api.themoviedb.org/3/discover/movie?language=en-US&sort_by=popularity.desc&include_adult=false&page=1&with_genres={}&api_key={}'.format(
        cat, api_key)
    search_cat_response = requests.get(search_cat_url).json()
    if search_cat_response['results']:
        search_cat_list = search_cat_response['results']
        search_cat_results = process_results(search_cat_list, True)
        return search_cat_results
    else:
        return False


configure_request(app)
app.run(debug=True)
