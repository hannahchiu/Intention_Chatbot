import json
import re

def read_json(filename):
    '''Read in a json file.'''
    with open(filename, 'r') as json_file:
        data = json.load(json_file)
    return data

def check_item(self):


regexp = r'\(([\w\|]*)\)'
patterns = read_json('intent_pattern.json')

for k, p_list in patterns.items():
    for p in p_list:
        pattern = p
        m = re.findall(regexp, p)
        if m:
            print('---------------------')
            print('pattern', p)
            print(m)
            for subreg in m:


                pattern.replace(subreg, subreg_expand)

        print('====')
        print('new pattern', pattern)