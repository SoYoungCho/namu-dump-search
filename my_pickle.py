import pickle

def load_pickle():
    with open('namuwiki.pickle', 'rb') as f:
        namu_wiki = pickle.load(f) # 따로 파이썬 파일 빼기
    return namu_wiki
