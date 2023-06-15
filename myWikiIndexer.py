import sys
import timeit
import re
from xml.sax import parse
from xml.sax import ContentHandler
from collections import defaultdict
from nltk.stem import PorterStemmer
i = 0

ps = PorterStemmer()
stemmingMap = dict()
fileLim = 25000
# use crawled data from the Internet
dumpFile = 'dump/enwiki-latest-abstract.xml'
#dumpFile = 'dump/enwiki-20230520-pages-articles-multistream.xml'
path_to_index = 'index'

documentTitleMapping = open("./docToTitle.txt", "w")
totaldl = 0

'''
Dictionary structure
{
    word : {
        docID :{
            t1 : cnt1,
            t2 : cnt2
        }
        docID : {
            t1 : cnt3,
            t2 : cnt4
        }
        .
        .
        .
    }
    .
    .
    .
}
'''
invertedIndex = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

stopwordsList = set()
with open("stopwords.txt", 'r') as f:
    for line in f:
        line = line.strip()
        stopwordsList.add(line)

# Regular Expression to remove Brackets and other meta characters from title
regExp = re.compile(r"[~`!@#$%\-^*+{\[}\]\|\\<>/?,]", re.DOTALL)



def cleanText(text):
    # Regular Expression to remove {{cite **}} or {{vcite **}}
    reg = re.compile(r'{{v?cite(.*?)}}', re.DOTALL)
    text = reg.sub('', text)
    # Regular Expression to remove Punctuation
    reg = re.compile(r'[.,;_()/\"\'\=]', re.DOTALL)
    text = reg.sub(' ', text)
    # Regular Expression to remove [[file:]]
    reg = re.compile(r'\[\[file:(.*?)\]\]', re.DOTALL)
    text = reg.sub('', text)
    # Regular Expression to remove <..> tags from text
    reg = re.compile(r'<(.*?)>', re.DOTALL)
    text = reg.sub('', text)
    # Remove Non ASCII characters
    reg = re.compile(r'[^\x00-\x7F]+', re.DOTALL)
    text = reg.sub(' ', text)
    return text


def addToIndex(wordList, docID, t):
    for word in wordList:
        word = word.strip()
        word = re.sub(r'[\ \.\-\:\&\$\!\*\+\%\,\@]+',"",word)
        if len(word) >= 3 and len(word) <= 500 and word not in stopwordsList:
            if word not in stemmingMap.keys():
                stemmingMap[word] = ps.stem(word)
            word = stemmingMap[word]
            if word not in stopwordsList:
                if word in invertedIndex:
                    if docID in invertedIndex[word]:
                        if t in invertedIndex[word][docID]:
                            invertedIndex[word][docID][t] += 1
                        else:
                            invertedIndex[word][docID][t] = 1
                    else:
                        invertedIndex[word][docID] = {t: 1}
                else:
                    invertedIndex[word] = dict({docID: {t: 1}})


def processBuffer(text, docID, isTitle):
    global path_to_index, totaldl
    text = text.lower()
    text = cleanText(text)
    regExp.sub(' ', text)
    words = text.split()
    totaldl += len(words)
    tokens = list()
    for word in words:
        if word not in stopwordsList:
            tokens.append(word.strip())
    if isTitle == True:
        addToIndex(tokens, docID, "t")
    else:
        addToIndex(tokens,docID,'b')
        if docID%fileLim == 0:
                f = open(path_to_index + "/" + str(docID) + ".txt", "w")
                for key, val in sorted(invertedIndex.items()):
                    s = str(key)+"="
                    for k, v in sorted(val.items()):
                        s += str(k) + ":"
                        for k1, v1 in v.items():
                            s = s + str(k1) + str(v1) + "#"
                        s = s[:-1]+","
                    f.write(s[:-1]+"\n")
                f.close()
                invertedIndex.clear()
                stemmingMap.clear()
    return len(words)

class WikiContentHandler(ContentHandler):
    def __init__(self):
        self.docID = 0
        self.isTitle = False
        self.title = ""
        self.buffer = ""
        self.url =""
        self.length=0

    def characters(self, content):
        self.buffer = self.buffer + content

    def startElement(self, element, attributes):
        if element == "title":
            self.buffer = ""
            self.isTitle = True
        if element == "doc":
            self.docID += 1
        if element == "abstract":
            self.buffer = ""

    def endElement(self, element):
        if element == "title":
            self.length += processBuffer(self.buffer, self.docID, self.isTitle)
            self.isTitle = False
            self.title = self.buffer
            self.buffer = ""
        elif element == "url":
            self.url = self.buffer[1:]
            self.buffer = ""
        elif element == "abstract":
            self.length += processBuffer(self.buffer, self.docID, self.isTitle)
            try:
                documentTitleMapping.write(str(self.docID)+"#"+str(self.length)+'#'+self.title+'   url:'+self.url+"\n")

            except:
                documentTitleMapping.write(
                    str(self.docID)+"#"+str(self.length)+'#'+self.title.encode('utf-8')+'   url:'+self.url+"\n")
            self.buffer = ""
            self.length = 0


def main():
    parse(dumpFile, WikiContentHandler())
    f = open("total_length.txt", "w")
    f.write(str(totaldl))
    f.close()


    f = open(path_to_index + "/final.txt", "w")
    for key, val in sorted(invertedIndex.items()):
        s = str(key)+"="
        for k, v in sorted(val.items()):
            s += str(k) + ":"
            for k1, v1 in v.items():
                s = s + str(k1) + str(v1) + "#"
            s = s[:-1]+","
        f.write(s[:-1]+"\n")
    f.close()
    invertedIndex.clear()
    stemmingMap.clear()


if __name__ == "__main__":
    start = timeit.default_timer()
    main()
    stop = timeit.default_timer()
    print(stop - start)
