#-*- coding:utf-8 -*-
import re
from namuwiki.extractor import extract_text

SYNONYM_FLAG = "ᴥ"
SYNONYM_SET = {'문서참조','문서참고','문서 참조','문서 참조.','문서 참고','문서로.','문서를 참고','문서를 참조','항목 참조'}


def generate_dict(namu_wiki):
    word2id = dict()
    for idx, _ in enumerate(namu_wiki):
        word2id[namu_wiki[idx]['title']] = idx

    return word2id


def search_keyword(word2id, keyword, namu_wiki) -> str:
    """
    Search keyword in Namuwiki dump using dictionary 'word2id'.
    Args:
        keyword (str): Keyword to search.
    Returns:
        origin_text (str): Original text saved in dump.
                        If searched keyword does not exist, raise KeyError.
                        If redirected to different keyword, search with respective keyword.
    """
    try:
        doc_id = word2id[keyword]
    except KeyError as ke:
        print("존재하지 않는 키워드입니다.")

    document = namu_wiki[doc_id]
    origin_text = document['text']

    if "redirect" in origin_text:
        splited_result = origin_text.split(" ")
        redirect_keyword = splited_result[-1][:-1]
        doc_id = word2id[redirect_keyword]
        document = namu_wiki[doc_id]
        origin_text = document['text']

    return origin_text


def find_synonym(origin_text) -> list and str:
    """
    Find and replace synonym with SYNONYM_FLAG.
    Args:
        origin_text (str): Original text saved in dump.
    Returns:
        replaced_text (str): Text where synonym replaced with SYNONYM_FLAG.
        splited_replaced_list (list): replaced_text splited with double line feed(\n\n) into list.
    """
    for synonym in SYNONYM_SET:
        if synonym in origin_text:
            origin_text = origin_text.replace(synonym, SYNONYM_FLAG)
    #         else:
    #             replaced_text = origin_text

    splited_replaced_list = origin_text.split("\n\n")

    return origin_text, splited_replaced_list


def parse_text(keyword, text, splited_list) -> list and list and list and bool:
    """
    Find and replace synonym with SYNONYM_FLAG.
    Args:
        keyword (str): Keyword to search.
        text (str): Text where synonym replaced with SYNONYM_FLAG.
        splited_list (list): text splited with double line feed(\n\n) into list.
    Returns:
        search_list (list): List of Search results.
        title_list (list): List of synonyms of specific item titles. This list will be used in list_view.html.
        redirect_list (list): List of words being used to redirect search. (=List of synonyms)
        sub_title_flag (bool): 참조 문서가 있으나 title_list의 항목이 참조문서 제목인 경우 (=== 가 제목일 경우) true.
    """

    start_flag = True
    sub_title_flag = False

    tmp_list = list()
    search_list = list()
    title_list = list()
    redirect_list = list()

    if SYNONYM_FLAG in text:  # 동음이의어가 있는 다중문서인 경우
        for token in splited_list:
            if "== " in token and "=== " not in token:  # == 로 시작하는 항목들만 추출

                if start_flag:  # 새로운 항목의 시작
                    tmp_list.append(token)
                    start_flag = False

                else:  # 항목의 끝 & 새로운 항목 시작
                    item = ''.join(tmp_list)
                    search_list.append(item)
                    tmp_list = list()
                    tmp_list.append(token)

            elif "==\n===" in token:  # ==가 제목이 아니고 그 아래 === 가 제목일 경우
                search_list.append(token)

            elif not start_flag:  # ==이 없는 평범한 토큰
                tmp_list.append(token)

        item = ''.join(tmp_list)  # 마지막 항목
        search_list.append(item)

        if search_list[-1] == '':  # ==가 제목이 아니고 그 아래 === 가 제목일 경우
            search_list = search_list[:-1]  # 마지막에 더해진 빈 항목 제거
            sub_title_flag = True

        for item in search_list:
            if not sub_title_flag:  # == 로 시작하는 항목들
                title = item.split("==")[1].strip(" ").replace("[[", "").replace("]]", "")  # 양옆 공백 제거, 대괄호 제거
                title = re.sub(r'\[[^)]*\]', '', title)  # 대괄호 사이 문자열 제거
                title_list.append(title)

            else:  # ==가 제목이 아니고 그 아래 === 가 제목일 경우
                title = item.split("[[")[1]  # 대괄호 안 내용 추출
                title = title.split("|")[0] if "|" in title else title.split("]]")[
                    0]  # | 가 있으면 |까지의 문자열, 없을 경우 [[]] 사이 문자열
                title_list.append(title)

        synonym_split_tokens = text.split(SYNONYM_FLAG)

        if not sub_title_flag:  # == 로 시작하는 항목들
            for token in synonym_split_tokens:
                token_list = token.split("\n")
                synonym = token_list[-1]

                if "|" in synonym:
                    synonym = synonym.split("|")[0]

                if "분류" in synonym:
                    continue

                elif synonym:
                    redirect_list.append(synonym.strip(" ").replace("[[", "").replace("]]", ""))
        else:
            redirect_list = title_list

    else:  # 단일 의미인 경우
        search_list = splited_list

    if title_list and title_list[0] == "개요":  # 단일 문서인 경우
        title_list = [keyword]  # title_list는 길이가 1이 되고, 검색 키워드를 title_list에 넣어준다
        redirect_list = list()  # 참조문서도 제거
        search_list_str = ' '.join(search_list)
        search_list = [search_list_str]

    elif not title_list:
        title_list = [keyword]

    return search_list, title_list, redirect_list, sub_title_flag


