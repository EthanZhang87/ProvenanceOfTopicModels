from flask import Flask,render_template, request, url_for, redirect, session
from markupsafe import Markup
import os, re
import wikipedia as wp
import topic
from collections import OrderedDict
import download
import sqlite3 as sql
import matplotlib.pyplot as plt
plt.rcParams['figure.autolayout'] = True
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import colors, colormaps

def plot_to_img():
        topic.topic_chart()
        plt.savefig("static/topicchart.png")
        plt.savefig("static/topicchart.pdf")
        topic.doc_chart()
        plt.savefig("static/docchart.png")

app = Flask(__name__,template_folder="templates", static_folder="static")
app.secret_key = "myKey"

@app.route("/")
def hello():
    import os
    print(os.getcwd())
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    global counter
    global topicId
    global a_name

    a_name = request.form.get('data')
    counter = request.form.get('count')
    topicId = request.form.get('topicId')
    articles = download.checktable(a_name)
    
    topicWord = request.form.get('topicWord')

    session['a_name'] = a_name
    
    return render_template("articles.html", rows = articles, article_length = len(articles), table_len = (len(articles))/3)

def getMainName():
    return session.get('a_name', 'Default Value')

@app.route('/topic/<int:id>', methods = ['GET', 'POST'])
def one_topic(id):
    global topics
    topic_data = topic.singleTopic(id)
    topic_data = Markup(topic_data)

    return render_template("singleTopic.html", t=topic_data, i = id)


def process_key_word(word, value):
    cmap = colormaps.get_cmap("YlGnBu")
    scaled_value = int(float(value) * 255)  
    color = colors.rgb2hex(cmap(scaled_value))
    new_word = '<mark style="background: %s ">%s</mark>' % (color + "BF", word)
    return new_word


def highlight_sentences(doc_sentences, keyValues):
    highlighted_sentences = []
    for sentence in doc_sentences:
        new_sentence = []
        for word in sentence.split():
            for k, v in keyValues.items():
                if k.lower() in word.lower():
                    word = process_key_word(word, v)
                    break
            new_sentence.append(word)
        highlighted_sentences.append(" ".join(new_sentence))
    return highlighted_sentences


