
from dotenv import load_dotenv
import os
load_dotenv()


######################## FOR EMAIL OTP SENDING #######################################
import os
import random
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi
from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail

def SEND_OTP(email):
    otp = random.randint(10000, 99999)

    config = Configuration()
    config.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_client = ApiClient(config)
    api_instance = TransactionalEmailsApi(api_client)

    email_data = SendSmtpEmail(
        to=[{"email": email}],
        sender={
            "name": "Printer App",
            "email": os.getenv("EMAIL_FROM") 
        },
        subject="Your OTP Verification",
        html_content=f"""
        <h3>Your OTP is: {otp}</h3>
        <p>Do Not Reply To this Email.</p>
        <p>Do not share it with anyone.</p>
        """
    )

    api_instance.send_transac_email(email_data)

    print("OTP sent:", otp)
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

