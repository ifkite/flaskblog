from datetime import datetime as date
from flask import Blueprint
from flask import render_template,url_for,make_response,g
from flask import abort,request,redirect,jsonify,flash
from flask import Markup
from wtforms import fields, widgets,validators
from flask.ext import admin
from flask.ext.admin.contrib import sqla
from flask.ext import login, admin
from flask.ext.admin import helpers, expose
from werkzeug.security import check_password_hash
from models import (Article, Category, Tag, DataQuery)
from utils import app, db
from bs4 import BeautifulSoup

blog = Blueprint('blog', __name__)

dataquery = DataQuery()


@blog.route('/', defaults={'page': 1})
@blog.route('/home/', defaults={'page': 1})
@blog.route('/home/<int:page>')
def home(page):
    articles = dataquery.get_recent_articles(start_artcle=(page - 1) * app.config['PER_PAGE'],
                                             per_page=app.config['PER_PAGE'])
    article_num = dataquery.get_articles_num()
    idx_contents = []
    for art in articles:
        soup = BeautifulSoup(art.content)
        if soup.h1:
            idx_contents.append({"title": Markup(soup.h1), "aid": art.aid})
    pages, mod = divmod(article_num, app.config['PER_PAGE'])
    if mod:
        pages += 1
    return render_template('index.html',
                           intro=app.config['INTRO'],
                           idx_contents=idx_contents,
                           pages=range(1, pages + 1))


@blog.route('/archive/')
@blog.route('/archive/<string:arch>/')
@blog.route('/archive/<string:arch>/<string:para>/')
@blog.route('/archive/<string:arch>/<string:para>/<int:pages>')
def archive(arch=None, para=None, pages=1):
    """
        return blog title,signature, search
        return statistics on time,
        on tags and directories
    """
    if not arch and not para:
        flash('arch and para is none')
        return redirect(url_for('blog.home'))
    #table driven,use dict alternative
    elif arch not in app.config['ITEMS']:
        flash(arch + ' is literal text')
        return redirect(url_for('blog.home'))
    elif not para:
        if arch == "date":
            articles = dataquery.get_articles_with_date()
            article_date = {}
            for article in articles:
                if not article_date.has_key(article.create_time.strftime('%Y %B')):
                    article_date[article.create_time.strftime('%Y %B')] = []
                article_date[article.create_time.strftime('%Y %B')].append(article)
            pages = 0
            return render_template('arch.html', article_date=article_date,
                                   arch=arch, pages=pages, intro=app.config['INTRO'])
        elif arch == "category":
            categories = dataquery.get_all_categories()
            pages = 0
            return render_template("arch.html", categories=categories,
                                   arch=arch, pages=pages, intro=app.config['INTRO'])
        elif arch == "tag":
            tags = dataquery.get_all_tags()
            pages = 0
            return render_template("arch.html", tags=tags,
                                   arch=arch, pages=pages, intro=app.config['INTRO'])
        else:
            abort(404)
    else:
        if arch == "date":
            #ISSUE here
            articles = dataquery.get_articles_by_date(para)
            if articles:
                pages = 0
                return render_template('index.html',
                                       intro=app.config['INTRO'],
                                       articles=articles,
                                       pages=range(1, pages + 1))
            else:
                abort(404)
        elif arch == "category":
            articles = dataquery.get_articles_by_cname(para)
            if articles:
                pages = 0
                return render_template('index.html',
                                       intro=app.config['INTRO'],
                                       articles=articles,
                                       pages=range(1, pages + 1))
            else:
                abort(404)
        else:
            articles = dataquery.get_articles_by_tname(para)
            if articles:
                pages = 0
                return render_template('index.html',
                                       intro=app.config['INTRO'],
                                       articles=articles,
                                       pages=range(1, pages + 1))
            else:
                abort(404)


@blog.route('/search')
def search():
    """
        search by key words in title, or tags, or directories,
    """
    search_article = dataquery.search_article(q=request.args.get('q'))
    pages = 0
    return render_template('index.html',
                           intro=app.config['INTRO'],
                           articles=search_article,
                           pages=range(1, pages + 1))


