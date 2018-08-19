default_website = "http://brosseau.ovh"

#ldap_server = "ldap://192.168.1.49"
#ldap_dn	= "uid={0},cn=users,dc=brosseau"
ldap_server = "ldap://localhost"
ldap_dn = "cn={0},dc=example,dc=org"

log_path = "/tmp/cso.log"

""" ADMIN """
login_url = "/login?apps=admin&next=/admin/login"
