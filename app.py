from flask import Flask, jsonify, redirect, render_template, request, session, url_for, send_from_directory
import requests
from flask_sqlalchemy import SQLAlchemy
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
import gzip
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Cookie / session config
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

db.init_app(app)

with app.app_context():
    db.create_all()

KEY = base64.urlsafe_b64decode(os.getenv("ENC_DEC_KEY"))

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
        "http://127.0.0.1:52018"
    ],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin"
    ]
)


clerk = Clerk(
    bearer_auth=os.getenv("CLERK_SECRET_KEY")
)


def current_clerk_identity():
    token = request.cookies.get("__session")

    if not token:
        return None, (
            jsonify(message="Unauthorized"),
            401
        )

    try:
        claims = jwt.decode(
            token,
            options={"verify_signature": False}
        )

    except Exception as error:
        print("CLERK TOKEN ERROR:", error)
        

        return None, (
            jsonify(message="Invalid session"),
            401
        )

    userid = claims.get("username")

    if not userid:
        return None, (
            jsonify(message="User information missing"),
            401
        )

    return userid, None


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return send_from_directory("templates","home.html")
    
@app.route("/privacy")
def privacy():
    return send_from_directory("templates","privacy.html")
    
@app.route("/terms")
def terms():
    return send_from_directory("templates","terms.html")

@app.get('/login')
def login():
    if request.cookies.get("__session"):
        return redirect("/print")

    return send_from_directory(
        'templates',
        'login.html'
    )


@app.get('/register')
def register():
    if request.cookies.get("__session"):
        return redirect("/print")

    return send_from_directory(
        'templates',
        'register.html'
    )


@app.get('/print')
def print_page():
    clerk_session_id = request.cookies.get("__session")

    if not clerk_session_id:
        return redirect("/login")

    return send_from_directory(
        'templates',
        'print.html'
    )


