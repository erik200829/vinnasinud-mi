import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from tinydb import TinyDB
from werkzeug.utils import secure_filename
import requests
from datetime import datetime
from math import ceil
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash
from tinydb import TinyDB, where



BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PER_PAGE'] = 5

db = TinyDB(os.path.join(BASE_DIR, 'data', 'posts.json'))






ADMIN_EMAIL = "admin@admin.is"
ADMIN_PASSWORD = "123456"

app.jinja_env.globals.update(zip=zip)

users_db = TinyDB(os.path.join(BASE_DIR, 'data', 'users.json'))
categories_db = TinyDB(os.path.join(BASE_DIR, 'data', 'categories.json'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

       
        if users_db.search(Query().email == email):
            flash('Þetta netfang er þegar í notkun', 'error')
            return redirect(url_for('register'))

     
        hashed_pw = generate_password_hash(password)
        users_db.insert({'email': email, 'password': hashed_pw})

        flash('Nýskráning tókst! Skráðu þig nú inn.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')





@app.context_processor
def inject_categories():
    all_categories = [c['name'] for c in categories_db.all()]
    return dict(categories=all_categories)







def get_all_posts():
    posts = db.all()
    def parse_created(p):
        try:
            return datetime.fromisoformat(p.get('created'))
        except:
            return datetime.min
    posts_sorted = sorted(posts, key=parse_created, reverse=True)
    return posts_sorted







def get_dog_images(count):
    try:
        r = requests.get(f"https://dog.ceo/api/breeds/image/random/{count}")
        if r.ok:
            return r.json().get('message', [])
    except:
        pass
   
    return ["/static/images/fallback_dog.jpg"] * count







def get_random_dog_image():
    try:
        r = requests.get("https://dog.ceo/api/breeds/image/random", timeout=5)
        if r.ok:
            return r.json().get('message')
    except:
        pass
    return None

def get_dog_fact():
    try:
        r = requests.get("https://dog-api.kinduff.com/api/facts", timeout=5)
        if r.ok:
            data = r.json()
            facts = data.get('facts')
            if facts and len(facts) > 0:
                return facts[0]
    except Exception as e:
        print("Villa við API kall:", e)
    return "Hundar elska að leika sér með bolta!"

@app.route('/')
def index():
    image = get_random_dog_image() or ''
    fact = get_dog_fact() or 'Engin staðreynd núna.'
    return render_template('index.html', dog_image=image, dog_fact=fact, active='home', current_year=datetime.now().year)

@app.route('/blog')
def blog_list():
    q = request.args.get('q','').strip().lower()
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    posts = get_all_posts()
    if q:
        posts = [p for p in posts if q in p.get('title','').lower() or q in p.get('content','').lower()]
    total = len(posts)
    pages = ceil(total / per_page) if total>0 else 1
    start = (page-1)*per_page
    end = start + per_page
    page_posts = posts[start:end]
    return render_template('blog_list.html', posts=page_posts, page=page, pages=pages, q=q, active='blog')

@app.route('/post/<int:doc_id>')
def post_detail(doc_id):
    post = db.get(doc_id=doc_id)
    if not post:
        abort(404)
    return render_template('blog_post.html', post=post, active='blog')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == 'admin@admin.is' and password == '123456':
            session['user'] = 'admin'
            flash('Velkomin(n), admin', 'success')
            return redirect(url_for('admin_dashboard'))

  
        user = users_db.get(Query().email == email)
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            flash(f'Innskráning tókst, {email}!', 'success')
            return redirect(url_for('index'))

        flash('Rangt netfang eða lykilorð', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Útskráning tókst', 'success')
    return redirect(url_for('index'))

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash('Þú þarft að skrá þig inn', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper

@app.route('/admin')
@login_required
def admin_dashboard():
    posts = get_all_posts()
    return render_template('admin_dashboard.html', posts=posts, active='admin')

@app.route('/admin/new', methods=['GET','POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        content = request.form.get('content','').strip()
        category = request.form.get('category','').strip()
        if not title or not content:
            flash('Titill og efni má ekki vera tómt', 'danger')
            return redirect(url_for('new_post'))
        image_path = None
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = url_for('static', filename=f'uploads/{filename}')
        post = {
            'title': title,
            'content': content,
            'category': category,
            'image': image_path,
            'created': datetime.now().isoformat()
        }
        db.insert(post)
        flash('Færslu bætt við', 'success')
        return redirect(url_for('admin_dashboard'))
    all_categories = [c['name'] for c in categories_db.all()]
    return render_template('blog_form.html', action='new', post=None, categories=all_categories)


@app.route('/admin/edit/<int:doc_id>', methods=['GET','POST'])
@login_required
def edit_post(doc_id):
    post = db.get(doc_id=doc_id)
    if not post:
        flash('Færslan fannst ekki', 'danger')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        content = request.form.get('content','').strip()
        category = request.form.get('category','').strip()
        if not title or not content:
            flash('Titill og efni má ekki vera tómt', 'danger')
            return redirect(url_for('edit_post', doc_id=doc_id))
        file = request.files.get('image')
        image_path = post.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = url_for('static', filename=f'uploads/{filename}')
        db.update({'title': title, 'content': content, 'category': category, 'image': image_path}, doc_ids=[doc_id])
        flash('Færslu uppfært', 'success')
        return redirect(url_for('admin_dashboard'))
    all_categories = [c['name'] for c in categories_db.all()]
    return render_template('blog_form.html', action='edit', post=post, doc_id=doc_id, categories=all_categories)
  


@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        category_name = request.form['category_name'].strip()
        if category_name:
            categories_db.insert({'name': category_name})
            flash(f"Flokkur '{category_name}' hefur verið bætt við.", "success")
    all_categories = categories_db.all()
    return render_template('admin_categories.html', categories=all_categories, active='admin')

@app.route('/admin/categories/delete/<category_name>', methods=['POST'])
@login_required
def delete_category(category_name):
    Category = Query()
    categories_db.remove(Category.name == category_name)
    flash(f"Flokkur '{category_name}' hefur verið eytt.", "info")
    return redirect(url_for('manage_categories'))



@app.route('/category/<category_name>')
def category_page(category_name):
    Post = Query()
    posts = db.search(Post.category == category_name)

  

    images = get_dog_images(len(posts))
    return render_template('category.html', posts=posts, images=images, category_name=category_name)





@app.route('/admin/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_post(doc_id):
    db.remove(doc_ids=[doc_id])
    flash('Færslu eytt', 'success')
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404



if __name__ == '__main__':
    app.run(debug=True)
