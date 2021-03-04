import re
import sys
from my_pickle import load_pickle
from namu_func import generate_dict, search_keyword, find_synonym, parse_text, filter_text, get_result

keyword = sys.argv[1]

namu_wiki = load_pickle()
word2id = generate_dict(namu_wiki)

try:
    origin_text = search_keyword(word2id, keyword, namu_wiki)
    replaced_text, splited_replaced_list = find_synonym(origin_text)
    search_list, title_list, redirect_list, sub_title_flag = parse_text(keyword, replaced_text, splited_replaced_list)
    clean_list = filter_text(word2id, search_list, redirect_list, sub_title_flag, namu_wiki)
    result_list = get_result(clean_list)
    
    if len(result_list)==1:
        text = result_list[0]
        kor_text = " ".join(re.compile('[가-힣]+').findall(text)) # 순수 한글 텍스트
        
        if len(kor_text) < len(text)/2: # 한글보다 영어나 특수기호가 많을 경우 (방탄소년단)
            title_list = [0]
            result_list = [0]
            
except:
    title_list = [0]
    result_list = [0]

print(title_list)
print(result_list[0])
