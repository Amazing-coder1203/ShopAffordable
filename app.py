from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify


from bs4 import BeautifulSoup

import requests
import json
from urllib.parse import urlparse, parse_qs, quote, unquote

from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__, template_folder='.')
app.secret_key = 'your_secret_key'

SERP_API_KEY = '87ca5cb4761370c51ac33a16ccffb29b424b5f61bb392b103cb0d1151a0a31d5'


# Fetch products based on a category
# def get_products_by_category(category):
#     url = f"https://serpapi.com/search.json"
#     params = {
#         "engine": "google_shopping",
#         "q": category,
#         "hl": "en",
#         "gl": "in",
#         "api_key": SERP_API_KEY
#     }
#     response = requests.get(url, params=params)
#     data = response.json()
    
#     # Extract product information
#     products = []
#     if 'shopping_results' in data:
#         for item in data['shopping_results']:
#             product = {
#                 'name': item.get('title', 'No Name'),
#                 'price': item.get('price', 'No Price'),
#                 'image': item.get('thumbnail', ''),
#                 'link': item.get('product_link', '#'),
#                 'seller': item.get('source', 'No Seller')
#             }
#             products.append(product)
#     return products

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'harrypotter'
app.config['MYSQL_DB'] = 'user_auth'

mysql = MySQL(app)



# @app.route('/User', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
        
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM users WHERE email = %s", (email,))
#         user = cur.fetchone()
#         cur.close()
        
#         if user and check_password_hash(user[3], password):  # Password is in the 3rd column
#             session['logged_in'] = True
#             session['username'] = user[1]  # Username is in the 1st column
#             flash('Login successful!', 'success')
#             return redirect(url_for('dashboard'))
#         else:
#             flash('Invalid credentials. Please try again.', 'danger')
#     return render_template('index_login.html')  # Login form is in index_login.html

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = generate_password_hash(request.form['password'])
        
#         cur = mysql.connection.cursor()
#         cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
#         mysql.connection.commit()
#         cur.close()
        
#         flash('Registration successful! Please log in.', 'success')
#         return redirect(url_for('login'))
#     return render_template('index_login.html')  # Add a registration form to index_login.html


# Function to render the login page
@app.route('/shopaffordable.netlify.app/login', methods=['GET'])
def show_login_page():
    return render_template('index_login.html')  # Render the login form

# Function to handle login form submission and redirect to dashboard if password is correct
@app.route('/shopaffordable.netlify.app/login', methods=['POST'])
def handle_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Fetch user from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        # if user:
        #     print("User  found:", user)
        #     print("Stored hashed password:", user[4])  # Assuming password is in the 4th column
        #     print("Plain-text password from form:", password)
        #     print("Password comparison result:", check_password_hash(user[3], password))
        
        # Check if the user exists and the password is correct
        if user and check_password_hash(user[4], password):  # Assuming password is in the 4th column
            session['logged_in'] = True
            session['username'] = user[1]  # Assuming username is in the 2nd column
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to the dashboard
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            print("wrong")
            return redirect(url_for('show_login_page'))  # Redirect back to the login page

# Function to render the dashboard
@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:  # Check if the user is logged in
        if request.args.get('show_profile') == 'true':
            session['show_profile'] = True
        else:
            session.pop('show_profile', None)
         # Fetch user data from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (session['username'],))
        user_data = cur.fetchone()
        cur.close()
        
        # Store user data in the session
        session['email'] = user_data[2]
        session['phone_number'] = user_data[3]
        return render_template('dash.html', username=session['username'])
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('show_login_page'))  # Redirect to the login page if not logged in
@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'logged_in' in session:  # Check if the user is logged in
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        
        # Update user data in the database
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET username = %s, email = %s, phone_number = %s WHERE username = %s", (username, email, phone_number, session['username']))
        mysql.connection.commit()
        cur.close()
        
        # Update session variables
        session['username'] = username
        session['email'] = email
        session['phone_number'] = phone_number
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('show_login_page'))  # Redirect to the login page if not logged in

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('show_login_page'))  # Redirect to the login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number'][:10]
        password = generate_password_hash(request.form['password'])
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, phone_number, password) VALUES (%s, %s, %s, %s)", (username, email, phone_number, password))
        mysql.connection.commit()
        cur.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('show_login_page'))
    return render_template('index_login.html')  # Add a registration form to index_login.html


