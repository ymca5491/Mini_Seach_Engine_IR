import sys
import re
import timeit
from collections import defaultdict
from operator import itemgetter
from nltk.stem import PorterStemmer
from bisect import bisect
from math import log10

ps = PorterStemmer()
noDocs = 0
avgdl = 0

k_bm = 2
b_bm = 0.75 # param for BM25

docToTitle = dict()
docLength = dict()
stopWords = set()
secondaryIndex = list()
invertedIndex = defaultdict(lambda : defaultdict(lambda : \
                            defaultdict(int)))
fieldDict = {
    'title': 't',
    'body': 'b'}
weight = {
    't': 5,
    'b': 3
}
fields = ['title:', 'body:']


def readDocTitleMap():
    global docToTitle, noDocs, avgdl
    with open('./total_length.txt', 'r') as f:
        tmp = f.read().strip()
        avgdl = float(tmp)

    with open('./docToTitle.txt', 'r') as f:
        for line in f:
            (docID, length, titleMap) = line.split('#')
            docToTitle[docID] = titleMap
            docLength[docID] = int(length)
            noDocs += 1
    avgdl /= noDocs


def readStopwords():
    global stopWords
    try:
        f = open('stopwords.txt', 'r')
        for line in f:
            stopWords.add(line.strip())
    except:
        print("Can't find stopwords.txt")
        sys.exit(1)

def readSecondaryIndex():
    global secondaryIndex
    try:
        f = open('finalIndex/secondaryIndex.txt', 'r')
        for line in f:
            secondaryIndex.append(line.split()[0])
    except:
        print("Can't find the secondary index file in 'finalIndex' Folder.")
        sys.exit(1)


def cleanText(text):

    # Regular Expression to remove {{cite **}} or {{vcite **}}

    reg = re.compile(r'{{v?cite(.*?)}}', re.DOTALL)
    text = reg.sub('', text)

    # Regular Expression to remove Punctuation

    reg = re.compile(r'[.,;_()"/\']', re.DOTALL)
    text = reg.sub(' ', text)

    # Regular Expression to remove [[file:]]

    reg = re.compile(r'\[\[file:(.*?)\]\]', re.DOTALL)
    text = reg.sub('', text)

    # Regular Expression to remove <..> tags from text

    reg = re.compile(r'<(.*?)>', re.DOTALL)
    text = reg.sub('', text)

    # Regular Expression to remove non ASCII char

    reg = re.compile(r'[^\x00-\x7F]+', re.DOTALL)
    text = reg.sub(' ', text)
    return text


def getFileNumber(word):
    position = bisect(secondaryIndex, word)
    return position


def getPostingList(word):
    position = getFileNumber(word)
    primaryFile = 'finalIndex/index' + str(position) + '.txt'
    file = open(primaryFile, 'r')
    data = file.readlines()
    low = 0
    high = len(data)
    mid = int()
    while low <= high:
        mid = int(low + (high - low) / 2)
        cur = data[mid].split('=')[0]
        if cur == word:
            break
        elif cur < word:
            low = mid + 1
        else:
            high = mid - 1
    return data[mid].split('=')[1].split(',')


def printResult(lengthFreq):
    lengthFreq = sorted(lengthFreq.items(), key=lambda item: item[1], reverse=True)[0:10]
    for tup in lengthFreq:
        (docId, _) = tup
        print("=> ", docToTitle[docId], end='')


def parseQuery(queryText, isFieldQuery):
    wordRegEx = re.compile(r'[\ \.\-\:\&\$\!\*\+\%\,\@]+', re.DOTALL)
    if isFieldQuery:
        fieldQList = list()
        queryList = queryText.split()
        for word in queryList:
            if ':' not in word:
                word = 'body:' + word
            (cat, content) = word.split(':')
            content = cleanText(content)
            content = ps.stem(content)
            content = wordRegEx.sub('', content)
            if len(content) > 0 and content.isalnum and content \
                not in stopWords:
                fieldQList.append((content, fieldDict[cat]))
        finalDict = defaultdict(int)
        for (word, category) in fieldQList:
            postingListAll = getPostingList(word)
            postingList = [i for i in postingListAll if category in i]
            if len(postingList) < 2:
                postingList = postingListAll
            numDoc = len(postingList)
            idf = log10(noDocs / numDoc)
            for pl in postingList:
                docId, freqList = pl.split(":")
                categoryFreq = freqList.split("#")
                tf = 0
                for cf in categoryFreq:
                    cat = cf[0]
                    freq = int(cf[1:])
                    tf += (freq * weight[cat])
                finalDict[docId] += float(idf) * (float(tf) * (k_bm + 1)) \
                    / (float(tf) + k_bm*(1-b_bm+b_bm*float(docLength[docId]/avgdl)))
    else:

        queryText = cleanText(queryText)
        tokenList = queryText.split(' ')
        tokenList = [wordRegEx.sub('', i) for i in tokenList]
        finalTokens = list()
        for tok in tokenList:
            val = ps.stem(tok)
            if len(val) > 0 and val.isalnum and val not in stopWords:
                finalTokens.append(val)
        finalDict = defaultdict(int)
        for word in finalTokens:
            postingList = getPostingList(word)
            numDoc = len(postingList)
            idf = log10(noDocs / numDoc)
            for pl in postingList:
                docId, freqList = pl.split(":")
                categoryFreq = freqList.split("#")
                tf = 0
                for cf in categoryFreq:
                    cat = cf[0]
                    freq = int(cf[1:])
                    tf += (freq * weight[cat])
                finalDict[docId] += float(idf) * (float(tf) * (k_bm + 1)) \
                    / (float(tf) + k_bm*(1-b_bm+b_bm*float(docLength[docId]/avgdl)))
    printResult(finalDict)


def search(path_to_index, query):
    global fields
    isFieldQuery = False
    for f in fields:
        if f in query:
            isFieldQuery = True
            break
    parseQuery(query, isFieldQuery)


def main():
    path_to_index = './finalIndex/'
    while True:
        query = input('\nEnter Query: ')
        print('+++++++++++++++++++++++++++++++++++')
        start = timeit.default_timer()
        search(path_to_index, query)
        end = timeit.default_timer()
        print('\nTook', end - start, 'sec\n')
        print('+++++++++++++++++++++++++++++++++++')


if __name__ == '__main__':
    print ('reading DoctitleMap')
    readDocTitleMap()
    print ('reading secondary Index')
    readSecondaryIndex()
    readStopwords()
    try:
        main()
    except:
        print ('''\n\nThank You..\n''')
