
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


@app.route('/printers', methods=['GET'])
def get_printers():
    pObjs = Printer.query.all()

    printers = [
        {
            "id": p.PRINTER_ID,                              
            "name": p.PRINTER_NAME,                        
            "sub": f"{p.BLOCK} · {p.PRINTER_LOCATION}",      
            "online": bool(p.AVAILABLE),
            "endpoint": p.ENDPOINT_URL                   
        }
        for p in pObjs
    ]

    return jsonify(printers)



@app.route("/upload", methods=["POST"])
def upload():
    # ---- Clerk session ----
    token = request.cookies.get("__session")
    if not token:
        return redirect("/login")

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        userid = claims.get("username")
        email  = claims.get("email")
    except Exception as e:
        print("CLERK TOKEN ERROR:", e)
        return jsonify(message="Invalid session"), 401

    if not userid:
        return jsonify(message="User information missing"), 401

    # ---- form fields ----
    r = request.form.to_dict(flat=True)
    file = request.files.get("file")
    printer_id = r.get("printer")
    copies = r.get("copies", "1")
    mode   = r.get("mode", "color")

    if not file or not file.filename:
        return jsonify(message="No file selected."), 400

    # ---- pending-job guard ----
    check = PrintJob.query.filter_by(USERNAME=userid).first()
    if check:
        if check.STATUS == "PENDING":
            return jsonify(message="You have a pending print job."), 409
        if check.STATUS == "PRINTING":
            db.session.delete(check)
            db.session.commit()

    # ---- resolve printer ----
    pObj = Printer.query.filter_by(PRINTER_ID=printer_id).first()
    if not pObj or not pObj.ENDPOINT_URL:
        return jsonify(message="Printer not found."), 404
    purl = pObj.ENDPOINT_URL.rstrip("/")

    filename = secure_filename(file.filename)

    # ---- stream the file to the printer ----
    try:
        resp = requests.post(
            f"{purl}/upload",
            files={"file": (filename, file.stream, file.mimetype)},
            data={
                "username": userid,
                "printer":  printer_id,
                "copies":   copies,
                "mode":     mode,
            },
            timeout=30,
        )
    except requests.RequestException as e:
        print("PRINTER UPLOAD ERROR:", e)
        return jsonify(message="Could not reach printer."), 502

    if resp.status_code != 200:
        print("PRINTER RESPONSE:", resp.status_code, resp.text)
        return jsonify(message="Printer rejected the file."), 502

    # ---- OTP + PrintJob ----
    otp = SEND_OTP(email, "Print Job")
    print("OTP FOR:", userid, "IS:", otp)

    # logical remote path — the printer owns the actual bytes
    remote_path = f"{printer_id}/{userid}/{filename}"

    printjob = PrintJob(
        FILE_NAME=filename,
        FILE_PATH=remote_path,      # logical reference, not a local file
        USERNAME=userid,
        OTP_FOR_PRINTING=otp,
        PRINTER_ID=printer_id,
        STATUS="PENDING",
    )
    db.session.add(printjob)
    db.session.commit()

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
@app.post("/triggerprinting")
def invoke():
    try:
        claims = jwt.decode(
            request.cookies.get("__session"),
            options={"verify_signature": False},
        )
        userid = claims.get("username")
        data = request.get_json()
        otp = data.get("otp") if data else None

        if not all([userid, otp]):
            return jsonify(msg="Send All Data"), 417

        printjob = PrintJob.query.filter_by(USERNAME=userid).first()
        if not printjob:
            return jsonify(msg="No Pending Print Job Found"), 404

        if str(printjob.OTP_FOR_PRINTING).strip() != str(otp).strip():
            return jsonify(msg="OTP Incorrect"), 409

        pObj = Printer.query.filter_by(PRINTER_ID=printjob.PRINTER_ID).first()
        if not pObj or not pObj.ENDPOINT_URL:
            return jsonify(msg="Printer not found"), 404
        purl = pObj.ENDPOINT_URL.rstrip("/")

        # ---- tell the printer to start ----
        try:
            resp = requests.post(
                f"{purl}/print2",
                json={
                    "check":    True,
                    "username": userid,
                    "printer":  printjob.PRINTER_ID,
                    "file":     printjob.FILE_NAME,
                },
                timeout=10,
            )
        except requests.RequestException as e:
            print("PRINTER INVOKE ERROR:", e)
            return jsonify(msg="Could not reach printer"), 502

        if resp.status_code != 200:
            print("PRINTER RESPONSE:", resp.status_code, resp.text)
            return jsonify(msg="Error in Printing"), 500

        # ---- mark done and clean up the row ----
        printjob.STATUS = "PRINTING"
        db.session.commit()

        db.session.delete(printjob)
        db.session.commit()

        return jsonify(msg="Print Job Invoked"), 200

    except Exception as e:
        print("TRIGGER ERROR:", e)
        return jsonify(message="Invalid session"), 401
    
@app.get('/testHTML')
def testHTML():
    return send_from_directory('templates', 'test.html')
    


if __name__=='__main__':
   
    app.run(debug=True, threaded=True, host="0.0.0.0",port=5005) 
    
