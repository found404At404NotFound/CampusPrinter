
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, send_from_directory
import requests
from flask_sqlalchemy import SQLAlchemy
import requests
from flask_cors import CORS
from random import randint as rd
from dotenv import load_dotenv
import os, datetime, re
from helpers import *
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import FileStorage
from models import * 
from werkzeug.utils import secure_filename
from tasks import print_pdf
from clerk_backend_api import Clerk
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
import jwt
load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(),'uploads')

# Cookie / session config
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

db.init_app(app)

with app.app_context():
    db.create_all()


CORS(
    app,
    supports_credentials=True,
    origins=[
        "https://two-pichunter-rom-notes.trycloudflare.com",
        "https://calcium-cave-sticker-legend.trycloudflare.com",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:50792",
        "http://127.0.0.1:53600",
        "http://127.0.0.1:59554",
        "http://127.0.0.1:5500",
        "https://127.0.0.1:5500",
        'http://127.0.0.1:52018'
        
    ],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"]
)


clerk = Clerk(bearer_auth=os.getenv('CLERK_SECRET_KEY'))



clerk = Clerk(
    bearer_auth=os.getenv("CLERK_SECRET_KEY")
)

def current_clerk_identity():
    token = request.cookies.get("__session")
    if not token:
        return None, (jsonify(message="Unauthorized"), 401)

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except Exception as error:
        print("CLERK TOKEN ERROR:", error)
        return None, (jsonify(message="Invalid session"), 401)

    userid = claims.get("username")
    if not userid:
        return None, (jsonify(message="User information missing"), 401)

    return userid, None




@app.route("/")
def home():
    return redirect("/login")
@app.get('/login')
def login():
    if request.cookies.get("__session"):
        return redirect("/print")
    return send_from_directory('templates', 'login.html')

@app.get('/register')
def register():
    if request.cookies.get("__session"):
        return redirect("/print")
    return send_from_directory('templates', 'register.html')

@app.get('/print')
def print_page():
    clerk_session_id = request.cookies.get("__session")
    
    if not clerk_session_id:
        return redirect("/login")
    return send_from_directory('templates', 'print.html')

@app.get('/upload')
def get_uploads():
    return send_from_directory('templates','print.html')



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    response = redirect("/login")
    response.delete_cookie("__session")
    return response




@app.route("/upload", methods=["POST"])
def upload():

    # Get Clerk session token
    token = request.cookies.get("__session")

    if not token:
        return redirect("/login")

    try:
        # Read Clerk session claims
        # IMPORTANT: verify the JWT signature in production.
        claims = jwt.decode(
            token,
            options={"verify_signature": False}
        )

        userid = claims.get("username")
        email = claims.get("email")
        clerk_user_id = claims.get("user_id")


    except Exception as e:
        print("CLERK TOKEN ERROR:", e)
        return jsonify(message="Invalid session"), 401

    if not userid:
        return jsonify(message="User information missing"), 401

    print("USER:", userid)
    print("CLERK ID:", clerk_user_id) 
    print("EMAIL:", email)

    file: FileStorage | None = request.files.get("file")
    printer_id: str = "LH103"
    try:
        check = PrintJob.query.filter_by(USERNAME=userid).first()
        if check:
            if check.STATUS == "PENDING":
                return jsonify(message="You have a pending print job."), 409
            if check.STATUS == "PRINTING":
                db.session.delete(check)
                db.session.commit()
    except Exception as e:
        pass


    otp = SEND_OTP(email, "Print Job")

    print(file)
    print("OTP FOR:", userid, "IS:", otp)

    if not file:
        print("NO FILE PART")
        return jsonify(message="empty request."), 400

    if not file.filename:
        print("NO SELECTED FILE")
        return jsonify(message="No file selected."), 400

    filename = secure_filename(file.filename)

    print("FILENAME:", filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    pendingfile = UploadFile(
        FILE_NAME=filename,
        FILE_PATH=filepath,
        USERNAME=userid,
        PRINTER_ID=printer_id
    )

    printjob = PrintJob(
        FILE_NAME=filename,
        FILE_PATH=filepath,
        USERNAME=userid,
        OTP_FOR_PRINTING=otp,
        PRINTER_ID=printer_id,
        STATUS="PENDING"
    )

    db.session.add(pendingfile)
    db.session.add(printjob)
    db.session.commit()

    if not os.path.exists(filepath):
        print("FILE NOT SAVED")
        return jsonify(message="Error in saving file."), 500

    return jsonify(message=True), 200    


@app.get("/pending")
def pending_print():
    userid, error = current_clerk_identity()
    if error:
        return error

    printjob = PrintJob.query.filter_by(
        USERNAME=userid, STATUS="PENDING"
    ).first()
    if not printjob:
        return jsonify(pending=False), 200

    return jsonify(pending=True, file_name=printjob.FILE_NAME), 200


@app.post("/cancel")
def cancel_print():
    userid, error = current_clerk_identity()
    if error:
        return error

    printjob = PrintJob.query.filter_by(
        USERNAME=userid, STATUS="PENDING"
    ).first()
    if not printjob:
        return jsonify(message="No pending print job"), 404

    filepath = printjob.FILE_PATH
    db.session.delete(printjob)
    db.session.commit()
    if os.path.exists(filepath):
        os.remove(filepath)

    return jsonify(message="Print job cancelled"), 200
    

@app.route("/api/protected")
def protected():
    
    result = clerk.authenticate_request(request)

    if not result.is_authenticated:
        return jsonify({
            "error": "Unauthorized"
        }), 401

    user_id = result.payload.get("sub")

    try:
        user = clerk.users.get(user_id=user_id)
        username = user.username

    except Exception:
        return jsonify({
            "error": "Could not get user"
        }), 500

    if not username:
        return jsonify({
            "error": "Username required"
        }), 403

      
    return jsonify({
        "message": "You are authenticated!",
        "user_id": user_id,
        "username": username
    })


@app.post('/triggerprinting')
def invoke():
    try:
        claims = jwt.decode(
            request.cookies.get("__session"),
            options={"verify_signature": False}
        )
        userid = claims.get("username")
        data: dict = request.get_json()
        otp: str = data.get('otp') if data else None
        if not all([userid, otp]):
            return jsonify(msg='Send All Data'), 417
        try:
            printjob = PrintJob.query.filter_by(USERNAME=userid).first()
            if not printjob:
                return jsonify(msg='No Pending Print Job Found'), 404
            if str(printjob.OTP_FOR_PRINTING).strip() != str(otp).strip():
                return jsonify(msg='OTP Incorrect'), 409
    
            resp = requests.post(
                'http://127.0.0.1:6969/ping',
                files={'file': open(printjob.FILE_PATH, 'rb')},
                data={'printer_id': printjob.PRINTER_ID},
            )
            if resp.status_code != 200:
                return jsonify(msg='Error in Printing'), 500
    
            printjob.STATUS = 'PRINTING'
            db.session.commit()
            os.remove(printjob.FILE_PATH)
            printjob = PrintJob.query.filter_by(USERNAME=userid).first()
            if printjob:
                db.session.delete(printjob)
                db.session.commit()
                
            return jsonify(msg='Print Job Invoked'), 200
        except Exception:
            print('EXCEPTION')
            return jsonify(msg='EXCEPTION'), 404
    
    except Exception as e:
        print("CLERK TOKEN ERROR:", e)
        return jsonify(message="Invalid session"), 401    

    


if __name__=='__main__':
   
    app.run(debug=True, threaded=True, host='0.0.0.0',port=5005)
