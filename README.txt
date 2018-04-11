# Commands (need to do this first for Windows)
set FLASK_APP=C:\Users\liuyu\source\repos\fin_sys_tech_project\app.py
set FLASK_APP=C:\Users\Justin\PycharmProjects\fin_sys_tech_project\app.py

--Mac
export FLASK_APP=/Users/yelaoda/Desktop/fin_sys_tech_project/app.py

Users/yelaoda/Desktop
# Run Application
flask run


# Create User
flask shell
>>> u = User(username='susan', email='susan@example.com')
>>> u.set_password('cat')
>>> db.session.add(u)
>>> db.session.commit()


# Setup Database
--Creates Migration Repository
flask db init
--Database Migration
flask db migrate
flask db migrate -m "users table"

--Upgrade database
flask db upgrade

--Rollback Database
flask db downgrade


--STEVENS SERVER
155.246.104.19
login:fe595green
password:fe595


--ipython3
mongo --host 155.246.104.19


--VPN
https://sit.teamdynamix.com/TDClient/KB/ArticleDet?ID=805
Server:	155.246.151.12
155.246.82.169


-- update project
MAC- command t （merge）

Push changes
MAC- command k (COMMIT)
      command + shift + k (Push)

