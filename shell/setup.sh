# systemctl stop nginx
# cp /home/pi/pilotmap/pilotmap/etc/nginx/app.conf /etc/nginx/sites-available
# ln /etc/nginx/sites-available/app.conf /etc/nginx/sites-enabled/
# rm /etc/nginx/sites-available/default
# rm /etc/nginx//sites-enabled/default

cp /home/pi/pilotmap/pilotmap/src/* /usr/local/src

cp /home/pi/pilotmap/pilotmap/etc/system/weather.service /etc/systemd/system/
chmod 644 /etc/systemd/system/weather.service

cp /home/pi/pilotmap/pilotmap/etc/system/lights.service /etc/systemd/system/
chmod 644 /etc/systemd/system/lights.service

systemctl daemon-reload

systemctl start weather.service
systemctl start lights.service

systemctl enable lights.service
systemctl enable weather.service

# systemctl restart nginx
