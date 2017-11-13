from database import init_db, db_session
from models import UserDroit, Application
init_db()

# Create the first UserDroit
username = raw_input("Your first admin username (should match with an existing LDAP account) : ")
main_user = UserDroit(username=username)
main_user.group = "admin,users"
main_user.level = "10"

db_session.merge(main_user)
db_session.commit()

admin_application = Application(nom="admin")
admin_application.key = "T680SvwrxNtWPxB4DAT2"
db_session.merge(admin_application)
db_session.commit()

admin_application = Application(nom="default")
admin_application.key = "mWgBV6mKZ3nwhwpvMBxx"
db_session.merge(admin_application)
db_session.commit()

print ("Setup Done.")