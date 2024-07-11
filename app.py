from flask import Flask,render_template, request, url_for, redirect
from markupsafe import Markup
import os, re
import wikipedia as wp
import topic
import download
import sqlite3 as sql
import matplotlib.pyplot as plt
plt.rcParams['figure.autolayout'] = True
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def plot_to_img():
        topic.topic_chart()
        plt.savefig("static/topicchart.png")
        plt.savefig("static/topicchart.pdf")
        topic.doc_chart()
        plt.savefig("static/docchart.png")

app = Flask(__name__,template_folder="templates", static_folder="static")

@app.route("/")
def hello():
    import os
    print(os.getcwd())
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    global counter
    global topicId
    a_name = request.form.get('data')
    counter = request.form.get('count')
    topicId = request.form.get('topicId')
    articles = download.checktable(a_name)
    return render_template("articles.html", rows = articles, article_length = len(articles), table_len = (len(articles))/3)

@app.route('/topic/<int:id>', methods = ['GET', 'POST'])
def one_topic(id):
    global topics
    topic_data = topic.singleTopic(id)
    topic_data = Markup(topic_data)

    return render_template("singleTopic.html", t=topic_data, i = id)

@app.route('/documents')
def get_documents():
    global topic
    documents = topic.printDocuments()
    documents = Markup(documents)

    return render_template("returnDocuments.html", d = documents)

@app.route('/documents/<int:id>', methods = ['GET', 'POST'])
def get_one_document(id):
     conn = sql.connect('article_db.db', check_same_thread=False)
     c = conn.cursor()
     global topics
     document = topic.printOneDocument(id)
     document = Markup(document)
     #contents = download.contentList[id].replace("\n", "<br>")
     #title = download.titles[id]
     #content = download.contentList[id]
     c.execute("SELECT article_title, article_content FROM documents_" + download.main_page_id)
     results = c.fetchall()
     content = results[id]
     title = content[0]
     docContent = content[1]
     topicID = request.form.get('data')
     word = "polygon"

     string_of_words = ""

     for x in docContent[1]:
        if x == "polygon":
            i = docContent[1].index(x)
            string_of_words += docContent[i-50: i]
            string_of_words += docContent[i: i+50]
    



     try:
        highlight = topic.highlight_word2(id, docContent, int(topicID))
     except:
        highlight = docContent
     highlight = Markup(highlight)

    


     return render_template("singleDocument.html", doc = document, title = title, contentView = highlight, stringOfWords = string_of_words)


@app.route('/documents/<int:id>/<int:tid>', methods = ['GET', 'POST'])
def get_one_document2(id, tid):
     conn = sql.connect('article_db.db', check_same_thread=False)
     c = conn.cursor()
     global topics
     document = topic.printOneDocument(id)
     document = Markup(document)
     #contents = download.contentList[id].replace("\n", "<br>")
     #title = download.titles[id]
     #content = download.contentList[id]
     c.execute("SELECT article_title, article_content FROM documents_" + download.main_page_id)
     results = c.fetchall()
     content = results[id]
     title = content[0]
     docContent = content[1]


     highlight = topic.highlight_word2(id, docContent, tid)
     highlight = Markup(highlight)

    


     return render_template("singleDocument.html", doc = document, title = title, contentView = highlight )


@app.route('/topic')
def topics():
    global topics
    topics = topic.main()
    topics = Markup(topics)
    docNames = topic.returnDocName()
    # Convert plot to image
    plot_to_img()

    t3Words = topic.getTopThreeWords()
    topThree = topic.topThreeProb()
    topThreeDoc = topic.topThreeDocProb()
    topic_list = topic.docTopic()


    topic_colors = ('#DAF7A6', '#FB2C00', '#00FB1B', '#FBAB00', '#000000', '#F700FF', '#001BFF','#00FFC1', '#F3FF00', '#00C9FF')
    firstTenTopics = tuple(tuple(topic_list[1]))
    
    topic_colors_list = dict(zip(firstTenTopics, topic_colors))
    #import pdb; pdb.set_trace()
    topchart = Markup(' <img src = "static/topicchart.png"> ')
    docchart = Markup(' <img src = "static/docchart.png"> ')

    return render_template("topic.html", t=topics, colorsList = topic_colors_list, docTopics = topic_list, top_img = topchart, count = len(topThreeDoc), doc_img = docchart, names = docNames,  t3 = topThree, t3Doc = topThreeDoc, t3words = t3Words, numListed = int(counter))

@app.route('/text', methods=['POST'])
def text():
    global topics
    topics = Markup(topics)
    d_index = int(request.form.get('d_id'))
    topic_index = int(request.form.get('t_id'))
    article_text = topic.get_text(d_index)
    highlight_text = topic.highlight_word(d_index, article_text, topic_index)
    highlight_text = Markup(highlight_text)
    return render_template("text.html", t = topics, a_text = highlight_text)

if __name__ == '__main__':
    app.run(debug=True, port=8080)