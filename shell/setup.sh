set -x
systemctl stop nginx
cp /home/pi/pilotmap/etc/nginx/app.conf /etc/nginx/sites-available
ln /etc/nginx/sites-available/app.conf /etc/nginx/sites-enabled/
rm /etc/nginx/sites-available/default
rm /etc/nginx//sites-enabled/default

cp -r /home/pi/pilotmap/src/* /usr/local/src

cp /home/pi/pilotmap/etc/systemd/weather.service /etc/systemd/system/
cp /home/pi/pilotmap/etc/systemd/weather.timer /etc/systemd/system/
chmod 644 /etc/systemd/system/weather.service

cp /home/pi/pilotmap/etc/systemd/lights.service /etc/systemd/system/
chmod 644 /etc/systemd/system/lights.service

cp /home/pi/pilotmap/etc/systemd/display.service /etc/systemd/system/
chmod 644 /etc/systemd/system/display.service


systemctl daemon-reload

systemctl start weather.service
systemctl start weather.timer

systemctl start lights.service
systemctl start display.service

systemctl enable weather.service
systemctl enable weather.timer

systemctl enable lights.service
systemctl enable display.service

# systemctl restart nginx
