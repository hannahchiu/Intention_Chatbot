from flask import Flask, render_template, request
from app import app
from app.control import ctrl

app1 = Flask(__name__)


@app.route('/')
def index():
    return render_template("index_chatbot.html")

#
# @app.route('/', methods=['POST'])
# def upload():
#     output = request.values['news']
#     print(output)
#     return render_template("index.html", res=output)


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    intent_string, pattern_string, get_item, item_list, resp_string = ctrl.control(userText)
    return resp_string


if __name__ == '__main__':
    app1.run(host='0.0.0.0', port=7777, threaded=True, debug=True)
