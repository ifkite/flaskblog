from datetime import datetime as date
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (MetaData, ForeignKey, Column, Integer,\
String, Text, DateTime)
from sqlalchemy.orm import sessionmaker
from wtforms import form, fields, validators
from werkzeug.security import check_password_hash
from lru import cached, fresh
import threading

engine = create_engine('mysql+mysqldb://pyblog_admin:@localhost/pyblog',\
                       encoding='utf-8')
metadata = MetaData()
Base = declarative_base()
Session = sessionmaker(bind=engine)
sess = Session()
class DataQuery:
#PASSED
    def __init__(self):
        self.cache_general = {}

    @cached('article_aid')
    def get_article_by_aid(self, aid):
        #article = sess.query(Article).filter_by(aid=aid).one()
        article = sess.execute("select aid,title,slug,content, \
                                create_time,update_time \
                                from article \
                                where aid=:aid",{"aid": aid}).fetchone()
        return article

    def get_articles_num(self):
        article_num = sess.execute("select count(*) as num\
                                    from article").fetchone()
        return article_num

    def get_articles_by_cid(self, cid):
        article_categories = sess.query(Article_category).filter_by(cid=cid).all()
        for article_category in article_categories:
            yield article_category.aid

#PASSED
    def get_articles_by_tid(self, tid):
        article_tags = sess.query(Article_tag).filter_by(tid=tid).all()
        for article_tag in article_tags:
            yield article_tag.aid


    def get_articles_with_date(self):
        articles = sess.execute("select aid,title,content,\
                                 concat(year(create_time),month(create_time)) \
                                 as c_time \
                                 from article \
                                 order by update_time desc"
                               ).fetchall()
        for article in articles:
            yield article

    @cached('article_date')
    def get_articles_by_date(self, para_date):
        return sess.execute("select * \
                             from article \
                             where concat(year(update_time),month(update_time))= :para_date",
                             {'para_date': para_date}).fetchall()


    def get_next(self, update_time):
        aid_title = sess.execute("select aid,title \
                            from article \
                            where update_time < :update_time \
                            order by update_time desc",
                            {'update_time': update_time}).fetchone()
        return aid_title


    def get_prev(self, update_time):
        aid_title = sess.execute("select aid,title \
                            from article \
                            where update_time > :update_time \
                            order by update_time asc",
                            {'update_time': update_time}).fetchone()
        return aid_title


    def get_recent_articles(self, start_artcle, per_page):
        articles = sess.execute("select aid, title,slug, content, create_time, update_time\
                                 from article\
                                 order by update_time desc\
                                 limit :start_artcle, :per_page",
                                     {"start_artcle": start_artcle,
                                      "per_page": per_page}
                               ).fetchall()
        return articles

    def get_num_by_date(self):
        aid_counts = sess.execute("select year(update_time),\
                                          month(update_time), count(aid)\
                                   from article\
                                   group by\
                                   year(update_time),month(update_time)").fetchall()
        #need to test and modify
        return aid_counts

    def get_num_by_categoty(self, cid):
        aid_counts = sess.execute("select count(aid),cid\
                                   from article_category\
                                   group by :cid",{"cid":cid}).fetchall()
        return aid_counts

    def get_num_by_tag(self, tid):
        aid_counts = sess.execute("select count(aid), tid\
                                   from article_tag\
                                   group by :tid",{"tid": tid}).fetchall()
        return aid_counts

#PASSED
    @cached('cids', lru_length=32)
    def get_article_cids(self, aid):
        cids = sess.execute("select cid\
                             from article_category\
                             where aid=:aid",{"aid": aid}).fetchall()
        return cids

    @cached('tids', lru_length=32)
    def get_article_tids(self, aid):
        tids = sess.execute("select tid\
                             from article_tag\
                             where aid= :aid",{"aid": aid}).fetchall()
        return tids

#PASSED
    def get_tag(self, tid):
        tname = sess.execute("select tname\
                            from tag\
                            where tid=:tid",{"tid": tid}).fetchone()
        #return ('tname blah',)
        return tname

    def get_all_tags(self):
        tags = sess.execute("select distinct tid,tname\
                             from tag").fetchall()
        for tag in tags:
            yield tag

    def get_tid(self, tname):
        tid = sess.execute("select tid\
                            from tag\
                            where tname=:tname",{"tname": tname}).fetchone()
        return tid

    @cached('cname')
    def get_cname(self, cid):
        cname = sess.execute("select cname\
                              from category\
                              where cid=:cid",{"cid":cid}).fetchone()
        return cname

    @cached('tname')
    def get_tname(self, tid):
        tname = sess.execute("select tname\
                              from tag\
                              where tid=:tid",{"tid": tid}).fetchone()
        return tname

    def get_all_categories(self):
        categories = sess.execute("select distinct cid,cname\
                                   from category").fetchall()
        for category in categories:
            yield category

    def get_cid(self, cname):
        cid = sess.execute("select cid\
                            from category\
                            where cname=:cname",{"cname": cname}).fetchone()
        return cid

    def get_user(self, username):
        return sess.query(User).filter_by(username=username).first()

    #@cached('comments', lru_length=128)
    def get_comments_by_aid(self, aid):
        comments = sess.execute("select comment_id, aid,\
                                 com_content, create_time, update_time, author\
                                 from comment\
                                 where aid=:aid\
                                 order by create_time asc", {"aid": aid}).fetchall()
        return comments


