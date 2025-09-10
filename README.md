**Description**

This project aims to create an integration service to act as a bridge between databases and websites.
It is deployed in an EC2 instance on AWS and all the configurations are made accordingly.
Be sure to change the configurations based on how and where you deploy this manual version of API Gateway.


**DOCKER**

To build the image: (may or may not need sudo depending on your configuration, make sure you are in the API_HANDLER FOLDER)
```
docker build -t my-flask-app .
```
**If running on another machine**

To save the image: (may or may not need sudo depending on your configuration)
```
docker save -o my-flask-app.tar my-flask-app:latest
```
To load in another machine: (may or may not need sudo depending on your configuration)
```
docker load -i my-flask-app.tar
```
To run: (may or may not need sudo depending on your configuration)
```
docker run -d   -p 5000:5000   --name my-flask-container   my-flask-app   .venv/bin/python -m gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app
```

**Configuring Nginx**

**Note**: NGINX must be installed, and you must have a valid DNS pointing to your IP. Make sure to change the DNS in the config file.
          

The following commands should do the trick for you:
```
sudo mv nginx_config /etc/nginx/sites-available/flask_app
sudo ln -s /etc/nginx/sites-enabled/flask_app /etc/nginx/sites-available/flask_app
sudo systemctl start nginx
```
**Configuring TLS (to enable traffic over HTTPS)**

```
sudo certbot --nginx -d YOUR_DUCK_DNS
```

**Adding Cron Jobs (to enable the server is up after reboot)**

```crontab -e```

Then add the following line for your user: (make sure your script it executable and updated with your DNS)

```
@reboot YOUR_PATH_TO_YOUR_DUCKDNS_UPDATE_SCRIPT
```

Then switch to root with: 

```sudo su```

```crontab -e```

Then add the following line for the system user: (make sure the container was manually created at least once)

```
@reboot /usr/bin/systemctl start nginx
@reboot /usr/bin/docker start my-flask-container
```
**Congratulations!! Your API is available at your domain**