@app.get('/upload')
def get_uploads():
    return send_from_directory(
        'templates',
        'print.html'
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    response = redirect("/login")
    response.delete_cookie("__session")
    return response


# ============================================================
# PRINTERS
# ============================================================

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

    # --------------------------------------------------------
    # Clerk session
    # --------------------------------------------------------

    token = request.cookies.get("__session")

    if not token:
        return redirect("/login")

    try:
        claims = jwt.decode(
            token,
            options={"verify_signature": False}
        )

        userid = claims.get("username")
        email = claims.get("email")

    except Exception as e:
        print("CLERK TOKEN ERROR:", e)
        return jsonify(message="Invalid session"), 401

    if not userid:
        return jsonify(message="User information missing"), 401

    # --------------------------------------------------------
    # Form fields
    # --------------------------------------------------------

    r = request.form.to_dict(flat=True)

    file = request.files.get("file")
    printer_id = r.get("printer")
    copies = r.get("copies", "1")
    mode = r.get("mode", "bw")

    print(
        "UPLOAD REQUEST:",
        userid,
        printer_id,
        copies,
        mode,
        file.filename if file else None
    )

    if not file or not file.filename:
        return jsonify(message="No file selected."), 400

    # --------------------------------------------------------
    # Pending-job guard
    # --------------------------------------------------------

    check = PrintJob.query.filter_by(
        USERNAME=userid
    ).first()

    if check:
        if check.STATUS == "PENDING":
            return jsonify(
                message="You have a pending print job."
            ), 409

        if check.STATUS == "PRINTING":
            db.session.delete(check)
            db.session.commit()

    # --------------------------------------------------------
    # Resolve printer
    # --------------------------------------------------------

    pObj = Printer.query.filter_by(
        PRINTER_ID=printer_id
    ).first()

    if not pObj or not pObj.ENDPOINT_URL:
        return jsonify(message="Printer not found."), 404

    purl = pObj.ENDPOINT_URL.rstrip("/")

    filename = secure_filename(file.filename)

    # ========================================================
    # GZIP + AES-256-GCM ENCRYPTION
    # ========================================================

    try:
        # File is ALREADY GZIP compressed by frontend
        gzip_data = file.read()
    
        # Generate random IV
        iv = os.urandom(12)
    
        # Encrypt GZIP data directly
        encrypted = AESGCM(KEY).encrypt(
            iv,
            gzip_data,
            None
        )
    
        # IV + encrypted GZIP data
        encrypted_data = iv + encrypted
    
        encrypted_filename = filename + ".bin"
    
        print(
            "FILE ENCRYPTED:",
            filename,
            "->",
            encrypted_filename
        )
    
    except Exception as e:
        print("ENCRYPTION ERROR:", e)
    
        return jsonify(
            message="Could not encrypt file."
        ), 500

    # --------------------------------------------------------
    # Send encrypted file to Print Agent
    # --------------------------------------------------------

    try:
        print("Sending encrypted file to printer agent...")

        resp = requests.post(
            f"{purl}/upload",
            files={
                "file": (
                    encrypted_filename,
                    encrypted_data,
                    "application/octet-stream"
                )
            },
            data={
                "username": userid,
                "printer": printer_id,
                "copies": copies,
                "mode": mode
            },
            timeout=120
        )

    except requests.RequestException as e:
        print("PRINTER UPLOAD ERROR:", e)

        return jsonify(
            message="Could not reach printer."
        ), 502

    # --------------------------------------------------------
    # Check Print Agent response
    # --------------------------------------------------------

    if resp.status_code != 200:
        print(
            "PRINTER RESPONSE:",
            resp.status_code,
            resp.text
        )

        return jsonify(
            message="Printer rejected the file."
        ), 502

    # --------------------------------------------------------
    # Read Print Agent response
    # --------------------------------------------------------

    try:
        agent_data = resp.json()

    except Exception as e:
        print("AGENT JSON ERROR:", e)

        return jsonify(
            message="Invalid response from printer."
        ), 502

    remote_path = agent_data.get("file_path")

    if not remote_path:
        print(
            "AGENT DID NOT RETURN FILE PATH:",
            agent_data
        )

        return jsonify(
            message="Printer did not return file path."
        ), 502

    # --------------------------------------------------------
    # Send OTP
    # --------------------------------------------------------

    otp = SEND_OTP(
        email,
        user=userid,
        printer=printer_id
    )

    # --------------------------------------------------------
    # Create PrintJob
    # --------------------------------------------------------

    printjob = PrintJob(
        FILE_NAME=filename,
        FILE_PATH=remote_path,
        USERNAME=userid,
        OTP_FOR_PRINTING=otp,
        PRINTER_ID=printer_id,
        STATUS="PENDING"
    )

    db.session.add(printjob)
    db.session.commit()

    return jsonify(
        message=True
    ), 200

# ============================================================
# PENDING
# ============================================================

@app.get("/pending")
def pending_print():

    userid, error = current_clerk_identity()

    if error:
        return error

    printjob = PrintJob.query.filter_by(
        USERNAME=userid,
        STATUS="PENDING"
    ).first()

    if not printjob:
        return jsonify(
            pending=False
        ), 200

    return jsonify(
        pending=True,
        file_name=printjob.FILE_NAME
    ), 200


# ============================================================
# CANCEL
# ============================================================
#
# Main backend:
#
# 1. Finds pending PrintJob
# 2. Finds printer
# 3. Sends /cancel to Print Agent
#
# Print Agent:
#
# 1. Finds UploadFile
# 2. Deletes physical file
# 3. Deletes UploadFile
# 4. Deletes PrintJob
#
# ============================================================

@app.post("/cancel")
def cancel_print():

    # ------------------------------------------------------------
    # Get logged-in user from Clerk
    # ------------------------------------------------------------
    userid, error = current_clerk_identity()

    if error:
        return error

    if not userid:
        return jsonify(
            message="User information missing"
        ), 401

    try:

        # --------------------------------------------------------
        # Find pending PrintJob
        # --------------------------------------------------------
        printjob = PrintJob.query.filter_by(
            USERNAME=userid,
            STATUS="PENDING"
        ).first()

        if not printjob:
            return jsonify(
                message="No pending print job"
            ), 404

        printer_id = printjob.PRINTER_ID

        # --------------------------------------------------------
        # Find printer
        # --------------------------------------------------------
        printer = Printer.query.filter_by(
            PRINTER_ID=printer_id
        ).first()

        if not printer:
            return jsonify(
                message="Printer not found"
            ), 404

        if not printer.ENDPOINT_URL:
            return jsonify(
                message="Printer endpoint not configured"
            ), 404

        purl = printer.ENDPOINT_URL.rstrip("/")

        # --------------------------------------------------------
        # Tell Print Agent to cancel
        #
        # The agent already knows its PRINTER_ID from .env.
        # We only need to tell it which username to cancel.
        # --------------------------------------------------------
        try:

            resp = requests.post(
                f"{purl}/cancel",
                json={
                    "username": userid,
                    "printer": printer_id
                },
                timeout=30
            )

        except requests.RequestException as e:

            print(
                "PRINTER CANCEL ERROR:",
                repr(e)
            )

            return jsonify(
                message="Could not reach printer."
            ), 502

        # --------------------------------------------------------
        # Agent successfully cancelled
        # --------------------------------------------------------
        if resp.status_code == 200:

            print(
                f"[cancel] Print agent cancelled "
                f"{userid} / {printer_id}"
            )

            # IMPORTANT:
            #
            # Print Agent has already deleted PrintJob
            # and UploadFile from the shared database.
            #
            # Do NOT db.session.delete(printjob) here.
            #

            return jsonify(
                message="Print job cancelled"
            ), 200

        # --------------------------------------------------------
        # Agent returned an error
        # --------------------------------------------------------
        print(
            "PRINTER CANCEL RESPONSE:",
            resp.status_code,
            resp.text
        )

        return jsonify(
            message="Error cancelling print job",
            printer_status=resp.status_code
        ), 500

    except Exception as e:

        print(
            "[cancel] ERROR:",
            repr(e)
        )

        return jsonify(
            message="Cancel failed",
            error=str(e)
        ), 500
# ============================================================
# PROTECTED
# ============================================================

@app.route("/api/protected")
def protected():

    result = clerk.authenticate_request(
        request
    )

    if not result.is_authenticated:

        return jsonify({
            "error": "Unauthorized"
        }), 401


    user_id = result.payload.get("sub")

    try:

        user = clerk.users.get(
            user_id=user_id
        )

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


# ============================================================
# TRIGGER PRINTING
# ============================================================
#
# Main backend:
#
# 1. Gets OTP from frontend
# 2. Finds PrintJob
# 3. Checks OTP
# 4. Finds printer
# 5. Sends /print2 to Print Agent
#
# Print Agent:
#
# 1. Finds UploadFile in Supabase
# 2. Gets FILE_PATH
# 3. Checks physical file
# 4. Sends file to Huey
# 5. Immediately returns 200
#
# ============================================================

@app.post("/triggerprinting")
def invoke():

    try:

        # ----------------------------------------------------
        # Clerk session
        # ----------------------------------------------------

        token = request.cookies.get(
            "__session"
        )

        if not token:

            return jsonify(
                message="Invalid session"
            ), 401


        claims = jwt.decode(
            token,
            options={"verify_signature": False}
        )

        userid = claims.get(
            "username"
        )


        # ----------------------------------------------------
        # OTP from frontend
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        ) or {}

        otp = data.get(
            "otp"
        )


        if not userid or not otp:

            return jsonify(
                msg="Send All Data"
            ), 417


        # ----------------------------------------------------
        # Find pending PrintJob
        # ----------------------------------------------------

        printjob = PrintJob.query.filter_by(
            USERNAME=userid,
            STATUS="PENDING"
        ).first()

        if not printjob:

            return jsonify(
                msg="No Pending Print Job Found"
            ), 404


        # ----------------------------------------------------
        # Verify OTP
        # ----------------------------------------------------

        if str(
            printjob.OTP_FOR_PRINTING
        ).strip() != str(
            otp
        ).strip():

            return jsonify(
                msg="OTP Incorrect"
            ), 409


        # ----------------------------------------------------
        # Resolve printer
        # ----------------------------------------------------

        pObj = Printer.query.filter_by(
            PRINTER_ID=printjob.PRINTER_ID
        ).first()

        if not pObj or not pObj.ENDPOINT_URL:

            return jsonify(
                msg="Printer not found"
            ), 404

        purl = pObj.ENDPOINT_URL.rstrip("/")


        # ----------------------------------------------------
        # Tell Print Agent to print
        # ----------------------------------------------------

        try:

            resp = requests.post(
                f"{purl}/print2",

                json={
                    "check": True,
                    "username": userid,
                    "printer": printjob.PRINTER_ID
                },

                # Agent now immediately returns after
                # queueing the Huey task.
                timeout=30
            )

        except requests.RequestException as e:

            print(
                "PRINTER INVOKE ERROR:",
                e
            )

            return jsonify(
                msg="Could not reach printer"
            ), 502


        # ----------------------------------------------------
        # Check Print Agent response
        # ----------------------------------------------------

        if resp.status_code != 200:

            print(
                "PRINTER RESPONSE:",
                resp.status_code,
                resp.text
            )

            return jsonify(
                msg="Error in Printing"
            ), 500


        # ----------------------------------------------------
        # Mark job as PRINTING
        # ----------------------------------------------------

        printjob.STATUS = "PRINTING"

        db.session.commit()


        return jsonify(
            msg="Print Job Invoked"
        ), 200


    except Exception as e:

        print(
            "TRIGGER ERROR:",
            e
        )

        return jsonify(
            message="Invalid session"
        ), 401


# ============================================================
# TEST HTML
# ============================================================

@app.get('/testHTML')
def testHTML():

    return send_from_directory(
        'templates',
        'test.html'
    )


@app.get('/credits')
def credit():
    return send_from_directory("templates","credits.html")

# ============================================================
# START SERVER
# ============================================================

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(
        
        threaded=True,
        host="0.0.0.0",
        port=5005
    )
