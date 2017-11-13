# CSO

CSO is a simple Centralized Sign-on (using to your internal LDAP)

✋ Legacy app i’ve built long time ago… Not perfect but running 24/7 since a looooong time…

- LDAP Auth.
- Timebased OTP for user (Basic implementation)

![Login example](./static/images/home.png)
![User example](./static/images/users.png)
![Secret example](./static/images/secret.png)

## WIP

- [X] Fix bad CSRF Implementation.
- [X] Update the Design to something more … modern!
- [ ] Rewrite login (CSOMain module).
  - [X] Implement TOPT during the login.
  - [ ] Add a max SESSION time
- [X] Secret Administration (OTP):
  - [X] Generate.
  - [X] Update.
  - [X] Share via QRCode.

## Installation

```shell
pip install -r requirements.txt
```

## First setup

- Change the ```ldap_server``` and the ```ldap_server``` in the ```parameters.py```.
- Run the ```setup.py```, and enter your « first » admin ```username``` for the CSO. (the username should match with someone on the LDAP server).
- Start the test server ```python main.py```

## Workflow (login process)

Todo

## Run (in dev)

```shell
python main.py
```

## Administration

The administration is available via the [Web Interface](http://localhost:5000/admin)