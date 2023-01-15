class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////home/davit/Desktop/projects/personal/classroom/classroom.db"
    SECRET_KEY = 'secret-key'
    SECURITY_FRESHNESS_GRACE_PERIOD = 3600
    SECURITY_DEFAULT_REMEMBER_ME = True
    SECURITY_REGISTERABLE = True