@blog.route('/article/<int:aid>')
def article(aid):
    #what if aid not exists
    article = dataquery.get_article_by_aid(aid=aid)
    if article:
        # page_next = dataquery.get_next(update_time=article.update_time)
        # page_prev = dataquery.get_prev(update_time=article.update_time)
        # categories = dataquery.get_article_categories(aid=article.aid)
        # tags = dataquery.get_article_tags(aid=article.aid)
        # return render_template('article.html', article=article,
        #                        categories=categories, tags=tags,
        #                        next=page_next, prev=page_prev)
        return render_template('article.html', article=Markup(article.content))
    else:
        abort(404)


@blog.route('/publish/<int:aid>', methods=['GET', 'POST'])
@blog.route('/publish', methods=['GET', 'POST'])
#@login.login_required
def publish(aid=None):
    if request.method == 'POST':
        content = request.form.get('content')
        if aid is None:
            article = Article(content=content)
        else:
            article = Article.query.filter_by(aid=aid).first()
            article.content = content
            article.update_time = date.utcnow()
        db.session.add(article)
        db.session.flush()
        db.session.commit()
        # create
        if aid is None:
            return redirect('/home')
        # edit
        else:
            return redirect(url_for('blog.article', aid=aid))

    # GET method
    else:
        # create
        if aid is None:
            return render_template('publish.html')
        #edit
        else:
            article = Article.query.filter_by(aid=aid).first()
            return render_template('publish.html', aid=aid, article=article)

@blog.route('/delete/<int:aid>')
def delete(aid):
    article = dataquery.get_article_by_aid(aid)
    if article:
        article.is_delete = True
    return redirect(url_for('blog.home'))

@blog.route('/_comment',methods=["GET", "POST"])
def comment():
    author = request.form.get('author', 'no author', type=str)
    email = request.form.get('email', 'no email', type=str)
    content = request.form.get('comment', 'no content', type=str)
    #aid = request.form.get('aid',type=int)
    #datapost.ins_comment(aid, author, content)
    return jsonify(comment_html=
                   render_template('comment.html', author=author, content=content))

#@blog.route('backdoor')
#    pass

#@blog.route('about')
#def about():
#    """
#        self introduction
#    """

# @blog.errorhandler('/404')
# def not_found():
#     return 'page not found'

#class PageAdmin(sqla.ModelView):
#    form_overrides = dict(text=CKTextAreaField)
#    create_template = 'create.html'
#    edit_template = 'edit.html'

# def init_login():
#     login_manager = login.LoginManager()
#     login_manager.init_app(app)
#     login_manager.login_view='blog.login_view'
#     # Create user loader function
#     @login_manager.user_loader
#     def load_user(user_id):
#         sess = models.Session()
#         user = sess.query(models.User).get(user_id)
#         sess.close()
#         return user

# @blog.route("/login", methods=["GET", "POST"])
# def login_view():
#     login_form = models.LoginForm()
#     #if helpers.validate_form_on_submit(login_form):
#     if request.method == 'POST':
#         #user = login_form.get_user()
#         sess = models.Session()
#         login_user = dataquery.get_user(sess, username=request.form['username'])
#         sess.close()
#         if login_user is None:
#             raise validators.ValidationError("no such user")
#         if not check_password_hash(login_user.password, request.form.get("password")):
#             raise validators.ValidationError("error password")
#         login.login_user(login_user)
#         flash("login successful")
#         return redirect(request.args.get("next") or url_for('blog.publish'))
#     return render_template("login.html", login_form=login_form)

#@blog.route("/logout")
#@login.login_required
#def logout():
#    login.logout_user()
#    return redirect(url_for("blog.home"))
# init_login()

app.register_blueprint(blog)
if __name__ == '__main__':
    app.debug = True
    #admin = admin.Admin(app, name="Example: WYSIWYG")
    #admin.add_view(PageAdmin(Page, db.session))
    app.run(host='0.0.0.0', port=8080)