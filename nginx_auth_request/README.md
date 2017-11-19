# Use NGINX+CSO to authenticate your user

You have to way to USE CSO + NGINX

- The standalone, you have a small script on each server.
- Centralized version, each server must be able to contact the CSO in HTTP to test if the connection is active.

## Standalone setup

### Quick overview

- Setup the vhost like the sample configuration.
- Start the client ```client.py mWgBV6mKZ3nwhwpvMBxx``` (Python >=2.7).
- Go to your website you should be redirect to the CSO.

### Install the CSO_CLIENT service

If you use SystemD you can use the [cso_client.service file](./cso_client/cso_client.service) to start the cso_client automatically on system startup.

- copy the ```cso_client.service``` in the ```/etc/systemd/system/```
- Run ```sudo systemctl daemon-reload```
- ```sudo systemctl start cso_client```

### Add (or update) your NGINX Vhost

Take a look at [the sample configuration](./nginx_sample_vhost.conf)

If you already have a vhost juste add to your ```server``` block the following configuration:

✋ Don’t forget to edit the « https://login… », its should be your CSO URL.

```conf
error_page 401 = @error401;
    location @error401 {
    return 302 https://login.societe.internal/login?apps=default&next=http://www.monsite.fr/checkAuth;
}

location /auth {
    proxy_pass http://127.0.0.1:8000/auth;

    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_set_header Client-IP $remote_addr;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Upstream $remote_addr;
}

location /checkAuth {
    proxy_pass http://127.0.0.1:8000/checkAuth;
    proxy_redirect   off;
    proxy_set_header Host $host;
}
```

Now to enable the « auth » redirectio. Add this configuration in any ```location``` block you want to « protect » by the CSO

```conf
    auth_request /auth;
```