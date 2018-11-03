sudo gunicorn --access-logfile /home/ec2-user/logs/access.log --error-logfile /home/ec2-user/logs/error.log --bind 127.0.0.1:8080 wsgi:app &
