# Use NGINX+CSO to authenticate your user

You have two way to USE CSO + NGINX

- The standalone, you have a small script on each server.
- Centralized version, each server must be able to contact the CSO in HTTP to test if the connection is active.

## Centralized setup

### Quick overview

- Setup the vhost like (nginx_sample_vhost_centralized.conf)[the sample configuration]
- Go to your website you should be redirect to the CSO. 

## Standalone setup

### Quick overview

- Setup the vhost like (nginx_sample_vhost_standalone.conf)[the sample configuration]
- Start the client ```client.py mWgBV6mKZ3nwhwpvMBxx``` (Python >=2.7).
- Go to your website you should be redirect to the CSO.

### Install the CSO_CLIENT service

If you use SystemD you can use the [cso_client.service file](./cso_client/cso_client.service) to start the cso_client automatically on system startup.

- copy the ```cso_client.service``` in the ```/etc/systemd/system/```
- Run ```sudo systemctl daemon-reload```
- ```sudo systemctl start cso_client```