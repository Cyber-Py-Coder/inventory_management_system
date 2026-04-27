from flask import Flask, session, redirect, render_template, flash, request, url_for, jsonify, request
import mysql.connector
import os

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
    elif 'emp_id' in session:
        return redirect(url_for("Employee_dashboard"))
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
    
    cursor=mydb.cursor(dictionary=True)
    cursor.execute("select count(*) from products") #function for count all products 
    total=cursor.fetchone()

    cursor.execute('select count(*) from products where quantity<=5;') #function for low stock
    qty=cursor.fetchone()

    cursor.execute('select * from products where quantity<5')
    items=cursor.fetchall()

    cursor.execute('SELECT sum(sale_price) FROM sales WHERE DATE(sale_date) = CURDATE();') #functionn for today sale
    amount=cursor.fetchone()

    cursor.execute('select sum(sale_price) from sales') #function for total revenue
    revenue=cursor.fetchone()
    cursor.close()

    return render_template('dashboard.html', name=session['man_name'], items=items, total=total['count(*)'], qty=qty['count(*)'], amount=amount['sum(sale_price)'], revenue=revenue['sum(sale_price)'])

#sale page
@app.route('/sales')
def sales():
    if 'man_id' not in session:
        return redirect(url_for('home'))
    
    cursor=mydb.cursor(dictionary=True)
    cursor.execute('SELECT sum(sale_price) FROM sales WHERE DATE(sale_date) = CURDATE();') #functionn for today sales
    amount=cursor.fetchone()

    cursor.execute('SELECT count(*) FROM sales WHERE DATE(sale_date) = CURDATE();') #functionn for today orders
    today_order=cursor.fetchone()

    cursor.execute('SELECT count(*) FROM sales;') #function for totals orders
    total_order=cursor.fetchone()

    cursor.execute('select sum(sale_price) from sales') #function for total revenue
    revenue=cursor.fetchone()
    
    cursor.execute('select * from sales')
    items=cursor.fetchall()
    cursor.close()
    return render_template('sales.html', items=items ,revenue=revenue['sum(sale_price)'], today_sales=amount['sum(sale_price)'], total_orders=total_order['count(*)'],today_orders=today_order['count(*)'])

#add quantity page
@app.route('/add_quantity')
def quantity():
    if 'man_id' not in session:
        return redirect(url_for('home'))
    
    cursor=mydb.cursor(dictionary=True)
    cursor.execute('select * from products')
    items=cursor.fetchall()
    return render_template('add_qty.html', items=items)


@app.route('/add_qty', methods=['POST'])
def add_qty_post():
    if 'man_id' not in session:
        return redirect(url_for('home'))

    product_id = request.form['product_id']
    product_name = request.form['product_name']
    price = request.form['price']
    qty = int(request.form['qty'])

    cursor = mydb.cursor()
    # Update product quantity in database
    cursor.execute('UPDATE products SET quantity = quantity + %s WHERE id = %s', (qty, product_id))
    mydb.commit()

    flash(f"Added {qty} units to {product_name}", "success")
    return redirect(url_for('quantity'))  # redirect back to add quantity page


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
    
    cursor=mydb.cursor(dictionary=True)
    query='select * from products'
    cursor.execute(query)
    items=cursor.fetchall()
    return render_template('product_sale.html', items=items)

#sale item function
@app.route('/sale_item', methods=['GET', 'POST'])
def sale_item():
    if 'emp_id' not in session:
        return redirect(url_for('home'))

    product_id=request.form.get('product_id')
    qty=request.form.get('qty')
    product_name=request.form.get('product_name')
    price=request.form.get('price')

    cursor=mydb.cursor(dictionary=True)
    cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s AND quantity >= %s", (qty, product_id, qty))

    query='insert into sales (product_name, sale_price, product_id, qty) VALUES (%s, %s, %s, %s)'
    values=(product_name, price, product_id, qty)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()
    

    flash("Item sold successfully!", "success")
    return redirect(url_for('product_sale'))

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