@app.route('/topic/<int:topic_id>/<word>', methods = ['GET', 'POST'])
def word_topic_document(topic_id, word):
    conn = sql.connect('article_db.db', check_same_thread=False)
    c = conn.cursor()
    totalsum = 0
    global topic

    topics = topic.singleTopicGivenWord(topic_id)
    topics = Markup(topics)

    listOfKeyWords = []

    chances = topic.nameChance

    docsContaining = {}

    totalKeyWordCount = 0

    for k, v in chances.items():
        c.execute("SELECT article_title, article_content FROM documents_" + str(download.main_page_id) + " WHERE article_title = ?", (k,))
        results = c.fetchall()

        word = word.lower()

        if results:
            content = results[0][1] 

            content_words = content.split()

            for x in content_words:
                x = x.lower()
                if x == word or word in x:
                     totalKeyWordCount += 1
                    

            for x in content_words:
                x = x.lower()
                if x == word or word in x:
                    docsContaining[k] = v 
                    break


        
    for k,v in docsContaining.items():
        totalsum += v

    for k, v in docsContaining.items():
        totalCount = 0
        c.execute("SELECT article_title, article_content FROM documents_" + str(download.main_page_id) + " WHERE article_title = ?", (k,))
        results = c.fetchall()

        word = word.lower()

        if results:
            content = results[0][1] 

            content_words = content.split()

            for x in content_words:
                x = x.lower()
                if x == word or word in x:
                     totalCount += 1
        docsContaining[k] = (((v / totalsum)*100) * ((totalCount/totalKeyWordCount))) 

    docsContaining = {k: v for k, v in sorted(docsContaining.items(), key=lambda item: item[1], reverse=True)}

    a_name = session.get('a_name')

    c.execute("SELECT article_title, article_content FROM documents_" + str(download.main_page_id))
    results = c.fetchall()[0]
    



    article_c = results[1]



    sentences = article_c.split(".")

    article_sentence = ""

    for x in sentences:
        if next(iter(docsContaining)).lower() in x.lower():
            article_sentence += x
            break

    

    a_name = a_name.split()[0]

    tablename = f"words_{topic_id}_{a_name}"

    c.execute(f"SELECT article_word, article_prob FROM {tablename}")
    

    results = c.fetchall()
    article = results[0]
    keys = article[0].split()
    values = article[1].split()

    keyValues = {keys[x]: float(values[x])*100 for x in range(len(keys))}


    c.execute("SELECT article_title, article_content FROM documents_" + str(download.main_page_id) + " WHERE article_title = ?", (next(iter(docsContaining)),))
    results = c.fetchall()
    article = results[0]
    article_c = article[1].split(".")
    article_c = article_c[0:len(article_c)-2]


    #Most key words
    doc_sentence = ['','','']
    
    topSentences = {}
    for sentence in article_c:
        if word.lower() in sentence.lower():
            sentenceTotal = 0
            for k,v in keyValues.items():
                if k.lower() in sentence.lower():
                    for x in sentence.split():
                        if x.lower() == k.lower():
                            sentenceTotal += 1

            topSentences[str(sentence)] = sentenceTotal
    


    doc_sentence = sorted(topSentences.items(), key=lambda x: x[1])[-3:]

    doc_sentence = [x[0] for x in doc_sentence]

    doc_sentence = [re.sub(r'<br\s*/?>', '', sentence) for sentence in doc_sentence]

    

    doc_sentence.reverse()

    doc_sentence = highlight_sentences(doc_sentence, keyValues)

    #import pdb; pdb.set_trace()
    




    

    #Highest Probability
    doc_sentence2 = ['','','']
    
    topSentences2 = {}
    for sentence in article_c:
        if word.lower() in sentence.lower():
            sentenceTotal = 0
            for k,v in keyValues.items():
                if k.lower() in sentence.lower():
                    for x in sentence.split():
                        if x.lower() == k.lower():
                            sentenceTotal += float(v)*100

            topSentences2[str(sentence)] = sentenceTotal

    doc_sentence2 = sorted(topSentences2.items(), key=lambda x: x[1])[-3:]

    doc_sentence2 = [x[0] for x in doc_sentence2]

    doc_sentence2 = [re.sub(r'<br\s*/?>', '', sentence) for sentence in doc_sentence2]

    doc_sentence2.reverse()

    doc_sentence2 = highlight_sentences(doc_sentence2, keyValues)




    #Highest Average Probability
    doc_sentence3 = ['','','']
    
    topSentences3 = {}
    for sentence in article_c:
        if word.lower() in sentence.lower():
            sentenceTotal = 0
            sentenceLength = len(sentence)
            if sentenceLength > 0:
                for k,v in keyValues.items():
                    if k.lower() in sentence.lower():
                        for x in sentence.split():
                            if x.lower() == k.lower():
                                sentenceTotal += float(v)

                topSentences3[str(sentence)] = sentenceTotal/sentenceLength

    doc_sentence3 = sorted(topSentences3.items(), key=lambda x: x[1])[-3:]

    doc_sentence3 = [x[0] for x in doc_sentence3]

    doc_sentence3 = [re.sub(r'<br\s*/?>', '', sentence) for sentence in doc_sentence3]

    doc_sentence3.reverse()

    doc_sentence3 = highlight_sentences(doc_sentence3, keyValues)



    #Most Unique Words
    doc_sentence4 = ['','','']
    
    topSentences4 = {}
    for sentence in article_c:
        if word.lower() in sentence.lower():
            sentenceTotal = 0
            for k,v in keyValues.items():
                if k.lower() in sentence.lower():
                    sentenceTotal += 1

            topSentences4[str(sentence)] = sentenceTotal

    doc_sentence4 = sorted(topSentences4.items(), key=lambda x: x[1])[-3:]

    doc_sentence4 = [x[0] for x in doc_sentence4]

    doc_sentence4 = [re.sub(r'<br\s*/?>', '', sentence) for sentence in doc_sentence4]

    doc_sentence4.reverse()

    doc_sentence4 = highlight_sentences(doc_sentence4, keyValues)
            
    #import pdb; pdb.set_trace()



    #Highest Proportion of Sentence contains key words
    doc_sentence5 = ['','','']
    
    topSentences5 = {}
    for sentence in article_c:
        if word.lower() in sentence.lower():
            sentenceTotal = 0
            sentenceLength = len(sentence)
            if sentenceLength > 0:
                for k,v in keyValues.items():
                    if k.lower() in sentence.lower():
                        for x in sentence.split():
                            if x.lower() == k.lower():
                                sentenceTotal += len(k)

                topSentences5[str(sentence)] = sentenceTotal/sentenceLength

    doc_sentence5 = sorted(topSentences5.items(), key=lambda x: x[1])[-3:]

    doc_sentence5 = [x[0] for x in doc_sentence5]

    doc_sentence5 = [re.sub(r'<br\s*/?>', '', sentence) for sentence in doc_sentence5]

    doc_sentence5.reverse()

    doc_sentence5 = highlight_sentences(doc_sentence5, keyValues)


    return render_template("analyzeWord.html", data = docsContaining, word = word, sentence = Markup(article_sentence), doc_sentence = doc_sentence, doc_sentence2 = doc_sentence2, doc_sentence3 = doc_sentence3, doc_sentence4 = doc_sentence4, doc_sentence5 = doc_sentence5)

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


     try:
        highlight = topic.highlight_word2(id, docContent, int(topicID))
     except:
        highlight = docContent
     highlight = Markup(highlight)

    


     return render_template("singleDocument.html", doc = document, title = title, contentView = highlight)


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