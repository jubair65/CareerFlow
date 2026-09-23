import pymysql

pymysql.install_as_MySQLdb()

from django.db.backends.mysql.base import DatabaseFeatures

# Support MySQL 8.0.x on Django 6.1+
DatabaseFeatures.minimum_database_version = (8, 0)

