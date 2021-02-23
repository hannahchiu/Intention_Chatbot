import re
import json
import pandas as pd
import numpy as np


def read_json(filename):
    '''Read in a json file.'''
    with open(filename, 'r') as json_file:
        data = json.load(json_file)
    return data

class Controller(object):
    """docstring for Controller"""
    def __init__(self, intent_pattern, entity_info, styleme_new, effect2ids, resp_info):
        super(Controller, self).__init__()
        self.intent_pattern = read_json(intent_pattern)
        self.entity_info = read_json(entity_info)
        self.item_info = pd.read_csv(styleme_new, sep='\t')        # styleme_new.tsv
        self.effect2ids = read_json(effect2ids)                    # effect -> all items ids belonging to the effect
        self.resp_info = read_json(resp_info)                      # 我寫的response (目前是直接回list裡的第一個)
        
        self.regex = {}
        self.prepare_regex()
        self.num_rand_product = 5
        self.neccess_info = [1, 2, 4, 6]  # brand, chinese_name, item (item_type), image
        self.prepare_item_regex()

    def prepare_item_regex(self):
        self.items_regex = {}
        # self.entity_info['item'][0] -> all possible item type
        for l in self.entity_info['item'][0]:
            str_list = []
            for item_name in self.entity_info[l][1]:  # all alias of that type
                str_list.append('(' + item_name + ')')
            self.items_regex[l] = '|'.join(str_list)  # combine them into a regex, so we can match any alias

        self.brands_regex = {}
        for l in self.entity_info['brand'][0]: # -> all possible brand
            str_list = []
            for brand_name in self.entity_info[l][1]:  # all alias of that brand
                str_list.append('(' + brand_name + ')')
            self.brands_regex[l] = '|'.join(str_list)  # combine them into a regex, so we can match any alias

        self.effects_regex = {}
        for l in self.entity_info['effect'][0]:
            str_list = []
            for effect_name in self.entity_info[l][1]:
                str_list.append('(' + effect_name + ')')
            self.effects_regex[l] = '|'.join(str_list)

    def prepare_regex(self):
        # loop thru every items
        find_paren_exp = r'\(([\w\|]*)\)'

        for intent, p_list in self.intent_pattern.items():
            self.regex[intent] = []
            for p in p_list:  
                # for every pattern in p_list, we replace the placeholders with real value
                # and compile it into a compiled regex
                pattern = p
                m = re.findall(find_paren_exp, p)  # all (...|...|...) in the regex
                if m:
                    for subreg in m:  # for every (...|...|...)
                        # if subreg[:5] == 'brand' or subreg[:4] == 'name':
                        #     continue

                        # subereg_expand represents the new subreg after we replace the placeholders
                        subreg_expand = subreg
                        # handle 2 same placeholder in one regex
                        if subreg_expand[-2:] == '_1' or subreg_expand[-2:] == '_2':
                            subreg_expand = subreg_expand[:-2]
                        
                        # get all entity in subreg
                        ent_list = subreg_expand.split('|') # every ... between | is an entity
                        for ent in ent_list:
                            if ent[:4] == 'name':         # do not handle names (too many of them, time consuming)
                                continue
                            elif ent[:5] == 'brand':      # replace 'brand' with all possible brands
                                replace_str = self.check_item_brand(ent)
                            else:
                                replace_str = self.check_item(ent)  # replace 'item' with all possible item types
                            subreg_expand = subreg_expand.replace(ent, replace_str)  # replace entities

                        # replace every subreg with expanded subreg
                        pattern = pattern.replace(subreg, subreg_expand)  

                try:
                    compiled = re.compile(pattern)
                except:  # if sth goes wrong -> gg
                    print(pattern)
                    exit(0)

                # append all regex into a list, later compare it to input command 1 by 1
                self.regex[intent].append(compiled)

    def check_item(self, item):
        '''
            反覆去check此sense是否有下位的sense(可以用更細的概念取代)
            以及他是否有同義詞，把所有這些都拿進來變成一個regex
            確保所有符合此概念的詞都可以被match
        '''
        try:     # the first list are possible senses, terms are similar meaning words
            senses, terms = self.entity_info[item]
        except:  # if not a key in entity_info -> means it is a item (reach the bottom)
            return item
        sense_str_list = []
        
        terms = ['('+l+')' for l in terms]
        term_str = '|'.join(terms)  # combine all terms into a regex
        if senses:
            for s in senses:        # if the first list not empty -> need to check those senses
                sense_str = self.check_item(s)
                sense_str_list.append(sense_str)
            if terms:
                sense_str_list.append(term_str)
            return '|'.join(sense_str_list)  # return sense str and term str combined
        else:                       # if first list empty -> only return term str 
            return term_str

    def check_item_brand(self, item):
        '''
            same as check item
            but add escape char to all special chars
        '''
        try:
            senses, terms = self.entity_info[item]
        except:
            return item
        sense_str_list = []
        
        terms = ['('+l.replace('+', '\+').replace('.', '\.').replace('*', '\*').replace('(', '\(').replace(')', '\)').replace('=', '\=')+')' for l in terms]
        term_str = '|'.join(terms)
        if senses:
            for s in senses:
                sense_str = self.check_item_brand(s)
                sense_str_list.append(sense_str)
            if terms:
                sense_str_list.append(term_str)
            return '|'.join(sense_str_list)
        else:
            return term_str

    def check_intent(self, cmd):
        match_str = ""      # the string matching the specified regex
        match_intent = None # the matched intention
        match_idx = 0       # the index of matched pattern in an intention 
                            # (need it because we need to know whether user specify effect, brand or item)

        get_item = False    # whether display recommended item for users
        items = []          # retrieved item list, 
        for intent, reg_list in self.regex.items():  # enumerate thru all intent
            for i, reg in enumerate(reg_list):       # enumerate thru all pattern in a intent
                search_str = re.search(reg, cmd)
                if search_str:  # if the command match reg
                    # here we want to find the longest matched string, so we actually compare to all possible patterns
                    # and then stay with the regex with longest match
                    if len(search_str.group(0)) > len(match_str):
                        match_str = search_str.group(0)
                        match_intent = intent
                        match_idx = i
        if match_str == "":  # after search all possible patterns in all intent -> still no match
            return "nomatch", "NO PATTERNS FOUND...", False, [], ""
        else:                # match to sth
            print('match_str', match_str)
            if match_intent == 'search_item':
                get_item = True

                # retrieve items from styleme_new.tsv
                items = self.get_items(cmd, match_idx not in [5, 6, 17], match_idx in [7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19])
                print('items', items)
                items_proc = self.process_item(items)  # some postprocessing
                print('processed', items_proc)
                items = items_proc                     # return processed items

            return match_intent, self.intent_pattern[match_intent][match_idx], get_item, items, self.resp_info[match_intent][match_idx][0]

    def control(self, cmd):
        cmd_string, pattern_string, get_item, items, resp_string = self.check_intent(cmd)
        return cmd_string, pattern_string, get_item, items, resp_string

    def get_items(self, cmd, specify_item, brand_or_effect):
        items = self.item_info  # styleme_new.tsv
        if specify_item:        # 某種美妝用品，如化妝水等
            item_list = []
            if brand_or_effect: # 除了種類之外，還要求某種功效或品牌
                for effect, regex in self.effects_regex.items():
                    search_str = re.search(regex, cmd)
                    
                    if search_str:  # means belong to an effect, e.g. 保濕
                        ids = self.effect2ids[effect]  # get all item indices with the effect
                        items = items.iloc[ids]        # get all item belonging to the effect
                        print('effect', effect)
                        break

                for brand, regex in self.brands_regex.items():
                    search_str = re.search(regex, cmd)
                    
                    if search_str:  # means belong to a brand, e.g. sk2
                        items = items[items['brand'] == brand]  # get all item belonging to the brand
                        print('brand', brand)
                        break

                

            # check for if item
            for item_type, regex in self.items_regex.items():
                search_str = re.search(regex, cmd)
                
                if search_str:  # means belong to an item, e.g. 化妝水
                    items = items[items['item'] == item_type]  # get all item belonging to the item type
                    print('item', item_type)
                    break


            return self.random_return(df=items, size=20)

        else:
            return self.random_return()  # if does not specify anything, just random return (self.num_rand_product=5) products

    def random_return(self, df=None, size=None):
        # all random
        if not isinstance(df, pd.DataFrame):
            rand_nums = np.random.randint(self.item_info.shape[0], size=self.num_rand_product)
            items = self.item_info.iloc[rand_nums, self.neccess_info]  # self.neccess_info -> only get neccessary info
            print(items)
            item_list = list(items.to_records(index=False))
            return item_list

        if not size:  # if not specify how many items to display -> 5
            size = self.num_rand_product

        # if specify df
        if df.shape[0] <= size:  # if df not bigger the predefined size
            return list(df.iloc[:, self.neccess_info].to_records(index=False))
        else:
            rand_nums = np.random.randint(df.shape[0], size=size)
            items = df.iloc[rand_nums, self.neccess_info]
            item_list = list(items.to_records(index=False))
            return item_list
            
    def process_item(self, items):
        if not items:
            return []
        else:
            new_items = []
            for item in items:
                if isinstance(item[1], str) and isinstance(item[3], str):  # only get item with 'chinese name' and 'image'
                    if isinstance(item[0], str): # if have brand name
                        new_items.append((item[0].replace('_', ' '), item[1], item[3]))
                    else:  # if no brand name -> handle NAN problem in pandas
                        new_items.append(('', item[1], item[3]))

            return new_items        
        