def filter_text(word2id, search_list, redirect_list, sub_title_flag, namu_wiki) -> list:
    """
    Filters keyword search result in search_list.
    If there is redirect document, search again with respective redirect keyword and returns result.
    Args:
        search_list (list): List of Search results.
        redirect_list (list): List of words being used to redirect search. (=List of synonyms)
        sub_title_flag (bool): 참조 문서가 있으나 title_list의 항목이 참조문서 제목인 경우 (=== 가 제목일 경우) true.
    Returns:
        clean_list (list): List of filtered and redirected text. Filtering is done with extract_text function imported from namuwiki.extractor.
    """

    single_clean_list = list()
    clean_list = list()
    redirect_cnt = 0
    single_cnt = 0

    for idx, search_result in enumerate(search_list):

        if sub_title_flag:  # 참조 문서가 있으나 title_list의 항목이 참조문서 제목인 경우 (=== 가 제목일 경우)
            keyword = redirect_list[redirect_cnt]
            text = search_keyword(word2id, keyword, namu_wiki)

            clean_list.append(str(extract_text(text)))
            redirect_cnt += 1

        elif SYNONYM_FLAG in search_result and redirect_list:  # 참조 문서가 있는 동음이의어 (말)
            keyword = redirect_list[redirect_cnt]
            text = search_keyword(word2id, keyword, namu_wiki)

            clean_list.append(str(extract_text(text)))
            redirect_cnt += 1

        else:  # 참조 문서가 없는 경우
            single_cnt += 1
            clean_list.append(str(extract_text(search_result)))

    if single_cnt == len(search_list):  # 참조문서 없는 싱글 텍스트
        single_clean_str = ' '.join(clean_list)
        clean_list = [single_clean_str]

    return clean_list


def get_result(clean_list) -> list:
    """
    Filters clean_list removing unnecessary characters.
    Args:
        clean_list (list): List of filtered and redirected text.
    Returns:
        result_list (list): List of filtered text. This is the final list of results that are passed to main process.
    """
    result_list = list()
    for text in clean_list:
        text = text.replace("\n", " ")  # 개행문자 띄어쓰기로 변환
        text = (re.sub('[^ ㄱ-ㅣ가-힣A-Za-z.,?!0-9]', '', text))  # 한글, 영어, 일부 특수문자, 숫자 제외 제거
        if "개요" in text:
            result_list.append(text.split("개요")[1])
        else:
            result_list.append(text)

    return result_list

