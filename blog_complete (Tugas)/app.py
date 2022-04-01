from distutils.log import error
from msilib.schema import Error
from flask import (
    Flask, request, render_template, session, flash, redirect, url_for, jsonify
)
import pymysql
import re

from db import db_connection


app = Flask(__name__)
app.secret_key = 'THISISMYSECRETKEY'  # create the unique one for yourself




@app.route('/sign', methods=['GET','POST']) #Ini def sign nya codenya gw copy dari login karena menurut gw mirip mirip pasti
def sign():
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'name' in request.form:
        # variable doang, no use cu
        username = request.form['usernameReg']
        password = request.form['password']
        name = request.form['nameReg']
    elif request.method == 'POST':
        username = request.form['usernameReg']
        password = request.form['password']
        name = request.form['nameReg']
        # Kalo form kosong ini, ini msg nya
        msg = 'Please fill out the form!'
        #Mulai disini
        cursor = db_connection()
        con = cursor.cursor()
        con.execute('SELECT * FROM users WHERE username = %s', (username)) #Biar ga error kalo ada username yg sama
        account = con.fetchone()
        if account:
            msg = 'Account already exists!'
            flash(msg)
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
            flash(msg)
        elif len(password) < 5:
            msg = 'Make sure your password is at lest 5 letters'
            flash(msg)
        elif re.search('[A-Z]',password) is None:
            msg = 'Make sure your password has a 1 capital letter in it'
            flash(msg)
        elif not username or not password:
            msg = 'Please fill out the form!'
            flash(msg)
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            con.execute('INSERT INTO users (username,password,name) VALUES ( %s, %s,%s)', (username, password,name))
            cursor.commit()
            msg = 'You have successfully registered!'
            flash(msg)
            return redirect(url_for('login'))
    return render_template('sign.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ function to show and process login page """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = db_connection()
        cur = conn.cursor()
        sql = """
            SELECT id, username
            FROM users
            WHERE username = '%s' AND password = '%s'
        """ % (username, password)
        cur.execute(sql)
        user = cur.fetchone()

        error = ''
        if user is None:
            error = 'Wrong credentials. No user found'
        else:
            session.clear()
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))

        flash(error)
        cur.close()
        conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    """ function to do logout """
    session.clear()  # clear all sessions
    return redirect(url_for('login'))


@app.route('/')
def index():
    conn = db_connection()
    cur = conn.cursor()
    sql = """
        SELECT art.id, art.title, art.body
        FROM articles art
        ORDER BY art.title
    """
    cur.execute(sql)
    # [(1, "Article Title 1", "Art 1 content"), (2, "Title2", "Content 2"), ...]
    articles = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', articles=articles)


@app.route('/article/create', methods=['GET', 'POST'])
def create():
    # check if user is logged in
    if not session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json() or {}
        # check existence of title and body
        if data.get('title') and data.get('body'):
            title = data.get('title', '')
            body = data.get('body', '')
            user_id = session.get('user_id')

            # strip() is to remove excessive whitespaces before saving
            title = title.strip()
            body = body.strip()

            conn = db_connection()
            cur = conn.cursor()
            # insert with the user_id
            sql = """
                INSERT INTO articles (title, body, user_id) VALUES ('%s', '%s', %d)
            """ % (title, body, user_id)
            cur.execute(sql)
            conn.commit()  # commit to make sure changes are saved
            cur.close()
            conn.close()
            # an example with redirect
            return jsonify({'status': 200, 'message': 'Success', 'redirect': '/'})

        # else will be error
        return jsonify({'status': 500, 'message': 'No Data submitted'})

    return render_template('create.html')


@app.route('/article/<int:article_id>', methods=['GET'])
def read(article_id):
    # find the article with id = article_id, return not found page if error
    conn = db_connection()
    cur = conn.cursor()
    sql = """
        SELECT art.title, art.body, usr.name
        FROM articles art
        JOIN users usr ON usr.id = art.user_id
        WHERE art.id = %s
    """ % article_id
    cur.execute(sql)
    article = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('detail.html', article=article)


@app.route('/article/edit/<int:article_id>', methods=['GET', 'POST'])
def edit(article_id):
    # check if user is logged in
    if not session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        conn = db_connection()
        cur = conn.cursor()
        title = request.form['title']
        body = request.form['body']
        title = title.strip()
        body = body.strip()

        sql_params = (title, body, article_id)

        sql = "UPDATE articles SET title = '%s', body = '%s' WHERE id = %s" % sql_params
        print(sql)
        cur.execute(sql)
        cur.close()
        conn.commit()
        conn.close()
        # use redirect to go to certain url. url_for function accepts the
        # function name of the URL which is function index() in this case
        return redirect(url_for('index'))

    # find the record first
    conn = db_connection()
    cur = conn.cursor()
    sql = 'SELECT id, title, body FROM articles WHERE id = %s' % article_id
    cur.execute(sql)
    article = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('edit.html', article=article)


@app.route('/article/delete/<int:article_id>', methods=['GET', 'POST'])
def delete(article_id):
    # check if user is logged in
    if not session:
        return redirect(url_for('login'))

    conn = db_connection()
    cur = conn.cursor()
    sql = 'DELETE FROM articles WHERE id = %s' % article_id
    cur.execute(sql)
    cur.close()
    conn.commit()
    conn.close()
    return jsonify({'status': 200, 'redirect': '/'})
