from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from bs4 import BeautifulSoup
import base64
import requests
import json
from urllib.parse import urlparse, parse_qs, quote, unquote
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



app = Flask(__name__, template_folder='.')
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://Shopaffordable:harrypotter12@Shopaffordable.mysql.pythonanywhere-services.com/Shopaffordable$user_auth'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

SERP_API_KEY = '3936cf1352ad8dbbf546aeceeafc35c38f2ed9b24b0f92916b98d2e9d0f3145f'


db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    shop_id = db.Column(db.Integer, nullable=True)
    # No foreign key to shops here
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.phone_number}')"

class Shop(db.Model):
    __tablename__ = 'shops'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Foreign key to reference the User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Define the relationship to User
    user = db.relationship('User', backref='shops', lazy=True)

    def __repr__(self):
        return f"Shop('{self.name}', '{self.address}')"
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    image = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"Product('{self.name}', '{self.price}')"

def remove_plural_suffix(text):
    return re.sub(r's$', '', text)

@app.route('/test_connection')
def test_connection():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")  # Simple query to test connection
        cur.close()
        return "Connection successful!"
    except Exception as e:
        return f"Connection failed: {str(e)}"

@app.route('/register_shop')
def register_shop():
    return render_template('register_shop.html')

@app.route('/create_shop', methods=['POST'])
def create_shop():
    shop_name = request.form.get('shop_name')
    address = request.form.get('address')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # Ensure the user is logged in and retrieve their ID
    if 'user_id' not in session:
        flash('You must be logged in to create a shop.', 'error')
        return redirect(url_for('show_login_page'))

    user_id = session['user_id']  # Get the logged-in user's ID

    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        flash('User  not found.', 'error')
        return redirect(url_for('show_login_page'))

    # Validate input data
    if not shop_name or not address:
        flash('Shop name and address are required.', 'error')
        return redirect(url_for('register_shop'))

    # Validate latitude and longitude
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        flash('Invalid latitude or longitude value', 'error')
        return redirect(url_for('register_shop'))

    # Check if the user already has a shop
    existing_shop = Shop.query.filter_by(user_id=user_id).first()
    if existing_shop:
        flash('You already have a shop. Please update it instead.', 'error')
        return redirect(url_for('dashboard'))

    # Create the shop with the user_id
    shop = Shop(name=shop_name, address=address, latitude=latitude, longitude=longitude, user_id=user_id)
    db.session.add(shop)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash('Error creating shop: ' + str(e), 'error')
        return redirect(url_for('register_shop'))

    # Set the shop_id in the user's session
    session['shop_id'] = shop.id

    flash(f'Shop "{shop_name}" created successfully!', 'success')
    return redirect(url_for('dashboard'))

# @app.route('/create_shop', methods=['POST'])
# def create_shop():
#     shop_name = request.form['shop_name']
#     address = request.form['address']
#     latitude = request.form['latitude']
#     longitude = request.form['longitude']

#     # Ensure the user is logged in and retrieve their ID
#     if 'user_id' not in session:
#         flash('You must be logged in to create a shop.', 'error')
#         return redirect(url_for('show_login_page'))

#     user_id = session['user_id']  # Get the logged-in user's ID

#     # Check if the user exists
#     user = User.query.get(user_id)
#     if not user:
#         flash('User  not found.', 'error')
#         return redirect(url_for('show_login_page'))

#     # Validate latitude and longitude
#     try:
#         latitude = float(latitude)
#         longitude = float(longitude)
#     except ValueError:
#         flash('Invalid latitude or longitude value', 'error')
#         return redirect(url_for('register_shop'))

#     # Create the shop with the user_id
#     shop = Shop(name=shop_name, address=address, latitude=latitude, longitude=longitude, user_id=user_id)
#     db.session.add(shop)

#     try:
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()  # Rollback in case of error
#         flash('Error creating shop: ' + str(e), 'error')
#         return redirect(url_for('register_shop'))

#     # Set the shop_id in the user's session
#     session['shop_id'] = shop.id

#     flash('Shop created successfully!', 'success')
#     return redirect(url_for('dashboard'))