class DataPost:
    def ins_new_article(self, title, slug, content):
        """
        MySql expression
        -- $(var) stands for argument
            INSERT INTO article(title,content,create_time,update_time) \
                VALUES($(title),$(content),$(date.utcnow),\
                     $(date.utcnow))
        """
        article = Article(title=title, content=content, slug=slug,
                              create_time=date.now(),
                              update_time=date.now())
        sess.add(article)
        sess.commit()
        return article.aid

    def modify_article(self, aid, title, slug, content):
        sess.execute("update article set title=:title,slug=:slug,\
                      content=:content,update_time:=update_time \
                      where aid=:aid",{"title": title,"slug": slug,
                      "content": content,"update_time": date.now(),
                      "aid": aid}
                    )
        sess.commit()
        fresh('article_aid', aid)
        dataquery = DataQuery()
        dataquery.get_comments_by_aid(aid=aid)

    def ins_cate(self, cname):
        category = Category(cname=cname)
        sess.add(category)
        sess.commit()
        return category.cid

    def modify_cate(self, cid, cname):
        sess.execute("update category set cname=:cname where cid=:cid",
                     {"cname": cname,"cid": cid})
        sess.commit()
        fresh('cname', cid)
        dataquery = DataQuery()
        dataquery.get_cname(cid=cid)

    def attach_cate(self, aid, cid):
        article_category=Article_category(aid=aid,cid=cid)
        sess.add(article_category)
        sess.commit()
        fresh('cids',aid)
        dataquery = DataQuery()
        dataquery.get_article_cids(aid=aid)

#PASSED
    def ins_tag(self, tname):
        tag = Tag(tname=tname)
        sess.add(tag)
        sess.commit()
        return tag.tid

    def modify_tag(self, tid, tname):
        sess = Session()
        sess.execute("update tag set tname=:tname where tid=:tid",
                     {"tname": tname, "tid": tid})
        sess.commit()
        fresh('tname', tid)
        dataquery = DataQuery()
        dataquery.get_tname(tid=tid)

#PASSED
    def attach_tag(self, aid, tid):
        article_tag = Article_tag(aid=aid, tid=tid)
        sess.add(article_tag)
        sess.commit()
        fresh('tids', aid)
        dataquery = DataQuery()
        dataquery.get_article_tids(aid=aid)

    def ins_comment(self, aid, author, com_content):
        comment = Comment(aid=aid, com_content=com_content, author=author,
                          create_time=date.utcnow(),
                          update_time=date.utcnow())
        sess.add(comment)
        sess.commit()
        fresh('comments', aid)
        dataquery = DataQuery()
        dataquery.get_comments_by_aid(aid=aid)
        return comment.comment_id

    def modify_comment(self, aid, com_content):
        sess.execute("update comment set com_content=:com_content,\
                      update_time=:update_time where aid=:aid",
                      {"com_content": com_content,"update_time": date.utcnow(),
                      "aid": aid})
        sess.commit()

    def ins_comment_reply(self, comment_id, reply_to_id):
        reply = Reply(comment_id=comment_id, reply_to_id=reply_to_id)
        sess.add(reply)
        sess.commit()

class Article(Base):
    __tablename__ = 'article'
    aid = Column(Integer, primary_key=True,
                 nullable=False, autoincrement=True)
    #permalink = Column(String,nullable=False)
    slug = Column(Text, nullable=False)
    title = Column(String(255), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False,
                        default=date.utcnow())
    update_time = Column(DateTime, nullable=True,
                         default=date.utcnow())
    #visable column not in Article table
    #visable = Column(BOOLEAN,nullable=False,default=True)

class Comment(Base):
    __tablename__ = 'comment'
    comment_id = Column(Integer, primary_key=True,
                        nullable=False, autoincrement=True)
    aid = Column(Integer, ForeignKey('article.aid'),
                 nullable=False)
    author = Column(String(128), nullable=False)
    com_content = Column(Text, nullable=False)
    create_time = Column(DateTime, nullable=False,
                        default=date.utcnow())
    update_time = Column(DateTime, nullable=True,
                         default=date.utcnow())

class Reply(Base):
    __tablename__ = 'reply'
    comment_id = Column(Integer, ForeignKey('comment.comment_id'),
                        primary_key=True, nullable=False)
    reply_to_id = Column(Integer, ForeignKey('comment.comment_id'),
                         primary_key=True, nullable=False, unique=True)

class User(Base):
    __tablename__ = 'user'
    uid = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    email = Column(String(256), nullable=False, unique=True)
    password = Column(String(64), nullable=False, unique=False)

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
        sess = Session()
        user = sess.query(User).filter_by(username=self.username.data).first()
        return user

class User_comment(Base):
    __tablename__ = 'user_comment'
    user_id = Column(Integer, ForeignKey('user.uid'),
                     primary_key=True,nullable=False)
    comment_id = Column(Integer, ForeignKey('comment.comment_id'),
                        nullable=True)

class Tag(Base):
    __tablename__ = 'tag'
    tid = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tname = Column(String(255), nullable=False, unique=True)

class Article_tag(Base):
    __tablename__ = 'article_tag'
    aid = Column(Integer, ForeignKey('article.aid'), primary_key=True, nullable=False)
    tid = Column(Integer,ForeignKey('tag.tid'), primary_key=True, nullable=False)

class Category(Base):
    __tablename__ = 'category'
    cid = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    cname = Column(String(255), nullable=False, unique=True)

class Article_category(Base):
    __tablename__ = 'aritcle_category'
    aid = Column(Integer, ForeignKey('article.aid'), primary_key=True, nullable=False)
    cid = Column(Integer, ForeignKey('category.cid'), primary_key=True, nullable=False)

#class ArticleForm(Form):
#    title=StringField(label=u'title',validators=[InputRequired()]))

#    content=TextAreaField(label=u'content',validators=[InputRequired()])

Base.metadata.create_all(engine)