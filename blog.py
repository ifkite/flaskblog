import models
from flask import Blueprint
from flask import render_template,url_for
from flask import Flask,abort,request,redirect,jsonify

blog = Blueprint('blog',__name__)
app = Flask(__name__)
datapost = models.DataPost()
dataquery = models.DataQuery()
app.config.from_object('config')


@blog.route('/',defaults={'page':1})
@blog.route('/home/',defaults={'page':1})
@blog.route('/home/<int:page>')
def home(page):
    """
        return blog title, signature, search
        return slugs and pagenation
    """
    sess=models.Session()
    articles=dataquery.get_recent_articles(sess,(page-1)*app.config['PER_PAGE'],\
                                        app.config['PER_PAGE'])
    article_num=dataquery.get_articles_num(sess)
    sess.close()

    pages,mod=divmod(article_num['num'],app.config['PER_PAGE'])
    if mod:
        pages+=1
    return render_template('index.html',\
                            intro=app.config['INTRO'],\
                            articles=articles,\
                            pages=range(1,pages+1))

@blog.route('/archive/',defaults={'arch':'date'})
@blog.route('/archive/<string:arch>')
def archive(arch):
    """ 
        return blog title,signature, search
        return statistics on time,
        on tags and directories
    """
    sess=models.Session()
    if arch == "date":
        articles=dataquery.get_articles_by_date(sess)
        sess.close()
        article_date={}
        for article in articles:
            if not article_date.has_key(article['c_time']):
                article_date[article['c_time']]=[]
            article_date[article['c_time']].append(article)
        return render_template('arch.html',article_date=article_date,arch=arch)

    elif arch == "category":
        categories=dataquery.get_all_categories(sess)
        article_cate={}
        for category in categories:
            aids=dataquery.get_articles_by_cid(sess,category['cid'])
            for aid in aids:
                article=dataquery.get_article_by_aid(sess,aid)
                if not article_cate.has_key(category['cname']):
                    article_cate[category['cname']]=[]
                article_cate[category['cname']].append(article)
        sess.close()
        return render_template("arch.html",article_cate=article_cate,arch=arch)

    elif arch == "tag":
        tags=dataquery.get_all_tags(sess)
        article_tag={}
        for tag in tags:
            aids=dataquery.get_articles_by_tid(sess,tag['tid'])
            for aid in aids:
                article=dataquery.get_article_by_aid(sess,aid)
                if not article_tag.has_key(tag['tname']):
                    article_tag[tag['tname']]=[]
                article_tag[tag['tname']].append(article)
        sess.close()
        return render_template("arch.html",article_tag=article_tag,arch=arch)
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
    sess=models.Session()
    article=dataquery.get_article_by_aid(sess,aid)
    if article:
        next=dataquery.get_next(sess,article['update_time'])
        prev=dataquery.get_prev(sess,article['update_time'])
        cids=dataquery.get_article_cids(sess,aid)
        tids=dataquery.get_article_tids(sess,aid)
        cate_dict={}
        for cid in cids:
            cname=dataquery.get_cname(sess,cid['cid'])
            if cname:
                cate_dict.update({cid['cid']:cname['cname']})

        tag_dict={}
        for tid in tids:
            tname=dataquery.get_tname(sess,tid['tid'])
            if tname:
                tag_dict.update({tid['tid']:tname['tname']})

        sess.close()
        return render_template('post.html',article=article,\
                               cate_dict=cate_dict,tag_dict=tag_dict,\
                               next=next,prev=prev)
    else:
        sess.close()
        abort(404)
    """
        show title, article, author, tag, directories, rank, comment
        **related articles**
        more:picture with shaddow
    """

@blog.route('/publish/<int:aid>',methods=['GET','POST'])
@blog.route('/publish',methods=['GET','POST'])
def publish(aid=None):
    if request.method == 'POST':
        title=request.form.get('title')
        slug=request.form.get('slug')
        content=request.form.get('content')
        categories=request.form.get('category').split(app.config['CATE_SEP'])
        tags=request.form.get('tag').split(app.config['TAG_SEP'])
        sess=models.Session()
        if aid is None:
            aid=datapost.ins_new_article(sess,title,slug,content)
            for category in categories:
                if category:
                    cid=dataquery.get_cid(sess,category)
                    if cid is None:
                        cid=datapost.ins_cate(sess,category)
                        datapost.attach_cate(sess,aid,cid)
                    else:
                        datapost.attach_cate(sess,aid,cid['cid'])
            for tag in tags:
                if tag:
                    tid=dataquery.get_tid(sess,tag)
                    if tid is None:
                        tid=datapost.ins_tag(sess,tag)
                        datapost.attach_tag(sess,aid,tid)
                    else:
                        datapost.attach_tag(sess,aid,tid['tid'])
        else:
            datapost.update_article(sess,aid,title,slug,content)
        sess.commit()
        sess.close()

        if aid is None:
            return redirect('/home')
        else:
            return redirect(url_for('blog.article',aid=aid))

    if aid is None:
        return render_template('publish.html',aid=aid)
    else:
        sess=models.Session()
        article=dataquery.get_article_by_aid(sess,aid)
        sess.close()
        return render_template('publish.html',aid=aid,article=article)

@blog.route('/_comment',methods=["GET","POST"])
def comment():
    author = request.form.get('author','no author',type=str)
    email = request.form.get('email','no email',type=str)
    content = request.form.get('comment','no content',type=str)
    return jsonify(comment_html=render_template('comment.html',\
                   author=author,content=content))

#@blog.route('backdoor')
#def backdoor():
#    """
#        hidden login
#    """
#    pass

#@blog.route('about')
#def about():
#    """
#        self introduction
#    """

#@blog.errorhandler('/404')
#def notfound():
#    pass

app.register_blueprint(blog)
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',port=8080)
