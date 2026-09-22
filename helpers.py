
from dotenv import load_dotenv
import os
load_dotenv()


######################## FOR EMAIL OTP SENDING #######################################

import resend
import random
def SEND_OTP(email, type):
    otp = random.randint(100000, 999999)

    
    resend.api_key =os.getenv("RESEND_API_KEY")

    params = {
        "from": "CampusPrinter <otp@printer.mangojam.me>",
        "to": [f"{email}"],

        "template": {
            "id": "print-verification-code",
            "variables": {
                "first_name": "User",
                "printer_name": "CSE Lab Printer",
                "expiry_minutes": '10',
                "otp_code": f"{otp}",
                "company_name": "CampusPrinter",
                "company_address": "CVR College of Engineering"
            }
        }
    }

    email = resend.Emails.send(params)

    print(email)
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

def GET_BRANCH_AND_YEAR(rollNumber : str, current_year : int) -> tuple[str,int]:
    year=current_year-int(rollNumber[0:1])
    print(year)
    print(rollNumber)
    d={'A62':'CS',
       'A66':'AIML',
       'A05':'CSE',
       'A67':'DS',
       'A01':'CIVIL',
       'A32':'BS',
       'A04':'ECE',
       'A03':'MECH',
       'A06':'EVL',
       'A07':'EIE'}

    
    return d.get(rollNumber[5:8].upper()),year




def IS_DEV( roll : str )-> bool :
    l=['24B81A62J5','24B81A62H9','24B81A62E9','24B81A62K2','24B81A62G0','24B81A05ML']
    if not roll :
        return False
    if roll.upper() in l :
        return True
    else:
        return False


def GET_USERNAME(username : str , email : str) -> str:
    if( not username):
        l=len(email)
        username=email[:l-10]
    return username


