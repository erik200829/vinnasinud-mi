from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "lykilord"  
blogs = []  

def find_next_id():
    if not blogs:
        return 1
    return max(blog["id"] for blog in blogs) + 1


@app.route("/")
def index():
    sorted_blogs = sorted(blogs, key=lambda b: b["date"], reverse=True)
    return render_template("index.html", blogs=sorted_blogs)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == "dummy@mail.com" and password == "123456":
            session["user"] = email
            flash("Innskráning tókst!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Vitlaust netfang eða lykilorð", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Þú hefur verið skráður út", "info")
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session:
        flash("Þú þarft að skrá þig inn", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        author = request.form.get("author")
        date = datetime.now()

        if not title or not content or not author:
            flash("Vantar titil, höfund eða efni", "error")
        else:
            blogs.append({
                "id": find_next_id(),
                "title": title,
                "content": content,
                "author": author,
                "date": date
            })
            flash("Færsla vistuð!", "success")
            return redirect(url_for("index"))

    return render_template("admin.html", user=session["user"])


if __name__ == '__main__':
    app.run(debug=True)