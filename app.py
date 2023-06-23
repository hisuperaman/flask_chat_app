from flask import Flask, request, redirect, render_template, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import random, os
from datetime import datetime
# import pytz
from pytz import timezone
# import tzlocal
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

app.config['SECRET_KEY'] = 'ajdfklje!'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = "filesystem"

Session(app=app)

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///appdata.db"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

db = SQLAlchemy(app=app)

class pending_approvals(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

class app_admins(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

class logininfo(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    chats = db.relationship('chats', backref='logininfo', lazy=True)

class chats(db.Model):
    msgid = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('logininfo.uid'),
        nullable=False)
    username = db.Column(db.String, nullable=False)
    msg = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.String, nullable=False)

# def datetimefilter(value, format="%Y-%m-%d %H:%M:%S"):
#     tz = pytz.timezone('Asia/Kolkata') # timezone you want to convert to from UTC
#     utc = pytz.timezone('UTC')
#     value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
#     local_dt = value.astimezone(tz)
#     return local_dt.strftime(format)

# app.jinja_env.filters['datetimefilter'] = datetimefilter

@app.route('/')
def index():
    if session.get('uid'):
        return redirect('/home')
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if app_admins.query.filter_by(uid=1111).first()==None:
        admin_password = "#Aman433"
        app_admins.query.delete()
        db.session.commit()
        onlyadmin = app_admins(uid=1111, firstname='Aman', lastname='Kumar', username='aman', password=admin_password)
        db.session.add(onlyadmin)
        db.session.commit()

        logininfo.query.delete()
        db.session.commit()
        admin = logininfo(uid=1111, firstname='Aman', lastname='Kumar', username='aman', password=admin_password)
        db.session.add(admin)
        db.session.commit()

    if request.method=='POST':
        form = request.form
        username = form['username'].lower()
        usr_passsword = form['password']

        usernames = [i[0] for i in db.session.query(logininfo.username)]
        pending_usernames = [i[0] for i in db.session.query(pending_approvals.username)]
        users = logininfo.query.all()

        if username in pending_usernames:
            res = "Your registration is not approved yet!"
            return render_template('login.html', res=res)
        else:
            if username in usernames:
                for user in users:
                    if username==user.username:

                        if user.password==usr_passsword:
                            session['uid'] = user.uid
                        else:
                            res = "Incorrect password"
                            return render_template('login.html', res=res)
            else:
                res = "Username not found. Please register yourself before logging in!"
                return render_template('login.html', res=res)

    if session.get('uid'):
        return redirect('/home')

    return render_template('login.html')

@app.route('/home')
def home():
    if session.get('uid'):
        msgs = chats.query.all()
        admin = app_admins.query.filter_by(uid=1111).first()
        logged_usr = logininfo.query.filter_by(uid=session['uid']).first()
        current_msg = chats.query.filter_by(uid=session['uid']).order_by(chats.timestamp.desc()).first()
        return render_template('app_home.html', msgs=msgs, admin=admin, logged_usr=logged_usr, current_msg=current_msg)

    return redirect('/login')

@app.route('/logout', methods=['GET','POST'])
def logout():
    if session.get('uid'):
        session.clear()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        form = request.form
        username = form['username'].strip().lower()
        firstname = form['fname'].strip()
        lastname = form['lname'].strip()
        tpassword = form['tpassword'].strip()
        password = form['password'].strip()
        uids = [i[0] for i in db.session.query(logininfo.uid)]
        usernames = [i[0] for i in db.session.query(logininfo.username)]

        if tpassword!=password:
            res = "Password does not match with confirm password"
            return render_template('register.html', res=res)

        if username in usernames:
            res = 'Username already exists'
            return render_template('register.html', res=res)

        c = 0
        while True:
            if c>=100:
                uid = 9999
                break
            c += 1
            newuid = random.randint(1000, 9999)
            if newuid in uids:
                continue
            break
        try:
            user = pending_approvals(uid=newuid, firstname=firstname, lastname=lastname, username=username, password=password)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            res = "Some error occured"
            return render_template('register.html', res=res)
        return redirect('/login')

    return render_template('register.html')

@app.route('/admin')
def admin():
    if session.get('uid'):
        admin = app_admins.query.filter_by(uid=session['uid']).first()
        if admin is not None:
            users = pending_approvals.query.all()
            return render_template('/admin.html', users=users)
    return redirect('/login')

@app.route('/accept/<uid>', methods=['GET', 'POST'])
def accept(uid):
    if request.method=='POST':
        req_user = pending_approvals.query.filter_by(uid=uid).first()
        user = logininfo(uid=req_user.uid, firstname=req_user.firstname, lastname=req_user.lastname, username=req_user.username, password=req_user.password)
        db.session.add(user)
        db.session.commit()
        req_user = pending_approvals.query.filter_by(uid=uid).first()
        db.session.delete(req_user)
        db.session.commit()
    return redirect('/admin')

@app.route('/decline/<uid>', methods=['GET', 'POST'])
def decline(uid):
    if request.method=='POST':
        req_user = pending_approvals.query.filter_by(uid=uid).first()
        db.session.delete(req_user)
        db.session.commit()
    return redirect('/admin')

@app.route('/admin_allusers')
def admin_allusers():
    if session.get('uid'):
        users = logininfo.query.all()
        return render_template('/users.html', users=users)
    return redirect('/login')

@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    if request.method=='POST':
        form = request.form
        delete_q = chats.__table__.delete().where(chats.uid==form['usr_uid'])
        db.session.execute(delete_q)
        db.session.commit()
        req_user = logininfo.query.filter_by(uid=form['usr_uid']).first()
        db.session.delete(req_user)
        db.session.commit()
    return redirect('/admin')

@socketio.on('sendMsg')
def handle_sendMsg(msg):
    timestamp = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    user = logininfo.query.filter_by(uid=session['uid']).first()
    usr_msg = chats(uid=session['uid'], username=user.username, msg=msg, timestamp=timestamp)
    db.session.add(usr_msg)
    db.session.commit()
    admin = app_admins.query.filter_by(uid=1111).first()
    emit('chat', {'adminUID': admin.uid,
     'msgUID': usr_msg.uid,
     'msgID': usr_msg.msgid,
     'msgUsername': usr_msg.username,
     'msgTimestamp': usr_msg.timestamp,
     'msg': msg}, broadcast=True)

@socketio.on('deleteMsg')
def handle_deleteMsg(msgID):
    msg = chats.query.filter_by(msgid=msgID).first()
    db.session.delete(msg)
    db.session.commit()
    emit('deleteChat', {'msgID': msg.msgid}, broadcast=True)

@socketio.on('clearchat')
def handle_clearchat():
    msgs = chats.query.all()
    for msg in msgs:
        db.session.delete(msg)
    db.session.commit()
    emit('clearAllChat', broadcast=True)

# if __name__=='__main__':
#     socketio.run(app, debug=True)
