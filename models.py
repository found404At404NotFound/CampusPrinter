from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PendingUser(db.Model):
    ID = db.Column(db.Integer, primary_key=True)

    USERNAME = db.Column(db.String(100), nullable=False)
    NAME = db.Column(db.String(100), nullable=False)
    BRANCH = db.Column(db.String(100), nullable=False)
    YEAR = db.Column(db.String(10), nullable=False)
    EMAIL = db.Column(db.String(120), unique=True, nullable=False)
    DEV = db.Column(db.Boolean, default=False)
    PASSWORD = db.Column(db.String(256), nullable=False)

    OTP_FOR_REGISTRATION = db.Column(db.String(6), nullable=False)


#TODO : DO db.create_all() to create these tables in the database
class User(db.Model):
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    NAME = db.Column(db.String(100), nullable=False)

    USERNAME = db.Column(db.String(100), nullable=False)

    EMAIL = db.Column(db.String(120), unique=True, nullable=False)

    PASSWORD = db.Column(db.String(256), nullable=True)

    OTP_FOR_VERIFICATION = db.Column(db.String(6), nullable=True)

    BRANCH = db.Column(db.String(100), nullable=False)

    YEAR = db.Column(db.String(10), nullable=False)

    DEV = db.Column(db.Boolean, default=False)
    

    """
 #TODO: create this Captain: 
  class UserHistory(db.Model):
    STATICID=db.Column(db.String(50),primary_key=True)
    TOTALPRINTS=db.Column(db.Integer)
    LASTPRINT=db.Column(db.Date)
    PENDINGFILE=db.Column(db.Text)
    PENDINGFILEOTP = db.Column(db.Integer, nullable=True)
w
    """




class Printer(db.Model):
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    
    PRINTER_NAME = db.Column(db.String(100), nullable=False)
    BLOCK = db.Column(db.String(50), nullable=False)
    PRINTER_ID = db.Column(db.String(15), nullable=False, unique=True)
    PRINTER_LOCATION = db.Column(db.String(200), nullable=False)
    ENDPOINT_URL = db.Column(db.String(300), nullable=False)
    PASSWORD = db.Column(db.String(256), nullable=False)
    AVAILABLE = db.Column(db.Boolean, default=True)

    TOTAL_PRINTS = db.Column(db.Integer, default=0)

    



class PrintJob(db.Model):
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    FILE_NAME = db.Column(db.String(200), nullable=False)
    FILE_PATH = db.Column(db.String(300), nullable=False)
    USERNAME = db.Column(db.String(100), nullable=False)
    TIME = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    STATUS = db.Column(db.String(50), nullable=False)
    OTP_FOR_PRINTING = db.Column(db.String(6), nullable=True)
    PRINTER_ID = db.Column(db.String(15), nullable=False)



class UploadFile(db.Model):
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    FILE_NAME = db.Column(db.String(200), nullable=False)
    FILE_PATH = db.Column(db.String(300), nullable=False)
    USERNAME = db.Column(db.String(100), nullable=False)
    PRINTER_ID = db.Column(db.String(15), nullable=False)
    TIME = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    
