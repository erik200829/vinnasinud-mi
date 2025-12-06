from flask import Flask, render_template, request, redirect, url_for
import urllib.request, json, random
from tinydb import TinyDB
from urllib.parse import quote
from datetime import datetime

app = Flask(__name__)



def fetch_shows(page=0):
    url = f"https://api.tvmaze.com/shows?page={page}" if page else "https://api.tvmaze.com/shows"
    with urllib.request.urlopen(url) as u:
        return json.loads(u.read().decode())

data = fetch_shows(page=0)

def all_genres(shows):
    g = set()
    for s in shows:
        for genre in s.get("genres", []):
            g.add(genre)
    return sorted(g)


@app.context_processor
def inject_globals():
    return {"all_genres": all_genres(data)}

def fmt_date(isodate):
    if not isodate:
        return "Óþekkt"
    try:
        d = datetime.strptime(isodate, "%Y-%m-%d")
        return d.strftime("%d.%m.%Y")
    except Exception:
        return isodate

@app.route('/')
def index():
    listi = random.sample(data, 20)
    return render_template('index.html', listi=listi)

@app.route('/show/<int:id>')
def show(id):
    with urllib.request.urlopen(f"https://api.tvmaze.com/shows/{id}") as u:
        show_data = json.loads(u.read().decode())
    show_data['premiered_fmt'] = fmt_date(show_data.get('premiered'))
    show_data['ended_fmt'] = fmt_date(show_data.get('ended'))
    return render_template('show.html', date=show_data)

@app.route('/search', methods=["GET", "POST"])
def search():
    query = ""
    if request.method == "POST":
        query = request.form.get("q", "").strip()
    else:
        query = request.args.get("q", "").strip()

    results = []
    if query:
        safe_query = quote(query, safe="")
        with urllib.request.urlopen(f"https://api.tvmaze.com/search/shows?q={safe_query}") as u:
            data_api = json.loads(u.read().decode())
        results = [item.get("show") for item in data_api]

    return render_template("search.html", results=results, query=query)

@app.route('/genre/<genre>')
def genre(genre):
    shows = [s for s in data if genre in s.get('genres', [])]
    return render_template("genre.html", shows=shows, genre=genre)

db = TinyDB("profile.json")

@app.route('/about')
def about():
    profile = db.all()
    return render_template("about.html", profile=profile[0] if profile else {})

@app.route('/edit', methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("desc", "").strip()
        db.truncate()
        db.insert({"name": name, "desc": desc})
        return redirect(url_for("about"))
    profile = db.all()
    return render_template("edit.html", profile=profile[0] if profile else {})




if __name__ == '__main__':
    app.run(debug=True)