def get_product_link(product_name, price, seller):
    api_key = "87ca5cb4761370c51ac33a16ccffb29b424b5f61bb392b103cb0d1151a0a31d5"
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
    # Extract the product ID from the URL
    parsed_url = urlparse(product_link)
    query_params = parse_qs(parsed_url.query)

    # Get the product ID
    product_id = None
    if 'prds' in query_params:
        product_id = query_params['prds'][0].split(':')[1]

    # Construct the new URL
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

    # Get the product URL
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
                'id': item.get('id', ''),  # Use get() to provide a default value if 'id' key does not exist
                'title': item.get('title', ''),
                'price': item.get('price', ''),
                'image': item.get('thumbnail', ''),
                'link': item.get('product_link', ''),
                'seller': item.get('source', '')
            }
            products.append(product)
    return products

@app.route('/category/<category_name>')
def category(category_name):
    # Fetch products for the given category
    products = get_products_by_category(category_name)
    return render_template('results_cat.html', category=category_name, products=products)


# Home route that serves the main page
@app.route('/shopaffordable.netlify.app')
def main():

    if 'username' in session:  # Check if 'username' exists in the session
        username = session['username']  # Get the username from the session
        return render_template('main.html', username=username)
    else:
        # flash('Please log in to access this page.', 'warning')
        return render_template('main.html') # Redirect to the login page
# @app.route('/shopaffordable.netlify.app')
# def main():
#     return render_template('main.html')


# @app.route('/shopaffordable.netlify.app/login')
# def login():
#     return render_template('index_login.html')

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
                'image': item['thumbnail'],  # Add this line to include the image URL
                'link': item['product_link'],
                'seller': item.get('source', ''),
                'link2': get_product_website_link(item['product_link'])  # Get the exact product link
                # 'website_link': item['product_link'].split('&')[0]
            }
             # Check if the link points to Google Shopping; if so, use fallback
            # if "google.com/shopping" in comparison_item['link2']:
            #     comparison_item['link2'] = item.get('link2', '#')  # Try to get a better link
            comparison_data.append(comparison_item)
    return jsonify(comparison_data)
# Search route that fetches product data and shows results
@app.route('/api/get_product_link', methods=['POST'])
def get_product_link_api():
    data = request.get_json()
    product_name = data['product_name']
    price = data['price']
    seller = data['seller']
    product_link = get_product_link(product_name, price, seller)
    return jsonify({'product_link': product_link})
@app.route('/shopaffordable.netlify.app/search')
def search():
    query = request.args.get('query')  # Get the query from the search form
    print(f"Search query received: {query}")  # Debugging output

    api_key = "87ca5cb4761370c51ac33a16ccffb29b424b5f61bb392b103cb0d1151a0a31d5"  # Replace with your SerpApi key
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
                'image': item.get('thumbnail', ''),  # Check if the image URL is being passed correctly
                'link': item.get('product_link', ''),
                'seller': item.get('source', '')
            }
            products.append(product)
    return render_template('results.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)

















# if __name__ == '__main__':
#     app.run(debug=True)


# from flask import Flask, request, render_template
# import os
# import requests

# app = Flask(__name__, template_folder='.')

# SERP_API_KEY = '87ca5cb4761370c51ac33a16ccffb29b424b5f61bb392b103cb0d1151a0a31d5'


# def get_products_by_category(category):
#     url = f"https://serpapi.com/search?q={category}&tbm=shop&api_key={SERP_API_KEY}"
#     response = requests.get(url)
#     data = response.json()
    
#     # Example: Extract the product info from the API response
#     products = []
#     if 'shopping_results' in data:
#         for item in data['shopping_results']:
#             product = {
#                 'name': item.get('title', 'No Name'),
#                 'price': item.get('price', 'No Price'),
#                 'image': item.get('thumbnail', ''),
#                 'link': item.get('link', '#')
#             }
#             products.append(product)
    
#     return products

# @app.route('/category/<category_name>')
# def category(category_name):
#     products = get_products_by_category(category_name)
#     return render_template('results_cat.html', category=category_name, products=products)






# # Home route that serves the search form
# @app.route('/')
# def main1():
#     return render_template('main.html')
# @app.route('/shopaffordable.netlify.app')
# def main():
#     return render_template('main.html')  # Render main.html from the same folder
# @app.route('/shopaffordable.netlify.app/login')
# def login():
#     return render_template('index_login.html')  # Render main.html from the same folder
# # Search route that fetches product data and shows results



