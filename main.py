from flask import Flask, render_template, request
from control import Controller
ctrl = Controller('app/pattern/intent_pattern.json', 'app/pattern/entity_info.json', 'app/pattern/styleme_new.tsv', 'app/pattern/effect2ids.json', 'app/pattern/response.json')

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")

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
    return "("+intent_string+") "+resp_string


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777, threaded=True, debug=True)
