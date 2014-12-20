import models
from flask import Blueprint
from flask import render_template,url_for,make_response,g
from flask import Flask,abort,request,redirect,jsonify,flash
from wtforms import fields, widgets,validators
from flask.ext import admin
from flask.ext.admin.contrib import sqla
from flask.ext import login, admin
from flask.ext.admin import helpers, expose
from werkzeug.security import check_password_hash
blog = Blueprint('blog', __name__)
app = Flask(__name__)
datapost = models.DataPost()
dataquery = models.DataQuery()
app.config.from_object('config')
#show articles by date
#show articles by category
#show articles by tag
@blog.route('/', defaults={'page':1})
@blog.route('/home/', defaults={'page':1})
@blog.route('/home/<int:page>')
def home(page):
    """
        return blog title, signature, search
        return slugs and pagenation
    """
    sess = models.Session()
    #if not cache.has_key('articles'):
    articles = dataquery.get_recent_articles(sess,(page-1)*app.config['PER_PAGE'],
                                        app.config['PER_PAGE'])
        #cache['articles']=articles
    article_num = dataquery.get_articles_num(sess)
    sess.close()

    pages,mod = divmod(article_num['num'],app.config['PER_PAGE'])
    if mod:
        pages += 1
    return render_template('index.html',
                            intro=app.config['INTRO'],
                            articles=articles,
                            pages=range(1,pages+1))

#list all tag
#list all category
#list all date
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
    if arch is None and para is None:
        flash('arch and para is none')
        return redirect(url_for('blog.home'))
    #table driven,use dict alternative
    elif arch not in app.config['ITEMS']:
        flash(arch + ' is literial text')
        return redirect(url_for('blog.home'))
    elif para == None:
        sess = models.Session()
        if arch == "date":
            articles = dataquery.get_articles_with_date(sess)
            sess.close()
            article_date = {}
            for article in articles:
                if not article_date.has_key(article['c_time']):
                    article_date[article['c_time']] = []
                article_date[article['c_time']].append(article)
            sess.close()
            pages = 0
            return render_template('arch.html', article_date=article_date,
                                   arch=arch, pages=pages, intro=app.config['INTRO'])
        elif arch == "category":
            categories = dataquery.get_all_categories(sess)
            article_cate = {}
            for category in categories:
                aids = dataquery.get_articles_by_cid(sess,category['cid'])
                for aid in aids:
                    article = dataquery.get_article_by_aid(sess,aid)
                    if not article_cate.has_key(category['cname']):
                        article_cate[category['cname']] = []
                    article_cate[category['cname']].append(article)
            sess.close()
            pages = 0
            return render_template("arch.html", article_cate=article_cate,
                                   arch=arch, pages=pages, intro=app.config['INTRO'])
        elif arch == "tag":
            tags = dataquery.get_all_tags(sess)
            article_tag = {}
            for tag in tags:
                aids = dataquery.get_articles_by_tid(sess,tag['tid'])
                for aid in aids:
                    article = dataquery.get_article_by_aid(sess,aid)
                    if not article_tag.has_key(tag['tname']):
                        article_tag[tag['tname']] = []
                    article_tag[tag['tname']].append(article)
            sess.close()
            pages = 0
            return render_template("arch.html", article_tag=article_tag,
                                   arch=arch, pages=pages, intro=app.config['INTRO'])
        else:
            abort(404)
    else:
        sess = models.Session()
        if arch == "date":
            #ISSUE here
            articles = dataquery.get_articles_by_date(sess,para)
            sess.close()
            pages = 0
            return render_template('index.html',
                                    intro=app.config['INTRO'],
                                    articles=articles,
                                    pages=range(1,pages+1)
                                  )
        elif arch == "category":
            cid = dataquery.get_cid(sess,para)
            if cid:
                aids = dataquery.get_articles_by_cid(sess,cid['cid'])
                article_list = []
                for aid in aids:
                    article_list.append(dataquery.get_article_by_aid(sess,aid))
                sess.close()
                pages = 0
                return render_template('index.html',
                                       intro=app.config['INTRO'],
                                       articles=article_list,
                                       pages=range(1,pages+1))
            else:
                abort(404)
        else:
            tid = dataquery.get_tid(sess,para)
            if tid:
                aids = dataquery.get_articles_by_tid(sess,tid['tid'])
                article_list = []
                for aid in aids:
                    article_list.append(dataquery.get_article_by_aid(sess,aid))
                sess.close()
                pages = 0
                return render_template('index.html',
                                       intro=app.config['INTRO'],
                                       articles=article_list,
                                       pages=range(1, pages+1))
            else:
                abort(404)

@blog.route('/search')
def search():
    """
        search by key words in title, or tags, or directories,
    """
    return 'search page'

