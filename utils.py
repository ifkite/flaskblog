from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://pyblog_admin:@localhost/pyblog'
db = SQLAlchemy(app)