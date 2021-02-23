from app import app
from flask import render_template, flash, request, redirect, url_for
from app.forms import Form
from app.control import ctrl

# all commands, english and chinese
CMD_LIST = [
    ('aboutYou', '關於你',),
    ('request', '要求',),
    ('beauty_care', '美容',),
    ('choose', '選擇',),
    ('else_recommend', '推薦其他',),
    ('goodbye', '道別',),
    ('greeting', '打招呼',),
    ('help_decision', '幫助選擇',),
    ('inform', '告知',),
    ('noidea', '不知道',),
    ('react', '使用者回饋',),
    ('reset', '清除',),
    ('search_item', '尋找物件',),
    ('search_makeup', '尋找妝容',),
    ('skinBad', '皮膚不好',),
    ('thanks', '感謝',),
]

@app.route('/', methods=['GET', 'POST'])
def index():
    form = Form()           # flask form
    pattern_string = ""     # pattern string
    resp_string = ""        # response string

    get_item = False        # whether getting item info (bool)
    pattern = request.args.get('pattern')
    suggestions = []        # all the possible patterns(suggestion) corresponding to the intention 
                            # user can refer to the suggestion to formulate their own responses
    item_list = []
    if pattern: 
        # if ?pattern=..., means user have clicked on a intention button
        # -> display all possible patterns
        sug = ctrl.intent_pattern[pattern]
        for s in sug:
            if s.find('name') == -1:  # filter those pattern with 'name' in it, because it will greatly slow down the parsing process
                suggestions.append(s) 


    if form.validate_on_submit():               # if we have submit the form
        command = form.inputtext.data           # the string user inputted
        flash('已輸入指令: {}'.format(command))   # using flask flash() function, later render the message in html

        # controller get the command, and return the intent, the pattern, whether get item,
        # the retrived item list and the response string
        intent_string, pattern_string, get_item, item_list, resp_string = ctrl.control(command)

        # get chinese intent string
        zh_string = ""
        for k in CMD_LIST:
            if k[0] == intent_string:
                zh_string = k[1]

        # using flask flash() function, later render the message in html
        # displaying both pattern and intention
        flash('Intention: {} {}'.format(intent_string, zh_string))
        flash('Pattern:   {}'.format(pattern_string))

        print(intent_string)
        return render_template('index.html', title='Intention Demo', form=form, intent=intent_string, cmd_list=CMD_LIST, suggestions=suggestions, get_item=get_item, item_list=item_list, resp_string=resp_string)
    return render_template('index.html', title='Intention Demo', form=form, intent="", cmd_list=CMD_LIST, suggestions=suggestions, get_item=get_item, item_list=item_list, resp_string=resp_string)

@app.route('/items', methods=['GET', 'POST'])
def items():
    num_form = (len(request.form))//3
    print(num_form)
    item_list = []
    form_table = request.form.to_dict(flat=False)  # form converted to type of [ython dictionary 
    print('table', form_table)
    for i in range(num_form):
        item_list.append((form_table['brand-%d'%i], form_table['name-%d'%i], form_table['image-%d'%i])) 
        # item_list is a list of products, each element contains its brand, name and image

    return render_template('items.html', item_list = item_list)