@blog.route('/post/<int:aid>')
def article(aid):
    #what if aid not exists
    #TODO:alternate by dict
    sess = models.Session()
    article = dataquery.get_article_by_aid(sess,aid)
    if article:
        page_next = dataquery.get_next(sess,article['update_time'])
        page_prev = dataquery.get_prev(sess,article['update_time'])
        cids = dataquery.get_article_cids(sess,aid)
        tids = dataquery.get_article_tids(sess,aid)
        comments = dataquery.get_comments_by_aid(sess, aid)
        cate_dict = {}
        for cid in cids:
            cname = dataquery.get_cname(sess,cid['cid'])
            if cname:
                cate_dict.update({cid['cid']: cname['cname']})

        tag_dict = {}
        for tid in tids:
            tname = dataquery.get_tname(sess,tid['tid'])
            if tname:
                tag_dict.update({tid['tid']: tname['tname']})
        sess.close()
        return render_template('post.html', article=article, comments=comments,
                               cate_dict=cate_dict, tag_dict=tag_dict,
                               next=page_next, prev=page_prev)
    else:
        sess.close()
        abort(404)
    """
        show title, article, author, tag, directories, rank, comment
        **related articles**
        more:picture with shaddow
    """

@blog.route('/publish/<int:aid>', methods=['GET', 'POST'])
@blog.route('/publish', methods=['GET', 'POST'])
@login.login_required
def publish(aid=None):
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        categories = request.form.get('category').split(app.config['CATE_SEP'])
        tags = request.form.get('tag').split(app.config['TAG_SEP'])
        sess = models.Session()
        if aid is None:
            aid = datapost.ins_new_article(sess, title, slug, content)
            for category in categories:
                if category:
                    cid = dataquery.get_cid(sess, category)
                    if cid is None:
                        cid = datapost.ins_cate(sess, category)
                        datapost.attach_cate(sess, aid, cid)
                    else:
                        datapost.attach_cate(sess, aid, cid['cid'])
            for tag in tags:
                if tag:
                    tid = dataquery.get_tid(sess, tag)
                    if tid is None:
                        tid = datapost.ins_tag(sess, tag)
                        datapost.attach_tag(sess, aid, tid)
                    else:
                        datapost.attach_tag(sess, aid, tid['tid'])
        else:
            datapost.update_article(sess, aid, title, slug, content)
        sess.commit()
        sess.close()

        if aid is None:
            return redirect('/home')
        else:
            return redirect(url_for('blog.article', aid=aid))

    if aid is None:
        return render_template('publish.html', aid=aid)
    else:
        sess = models.Session()
        article = dataquery.get_article_by_aid(sess, aid)
        sess.close()
        return render_template('publish.html', aid=aid, article=article)

@blog.route('/_comment',methods=["GET", "POST"])
def comment():
    author = request.form.get('author', 'no author', type=str)
    email = request.form.get('email', 'no email', type=str)
    content = request.form.get('comment', 'no content', type=str)
    aid = request.form.get('aid',type=int)
    sess = models.Session()
    datapost.ins_comment(aid, author, content)
    sess.close()
    return jsonify(comment_html=render_template('comment.html',
                   author=author, content=content))

#@blog.route('backdoor')
#    pass

#@blog.route('about')
#def about():
#    """
#        self introduction
#    """

#@blog.errorhandler('/404')
#def notfound():
#    pass

#class CKTextAreaWidget(widgets.TextArea):
#    def __call__(self, field, **kwargs):
#        kwargs.setdefault('class_', 'ckeditor')
#        return super(CKTextAreaWidget, self).__call__(field, **kwargs)
#
#class CKTextAreaField(fields.TextAreaField):
#    widget = CKTextAreaWidget()
#
#class PageAdmin(sqla.ModelView):
#    form_overrides = dict(text=CKTextAreaField)
#    create_template = 'create.html'
#    edit_template = 'edit.html'

def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)
    login_manager.login_view='blog.login_view'
    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        sess = models.Session()
        user = sess.query(models.User).get(user_id)
        sess.close()
        return user

@blog.route("/login", methods=["GET", "POST"])
def login_view():
    login_form = models.LoginForm()
    #if helpers.validate_form_on_submit(login_form):
    if request.method == 'POST':
        #user = login_form.get_user()
        sess = models.Session()
        login_user = dataquery.get_user(sess, username=request.form['username'])
        sess.close()
        if login_user is None:
            raise validators.ValidationError("no such user")
        if not check_password_hash(login_user.password, request.form.get("password")):
            raise validators.ValidationError("error password")
        login.login_user(login_user)
        flash("login successful")
        return redirect(request.args.get("next") or url_for('blog.publish'))
    return render_template("login.html", login_form=login_form)

#@blog.route("/logout")
#@login.login_required
#def logout():
#    login.logout_user()
#    return redirect(url_for("blog.home"))

init_login()
app.register_blueprint(blog)

if __name__ == '__main__':

    app.debug = True
    #admin = admin.Admin(app, name="Example: WYSIWYG")
    #admin.add_view(PageAdmin(Page, db.session))
    app.run(host='0.0.0.0', port=8080)