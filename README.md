# CSO

CSO is a simple Centralized Sign-on. Manage your user login (user and group) with your internal LDAP Edit

✋ Legacy app i’ve built long time ago… Not perfect but running 24/7 since a looooong time…

- LDAP Auth.
- Timebased OTP for user (WIP)

## WIP

- Rewrite login (CSOMain module).
- Secret Administration (OTP):
  - Generate.
  - Update.
  - Share via QRCode.

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