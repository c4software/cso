# Use NGINX+CSO to authenticate your user.

## Quick setup

- Setup the vhost like the sample configuration.
- Configure the « secret_key » in the client.py and start the script (Python >=2.7).

## Install the service

If you use SystemD you can use the [cso_client.service file](./cso_client/cso_client.service) to start the cso_client automatically on system startup.

- copy the ```cso_client.service``` in the ```/etc/systemd/system/```
- Run ```sudo systemctl daemon-reload```
- ```sudo systemctl start cso_client```