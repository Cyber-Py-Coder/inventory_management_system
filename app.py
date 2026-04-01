from flask import Flask, session, redirect, render_template, flash, request, url_for
import mysql.connector

app=Flask(__name__)

mydb=mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='inventory'
)

app.secret_key="Top secrets"

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def home():
    if "man_id" in session:
        return redirect(url_for('manager_dashboard'))
    return render_template("login.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    cursor = mydb.cursor(dictionary=True)

    query = 'SELECT username, password, role, name FROM user WHERE username=%s AND password=%s'
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    if user:
        if user['role'] == 'manager':
            session['man_id'] = user['username']
            session['man_name'] = user['name']
            return redirect(url_for('manager_dashboard'))

        elif user['role'] == 'employee':
            session['emp_id'] = user['username']
            session['emp_name'] = user['name']
            return redirect(url_for('Employee_dashboard'))
    cursor.close()
    flash("Invalid credentials")
    return redirect(url_for('home'))

@app.route('/Manager_dashboard')
def manager_dashboard():
    if 'man_id' not in session:
        return redirect(url_for('home'))  
    return render_template('dashboard.html', name=session['man_name'])


#add product page
@app.route('/product_add_page')
def product_add_page():
    if "man_id" not in session:
        return redirect(url_for('home'))
    return render_template('add_product.html')

#adding products in inventory
@app.route('/add_product', methods=['POST', 'GET'])
def add_product():
    if "man_id" not in session:
        return redirect(url_for('home'))
    
    Product_name=request.form.get("Product_name")
    price=request.form.get('price')
    quantity=request.form.get('quantity')
    category=request.form.get('category')
    section=request.form.get('Section')

    cursor = mydb.cursor(dictionary=True)
    query='insert into products (product_name, quantity, price, category, section ) values(%s, %s, %s, %s, %s)'
    values=(Product_name, quantity, price, category, section)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()

    flash ("add Product successfully")
    return redirect(url_for('product_add_page'))

#product page and product view function--------------------
@app.route('/product')
def product():
    if "man_id" not in session:
        return redirect(url_for('home'))
    
    cursor=mydb.cursor(dictionary=True)
    query='select product_name, price, quantity, section from products'
    cursor.execute(query)
    items=cursor.fetchall()
    cursor.close()
    return render_template('products.html', items=items)

#employee dashboard with product view function----------------
@app.route('/Employee_dashboard')
def Employee_dashboard():
    if 'emp_id' not in session:
        return redirect(url_for('home'))
    
    cursor=mydb.cursor(dictionary=True)
    query='select * from products'
    cursor.execute(query)
    items=cursor.fetchall()
    return render_template('Employee_Dashboard.html', name=session['emp_name'], items=items )

#product sale page
@app.route('/product_sale')
def product_sale():
    if "emp_id" not in session:
        return redirect(url_for('home'))
    return render_template('product_sale.html')

#------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('home'))
    response.headers['Cache-Control'] = 'no-store'
    return response

#------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)