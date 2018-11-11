import logging
import os
import sqlite3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sklearn.metrics import mean_absolute_error

app = Flask(__name__)
app.secret_key = 'hostcompsecret'
db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(app.root_path, 'hostcomp.db')

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'admin')
db = SQLAlchemy(app)

testdata = None

# isort hack
if True:
    import hostcomp.views


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
