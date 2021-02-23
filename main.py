from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/', methods=['POST'])
def upload():
    output = request.values['news']
    print(output)
    return render_template("index.html", res=output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777, threaded=True, debug=True)
