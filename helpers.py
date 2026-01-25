
from dotenv import load_dotenv
import os
load_dotenv()


######################## FOR EMAIL OTP SENDING #######################################
import smtplib as smt
from email.mime.text import MIMEText as mt
import random as rd
class EmailNotValid(Exception):
    pass

def SEND_OTP(email):
    otp = rd.randint(10000, 99999)
    try:
        # Fetch sender email and password from .env
        sender = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        if not sender or not password:
            raise EmailNotValid("Email sender or password not set in environment variables")

        msg = mt(f'Your OTP is : {otp}\n\nKindly Do not reply to this email.')
        msg["From"] = sender
        msg["To"] = email
        msg["Reply-To"] = "noreply@example.com"

        with smt.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, email, msg.as_string())

        print(f"OTP sent to {email}: {otp}")

    except Exception as e:
        print("Email sending failed:", e)

    # Always return OTP (whether mail sent or not)
    return otp
######################################################################################



######################## FOR STATIC ID DECRYPT ENCRYPT #######################################

def GENERATE_STATIC_ID(usertype : str, userid : str, phone : str):
    """GENERATES A STATIC ID USING DATA STRS"""
    STATIC_ID=[]
    if (t:=usertype.strip().lower()) == 'f':
        STATIC_ID.append('F')
    elif usertype.strip().lower() == 's':
        STATIC_ID.append('S')
    
    STATIC_ID.append(userid.strip().upper())
    STATIC_ID.append(phone.strip())

    return '$'.join(STATIC_ID)+('@CVR.STUDENT' if t=='s' else '@CVR.FACULTY')

def DECRYPT_STATIC_ID(enc_data: str):
    """DECRYPTS A STATIC ID TO DATA LIST"""
    return enc_data.split('$')
#######################################################################################


###################FOR GENERATING HASH PASSWORDS ############################################

from werkzeug.security import generate_password_hash as gph, check_password_hash as cph

def GENERATE_HASH_PASSWORD(password: str):
    """Generates a password hash using werkzeug.security"""
    return gph(password)
def CHECK_PASSWORD_HASH(password: str, hashed_password: str):
    """Checks a password hash against a given password"""
    return cph(hashed_password, password)

#######################################################################################

