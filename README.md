# CSO

CSO is a simple Centralized Sign-on. Manage your user login (user and group) with your internal LDAP Edit

✋ Legacy app i’ve built long time ago… Not perfect but running 24/7 since a looooong time…

- LDAP Auth.
- Timebased OTP for user (Basic implementation)

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

## Workflow (login process)

Todo

## Run (in dev)

```shell
python main.py
```

## Administration

The administration is available via the [Web Interface](http://localhost:5000/admin)