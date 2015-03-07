from datetime import datetime
from dateutil import parser, relativedelta
from wtforms import form, fields, validators
from werkzeug.security import check_password_hash
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_
import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask.ext.whooshalchemy as whooshalchemy
from utils import app, db
from lru import cached


class DataQuery:
#PASSED
    def __init__(self):
        self.cache_general = {}

    #@cached('article_aid')
    def get_article_by_aid(self, aid):
        return Article.query.filter_by(aid=aid, is_delete=False).first()

    def get_articles_num(self):
        return Article.query.count()


    def get_next(self, update_time):
        try:
            article = Article.query.filter(Article.update_time < update_time, Article.is_delete==False).\
                order_by(Article.update_time.desc()).one()
        except NoResultFound:
            return None
        else:
            return article


    def get_prev(self, update_time):
        try:
            article = Article.query.filter(Article.update_time > update_time, Article.is_delete==False).\
                order_by(Article.update_time.asc()).one()
        except NoResultFound:
            return None
        else:
            return article

    def get_recent_articles(self, start_artcle, per_page):
        return Article.query.filter_by(is_delete=False).\
                   order_by(Article.update_time.desc())[start_artcle:start_artcle + per_page]

    def get_articles_with_date(self):
        articles = Article.query.filter_by(is_delete=False).\
            order_by(Article.update_time.desc()).all()
        return articles


    #@cached('cids', lru_length=32)
    def get_article_categories(self, aid):
        return Article.query.filter_by(aid=aid, is_delete=False).first().categories

#     @cached('tids', lru_length=32)
    def get_article_tags(self, aid):
        return Article.query.filter_by(aid=aid, is_delete=False).first().tags

    def get_all_categories(self):
        return Category.query.all()

    def get_all_tags(self):
        return Tag.query.all()

    def get_articles_by_date(self, year_month):
        try:
            start_date = parser.parse(year_month)
        except ValueError:
            return None
        else:
            start_date = start_date + relativedelta(day=1)
            end_date = start_date + relativedelta(months=1)
            return Article.query.filter(and_(Article.update_time.between(start_date,end_date),\
                                             Article.is_delete == False)).all()

    def get_articles_by_cname(self, cname):
        category = Category.query.filter_by(cname=cname, is_delete=False).first()
        if category:
            return category.articles
        else:
            return None

    def get_articles_by_tname(self, tname):
        tag = Tag.query.filter_by(tname=tname, is_delete=False).first()
        if tag:
            return tag.articles
        else:
            return None

    def search_article(self, q):
        return Article.query.filter_by(is_delete=False).whoosh_search(q).all()


categories = db.Table('categories',
                      db.Column('article_id', db.Integer, db.ForeignKey('article.aid')),
                      db.Column('category_id', db.Integer, db.ForeignKey('category.cid')))


tags = db.Table('tags',
                db.Column('article_id', db.Integer, db.ForeignKey('article.aid')),
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.tid')))


class Article(db.Model):
    __searchable__ = ['content']
    aid = db.Column(db.Integer, primary_key=True,
                    nullable=False, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False,
                            default=datetime.now())
    update_time = db.Column(db.DateTime, nullable=True,
                            default=datetime.now())
    is_delete = db.Column(db.Boolean, nullable=False, default=False)

    tags = db.relationship('Tag', secondary=tags,
                           backref=db.backref('articles', lazy='dynamic'))
    categories = db.relationship('Category', secondary=categories,
                                 backref=db.backref('articles', lazy='dynamic'))

    def __init__(self, content):
        self.content = content

    #visable column not in Article table
    #visable = Column(BOOLEAN,nullable=False,default=True)

class User(db.Model):
    #__tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(64), nullable=False, unique=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.uid

    def __unicode__(self):
        return self.username


class LoginForm(form.Form):
    username = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self,field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
        # to compare plain text passwords use
        # if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return User.query.filter_by(username=self.username.data).first()


class Tag(db.Model):
    tid = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    tname = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, tname):
        self.tname = tname


class Category(db.Model):
    cid = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    cname = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, cname):
        self.cname = cname


db.create_all()
if enable_search:
    whooshalchemy.whoosh_index(app, Article)