@app.route('/add_product', methods=['POST'])
def add_product():
    product_name = request.form['product_name']
    price = request.form['price']
    category = request.form['category']
    shop_id = session['shop_id']

    image = request.files['image']

    imgbb_url = 'https://api.imgbb.com/1/upload'
    imgbb_params = {
        'key': 'c3538ee992f52e3ddd0b8be637275e31'
    }
    files = {'image': image}
    response = requests.post(imgbb_url, params=imgbb_params, files=files)

    if response.status_code == 200:
        try:
            image_url = response.json()['data']['url']
        except KeyError:
            flash('Error uploading image to imgbb', 'error')
            return redirect(url_for('dashboard'))
    else:
        flash('Error uploading image to imgbb', 'error')
        return redirect(url_for('dashboard'))

    product = Product(name=product_name, price=price, category=category, shop_id=shop_id, image=image_url)
    db.session.add(product)
    db.session.commit()

    flash('Product added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def show_login_page():
    # if request.method == 'POST':
    #     return login_user()
    return render_template('index_login.html')


@app.route('/login_user', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()

    # if user and check_password_hash(user.password, password):
    #     session['logged_in'] = True
    #     session['user_id'] = user.id
    #     session['email'] = user.email
    #     session['username'] = user.username
    #     # session['shop_id'] = user.shop_id  # This should now work if shop_id is in User model
    # if user and check_password_hash(user[4], password):
    #     session['logged_in'] = True
    #     session['user_id'] = user[0]
    #     session['email'] = user[2]
    #     session['username'] = user[1]  # Set the username key in the session dictionary
    #      # Check if the user has a shop
    #     cur = mysql.connection.cursor()
    #     cur.execute("SELECT shop_id FROM users WHERE id = %s", (session['user_id'],))
    #     shop_id = cur.fetchone()
    #     cur.close()


    #     session['shop_id'] = shop_id[0]

    if user and check_password_hash(user.password, password):  # Adjust based on your model attribute
        session['logged_in'] = True
        session['user_id'] = user.id
        session['email'] = user.email
        session['username'] = user.username  # Set the username key in the session dictionary
        session['shop_id']= user.shop_id
        # print("Shop ID set in session:", session['shop_id'])


        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials. Please try again.', 'danger')

    return redirect(url_for('show_login_page'))

# @app.route('/login_user', methods=['POST'])
# def login_user():
#     email = request.form['email']
#     password = request.form['password']
#     # print("hola")
#     # print(f"Email: {email}, Password: {password}")
#     user = User.query.filter_by(email=email).first()

#     if user and check_password_hash(user.password, password):
#         session['logged_in'] = True
#         session['user_id'] = user.id
#         session['email'] = user.email
#         session['username'] = user.username
#         shop_id = user.shop_id
#         session['shop_id'] = shop_id
#         flash('Login successful!', 'success')
#         return redirect(url_for('dashboard'))
#     else:
#         flash('Invalid credentials. Please try again.', 'danger')

#     return redirect(url_for('show_login_page'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        if request.args.get('show_profile') == 'true':
            session['show_profile'] = True
            return render_template('dash.html', username=session['username'], show_profile=session['show_profile'])
        elif request.args.get('show_shop') == 'true':
            session['show_shop'] = True
            products = Product.query.filter_by(shop_id=session['shop_id']).all()
            return render_template('dash.html', username=session['username'], products=products, show_shop=session['show_shop'])
        elif request.args.get('add_product') == 'true':
            session['add_product'] = True
            return render_template('dash.html', username=session['username'], add_product=session['add_product'])
        elif request.args.get('show_analytics') == 'true':
            session['show_analytics'] = True
            return render_template('dash.html', username=session['username'], show_analytics=session['show_analytics'])
        else:
            session.pop('show_profile', None)
            session.pop('show_shop', None)
            user = User.query.filter_by(username=session['username']).first()
            session['email'] = user.email
            session['phone_number'] = user.phone_number

            # Check if shop_id exists in the session
            shop_id = session.get('shop_id')

            products = []
            # if shop_id:  # Check if shop_id is not None or empty
            products = Product.query.filter_by(shop_id=shop_id).all()
            return render_template('dash.html', username=session['username'], products=products, shop_id=session.get('shop_id'))
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('show_login_page'))

# @app.route('/dashboard')
# def dashboard():
#     if 'logged_in' in session:
#         if request.args.get('show_profile') == 'true':
#             session['show_profile'] = True
#             return render_template('dash.html', username=session['username'], show_profile=session['show_profile'])
#         elif request.args.get('show_shop') == 'true':
#             session['show_shop'] = True
#             products = Product.query.filter_by(shop_id=session['shop_id']).all()
#             return render_template('dash.html', username=session['username'], products=products, show_shop=session['show_shop'])
#         elif request.args.get('add_product') == 'true':
#             session['add_product'] = True
#             return render_template('dash.html', username=session['username'], add_product=session['add_product'])
#         else:
#             session.pop('show_profile', None)
#             session.pop('show_shop', None)
#             user = User.query.filter_by(username=session['username']).first()
#             session['email'] = user.email
#             session['phone_number'] = user.phone_number
#             # shop_id = session['shop_id']
#             products = Product.query.filter_by(shop_id=session['shop_id']).all()
#             return render_template('dash.html', username=session['username'], products=products)
#     else:
#         flash('Please log in to access the dashboard.', 'warning')
#         return redirect(url_for('show_login_page'))

@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'logged_in' in session:
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']

        user = User.query.filter_by(username=session['username']).first()
        user.username = username
        user.email = email
        user.phone_number = phone_number
        db.session.commit()

        session['username'] = username
        session['email'] = email
        session['phone_number'] = phone_number

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('show_login_page'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('show_login_page'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number'][:10]
        password = generate_password_hash(request.form['password'])

        user = User(username=username, email=email, phone_number=phone_number, password=password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('show_login_page'))
    return render_template('index_login.html')

def get_product_link(product_name, price, seller):
    api_key = "3936cf1352ad8dbbf546aeceeafc35c38f2ed9b24b0f92916b98d2e9d0f3145f"
    url = f"https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "hl": "en",
        "gl": "in",
        "api_key": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    product_link = None
    if 'shopping_results' in data:
        for item in data['shopping_results']:
            if item['title'].lower() == product_name.lower() and item['price'] == price and item['source'].lower() == seller.lower():
                product_link = item['product_link']
                break
    if product_link is None:
        print(f"Product link not found for {product_name} with price {price} and seller {seller}")
        print("Trying to find product link using Google search...")
        url = f"https://www.google.com/search?q={product_name}+{seller}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        for link in links:
            if link.get('href') and 'www.google.com' not in link.get('href'):
                product_link = link.get('href')
                break
    if product_link and 'www.google.com/shopping/product' in product_link:
        url = product_link
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        for link in links:
            if link.get('href') and 'Visit site' in link.text:
                product_link = link.get('href')
                break
    if product_link and 'url?q=' in product_link:
        product_link = product_link.split('url?q=')[1].split('&opi')[0]
        product_link = product_link.split('?')[0]
        product_link = product_link.split('%3F')[0]
    return product_link

def get_product_website_link(product_link):
    parsed_url = urlparse(product_link)
    query_params = parse_qs(parsed_url.query)

    product_id = None
    if 'prds' in query_params:
        product_id = query_params['prds'][0].split(':')[1]

    if product_id:
        website_link = f"https://www.google.com/shopping/product/{product_id}"
    else:
        website_link = product_link

    return website_link

def get_product_info(product_id):
    api_key = "YOUR_API_KEY"
    url = f"https://www.googleapis.com/shopping/search/v1/public/products/{product_id}?key={api_key}"
    response = requests.get(url)
    data = response.json()

    product_url = data['item']['link']

    return product_url

def get_products_by_category(category):
    url = f"https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": category,
        "hl": "en",
        "gl": "in",
        "api_key": SERP_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    products = []
    if 'shopping_results' in data:
        for item in data['shopping_results']:
            product = {
                'id': item.get('id', ''),
                'title': item.get('title', ''),
                'price': item.get('price', ''),
                'image': item.get('thumbnail', ''),
                'link': item.get('product_link', ''),
                'seller': item.get('source', '')
            }
            products.append(product)
    return products

# @app.route('/category/<category_name>')
# def category(category_name):
#     query = category_name
#     query = remove_plural_suffix(query.lower())
#     print(f"Search query received: {query}")

#     product_from_database = Product.query.filter(Product.category.like(f'%{query}%')).all()

#     if product_from_database:
#         shop_id = product_from_database.shop_id
#         shop = Shop.query.filter_by(id=shop_id).first()
#         if shop:
#             shop_name = shop.name
#         else:
#             shop_name = "Unknown Shop"
#     else:
#         shop_name = "Product not found in database"

#     products = get_products_by_category(category_name)
#     return render_template('results_cat.html', category=category_name, products=products, product_from_database=product_from_database, shop_name=shop_name)


@app.route('/category/<category_name>')
def category(category_name):
    query = remove_plural_suffix(category_name.lower())
    print(f"Search query received: {query}")

    products_from_database = Product.query.filter(Product.category.like(f'%{query}%')).all()

    # Create a dictionary to hold shop names for products found in the database
    shop_names = {}
    if products_from_database:
        # for product in products_from_database:
            # Get unique shop IDs from the products
        shop_ids = {product.shop_id for product in products_from_database}  # Set comprehension for unique shop IDs

            # Retrieve shops for those products in one query
        shops = Shop.query.filter(Shop.id.in_(shop_ids)).all()

            # Create a mapping of shop IDs to shop names
        shop_names = {shop.id: shop.name for shop in shops}

    else:
        shop_names = {}

    products = get_products_by_category(category_name)  # Assuming this function retrieves products from ONDC
    return render_template('results_cat.html', category=category_name, products=products, products_from_database=products_from_database, shop_names=shop_names)


@app.route('/api/comparison/<product_name>')
def comparison(product_name):
    product_name = unquote(product_name)
    product_name = product_name.replace('/', ' ')

    url = f"https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "hl": "en",
        "gl": "in",
        "api_key": SERP_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    comparison_data = []
    if 'shopping_results' in data:
        for item in data['shopping_results']:
            comparison_item = {
                'title': item['title'],
                'price': item['price'],
                'image': item['thumbnail'],
                'link': item['product_link'],
                'seller': item.get('source', ''),
                'link2': get_product_website_link(item['product_link'])
            }
            comparison_data.append(comparison_item)
    return jsonify(comparison_data)

@app.route('/api/get_product_link', methods=['POST'])
def get_product_link_api():
    data = request.get_json()
    product_name = data['product_name']
    price = data['price']
    seller = data['seller']
    product_link = get_product_link(product_name, price, seller)
    return jsonify({'product_link': product_link})

@app.route('/search')
def search():
    query = request.args.get('query')
    query = remove_plural_suffix(query.lower())
    print(f"Search query received: {query}")

    # Retrieve products from the database that match the search query
    products_from_database = Product.query.filter(Product.name.like(f'%{query}%')).all()

    # Create a dictionary to hold shop names for products found in the database
    if products_from_database:
        # for product in products_from_database:
            # Get unique shop IDs from the products
        shop_ids = {product.shop_id for product in products_from_database}  # Set comprehension for unique shop IDs

            # Retrieve shops for those products in one query
        shops = Shop.query.filter(Shop.id.in_(shop_ids)).all()

            # Create a mapping of shop IDs to shop names
        shop_names = {shop.id: shop.name for shop in shops}

    else:
        shop_names = {}

    api_key = "3936cf1352ad8dbbf546aeceeafc35c38f2ed9b24b0f92916b98d2e9d0f3145f"
    params = {
        "engine": "google_shopping",
        "q": query,
        "hl": "en",
        "gl": "in",
        "api_key": api_key
    }
    url = "https://serpapi.com/search.json"
    response = requests.get(url, params=params)
    data = response.json()
    products = []
    if 'shopping_results' in data:
        for item in data['shopping_results']:
            product = {
                'title': item.get('title', ''),
                'price': item.get('price', ''),
                'image': item.get('thumbnail', ''),
                'link': item.get('product_link', ''),
                'seller': item.get('source', '')
            }
            products.append(product)

    # Render the results template with both database and API products
    return render_template('results.html',
                           products=products,
                           products_from_database=products_from_database,
                           shop_names=shop_names)

# @app.route('/search')
# def search():
#     query = request.args.get('query')
#     query = remove_plural_suffix(query.lower())
#     print(f"Search query received: {query}")

#     products_from_database = Product.query.filter(Product.name.like(f'%{query}%')).all()

#     if product_from_database:
#         shop_id = product_from_database.shop_id
#         shop = Shop.query.filter_by(id=shop_id).first()
#         if shop:
#             shop_name = shop.name
#         else:
#             shop_name = "Unknown Shop"
#     else:
#         shop_name = "Product not found in database"

#     api_key = "3936cf1352ad8dbbf546aeceeafc35c38f2ed9b24b0f92916b98d2e9d0f3145f"
#     params = {
#         "engine": "google_shopping",
#         "q": query,
#         "hl": "en",
#         "gl": "in",
#         "api_key": api_key
#     }
#     url = "https://serpapi.com/search.json"
#     response = requests.get(url, params=params)
#     data = response.json()
#     products = []
#     if 'shopping_results' in data:
#         for item in data['shopping_results']:
#             product = {
#                 'title': item.get('title', ''),
#                 'price': item.get('price', ''),
#                 'image': item.get('thumbnail', ''),
#                 'link': item.get('product_link', ''),
#                 'seller': item.get('source', '')
#             }
#             products.append(product)
#     return render_template('results.html', products=products, product_from_database=product_from_database, shop_name=shop_name)


@app.route('/')
def main():
    if 'username' in session:
        username = session['username']
        return render_template('main.html', username=username)
    else:
        return render_template('main.html')

# @app.route('/product')
# def product():
#     product_name = request.args.get('name')
#     product_price = request.args.get('price')
#     product_seller = request.args.get('seller')
#     product_image = request.args.get('image')

#     return render_template('product.html',
#                           name=product_name,
#                           price=product_price,
#                           seller=product_seller,
#                           image=product_image)