ctrl = Controller('app/pattern/intent_pattern.json', 'app/pattern/entity_info.json', 'app/pattern/styleme_new.tsv', 'app/pattern/effect2ids.json', 'app/pattern/response.json')





if __name__ == '__main__':
    ctrl = Controller('app/pattern/intent_pattern.json', 'app/pattern/entity_info.json')
    # ctrl = Controller('app/pattern/intent_pattern.json', 'ent.json')
    for k, v in ctrl.intent_pattern.items():
        print(k)
    # find_paren_exp = r'\(([\w\|]*)\)'

    # for k, p_list in ctrl.intent_pattern.items():
    #     for p in p_list:
    #         if p != "((brand_1)的)?(name)的(price|feeling|color|smell|volume|CP|url|brand_2|pic|listed_time|comment|effect|info|tips|article|texture)(是什麼|如何)":
    #             continue
    #         pattern = p
    #         m = re.findall(find_paren_exp, p)
    #         if m:
    #             # print('---------------------')
    #             # print('pattern', p)
    #             # print(m)
    #             for subreg in m:
    #                 subreg_expand = subreg
    #                 if subreg_expand[-2:] == '_1' or subreg_expand[-2:] == '_2':
    #                     subreg_expand = subreg_expand[:-2]
    #                 print('subreg', subreg_expand)
    #                 ent_list = subreg_expand.split('|')
    #                 for ent in ent_list:
    #                     a = ctrl.check_item(ent)
    #                     subreg_expand = subreg_expand.replace(ent, a)
    #                 pattern = pattern.replace(subreg, subreg_expand)

    #         # print('====')
    #         print('new pattern', pattern)
        
# 