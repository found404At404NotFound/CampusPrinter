from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from random import randint as rd
from dotenv import load_dotenv
import os, datetime
from helpers import *
from sqlalchemy.exc import IntegrityError


load_dotenv()


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Cookie / session config
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

db = SQLAlchemy(app)

CORS(
    app,
    supports_credentials=True,
    origins=[
        "https://two-pichunter-rom-notes.trycloudflare.com",
        "https://calcium-cave-sticker-legend.trycloudflare.com",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:50792",
        "http://127.0.0.1:53600",
        "https://127.0.0.1:53600",
        "http://127.0.0.1:5500",
        "https://127.0.0.1:5500"
        
    ],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"]
)

class PendingUser(db.Model):
    ID = db.Column(db.Integer, primary_key=True, autoincrement = True)

    NAME = db.Column(db.String(100), nullable=False)

    USERNAME = db.Column(db.String(100), nullable=False)

    EMAIL = db.Column(db.String(120), unique=True, nullable=False)

    PASSWORD = db.Column(db.String(256), nullable=False)

    OTP_FOR_REGISTRATION = db.Column(db.String(6), nullable=False)



class User(db.Model):
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NAME = db.Column(db.String(100), nullable=False)

    USERNAME = db.Column(db.String(100), nullable=False)

    EMAIL = db.Column(db.String(120), unique=True, nullable=False)

    PASSWORD = db.Column(db.String(256), nullable=False)

    OTP_FOR_PRINT = db.Column(db.String(6), nullable=True)



@app.route('/ping')
def ping():
    return jsonify(ping="pong")


@app.get('/fof/register')
def get_register():
    return jsonify(msg='send post request.')

@app.post('/fof/register')
def post_register(): 
    data : dict = request.get_json()
    name : str = data.get('name') if data else None
    username : str = data.get('username') if data else None
    email : str = data.get('email') if data else None
    password : str = data.get('password') if data else None
    chk_list : list = [name,username,email,password]
    print(chk_list)
    if not all(chk_list):
        return jsonify(msg='Send All Data'), 417
    
    try:
        pending_user = PendingUser(NAME=name,
                               USERNAME=username,
                               PASSWORD=password,
                               EMAIL=email,
                               OTP_FOR_REGISTRATION=SEND_OTP(email))
    
        db.session.add(pending_user)
        db.session.commit()
        session['username']=username
        return jsonify(msg='User Ready For Verification.'),200
    except IntegrityError:
        return jsonify(msg="User Alread Exists With Some Otp"),403

    

@app.get('/fof/reg_otp')
def get_reg_otp():
    return jsonify(msg='send post request.'),200

@app.post('/fof/reg_otp')
def post_reg_otp():
    username :str = request.args.get('username') if request.args.get('username') else None
    print(username)
    data :dict = request.get_json()
    otp : str= str(data.get('otp')  if data else None ) if data else None
    chk_list : list = [otp, username]
    if not all(chk_list):
        return jsonify(msg='Send All Data'), 417
    
    try:
        pendingUser : PendingUser = PendingUser.query.filter_by(USERNAME=username).first()

        if pendingUser is None:
            return jsonify(msg='User Doesnt exist.'),404
        
        if otp.strip() == str(pendingUser.OTP_FOR_REGISTRATION).strip():
            user = User(
                NAME=pendingUser.NAME,
                USERNAME = pendingUser.USERNAME,
                EMAIL=pendingUser.EMAIL,
                PASSWORD = GENERATE_HASH_PASSWORD(pendingUser.PASSWORD)
            )

            db.session.add(user)
            db.session.commit()

            return jsonify(msg='User Sucessfully registered.'),200
        
        return jsonify(msg='Otp wrong'),409

    
    except:
        print('EXCEPTION')
        return jsonify(msg= 'EXCEPTION'),404



@app.get('/fof/login')
def get_login():
    return render_template('login.html')

@app.post('/fof/login')

def post_login():
    data : dict = request.get_json()
    username : str = data.get('username') if data else None
    email : str = data.get('email') if data else None
    password : str = data.get('password') if data else None
    print ( username, email, password)
    try:
        if username:
            user = User.query.filter_by(USERNAME=username).first()
            if not user:
                return jsonify(msg='User might not exist.'),404
            if CHECK_PASSWORD_HASH(str(password).strip(),user.PASSWORD):
                session['LOGIN']=True
                return jsonify(msg='Logged In.'),200
            else:
                return jsonify(msg='Password Incorrect.'),419
        elif email:
            user = User.query.filter_by(EMAIL=email).first()
            if not user:
                return jsonify(msg='User might not exist.'),404

            if CHECK_PASSWORD_HASH(str(password).strip(),user.PASSWORD):
                session['LOGIN']=True
                return jsonify(msg='Logged In.'),200
            else:
                return jsonify(msg='Password Incorrect.'),419
        
        else:
            return jsonify('Send Proper Data'),403
    


    except:
        print('EXCEPTION')
        return jsonify(msg='EXCEPTION'),404

@app.post('/setses')
def ses():
    if request.method=='POST':
        session['ses']=True
        print(session.get('ses'))
        return jsonify(msg=True),200
    
    
@app.post('/getses')
def getses():
    print(session.get('ses'))
    if not session.get('ses'):
        return jsonify(msg=False),404
    else:
        return jsonify(msg=True),200    



if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, threaded=True, host='0.0.0.0')
