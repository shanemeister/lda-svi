#!/usr/bin/python

import nltk
from nltk import word_tokenize
from bs4 import BeautifulSoup
import urllib.request
from collections import defaultdict, Counter
import os
import re
from nltk.stem import RegexpStemmer

def popDict(dataDict, path, filename):
    with open(path + '/' + filename, 'r') as f:
       #print(filename)
       for line in f.readlines():
            line = line.strip()
            if re.search('^Filename:', line):
                filename = re.search('^Filename:\s(.*)\.', line).groups(1)[0]
            elif re.search('^Author:', line):
                author = re.search('^Author:\s(.*)', line).groups(1)[0]
                dataDict[filename].append(author)
            elif re.search('^Citation Date:', line):
                citation_date = re.search('^Citation Date:\s(.*)', line).groups(1)[0]
                dataDict[filename].append(citation_date)
                year = re.search('^Citation Date: (\d+)', line).groups(0)[0]
                dataDict[filename].append(year)
            elif re.search('^Abstract URL:', line):
                abstract_url = re.search('^Abstract URL:\s(.*)', line).groups(1)[0]
                dataDict[filename].append(abstract_url)
            elif re.search('^Title:', line):
                title = re.search('^Title:\s(.*)', line).groups(1)[0]
                dataDict[filename].append(title)
            elif re.search('^Abstract:', line):
                abstract = re.search('^Abstract:\s(.*)', line).groups(1)[0]
            else:
                abstract += line
    dataDict[filename].append(abstract)
    return dataDict

def nested_dict():
    return defaultdict(nested_dict)

def readURL(url):
    print(url)
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read()
    except urllib.error.URLError as e:
        print('Message on readURL error: ', e.reason)
        return None

    return html

def faculty():

    html = readURL("https://www.eecs.mit.edu/people/faculty-advisors")
    soup = BeautifulSoup(html, 'html.parser')
    names = defaultdict(list)
    divs = soup.find_all(class_="field-content card-title")
    for div in divs:
        try:
            dept = div.find('a')['href']
            if dept.lower().find('csail') > 0 : dept = 'CSAIL'
            elif dept.lower().find('lids') > 0 : dept = 'LIDS'
            elif dept.lower().find('mtl') > 0 : dept = 'MTL'
            elif dept.lower().find('rle') > 0 : dept = 'RLE'
            else: dept = 'UNK'
        except:
            dept = 'UNK' # These records had no No HREF
            pass
        try:
            names[div.get_text()] = dept
        except:
            continue
    return names

def getArticles(fac_lst):
    #Search papers in arXiv for each person in
    # arxiv.org/find/all/1/au:+(lastname)_(initial)/0/1/0/all/0/1
    fac_dict = nested_dict()
    count = 0
    for i in range(len(fac_lst)):
        try:
            fname, lname = fac_lst[i].split()
            fac_dict[i] = (lname, fname,)
        except:
            print('Error occurred:', count)
            count += 1
            continue
            # Not going to worry about rare exceptions of one name --
            # which there is at least one
        try:
            mirror = 'https://arxiv.org:443'
            search_str = mirror + '/find/all/1/au:+' + fac_dict[i][0] + '_' + fac_dict[i][1] + \
                         '/0/1/0/all/0/1'
            print('Search string', search_str)
        except:
            msg = "Cannot open %s" % search_str
            print(msg)
            print('Error occurred:', count)
            count += 1
            continue
        try:
            paper = readURL(search_str)
            soup = BeautifulSoup(paper, "html.parser")
            #print(soup.contents)
            spans = soup.find_all("span", class_="list-identifier")
        except:
            continue
        if len(spans) == 0:
            continue
        print(str(i) + " " + fac_dict[i][0] + ", " + fac_dict[i][1] + " has " + \
              str(len(spans)) + " abstract(s)")
        for span in spans:
            abs_url = 'https://arxiv.org/' + span.a["href"]
            html_text = readURL(abs_url)
            soup = BeautifulSoup(html_text, "html.parser");
            abstract = soup.find("blockquote", class_="abstract").text
            citation_date = soup.find("meta", {"name":"citation_date"})['content']
            print(type(citation_date))
            abstract = abstract.replace("Abstract: ", "")
            title = soup.find("h1", class_="title").text
            #pattern = '%Y-%m-%d'
            #epoch = int(time.mktime(time.strptime(citation_date, pattern)))
            #filename = str(str(epoch) + '_' + fac_dict[i][0] + '.txt')
            #filename = str(str(pattern) + '_' + fac_dict[i][0] + '.txt')
            filename = str(citation_date.replace('/', '-') + '_' + fac_dict[i][0] + '.txt')
            print('Filename:', filename)
            author = str(fac_dict[i][0] + ", " + fac_dict[i][1])
            abs_complete = str('Filename: ' + filename + '\n' + \
                'Author: ' + author + \
                '\n' + 'Citation Date: ' + citation_date + '\n' + \
                'Abstract URL: ' + abs_url + '\n' + title + '\n' + \
                'Abstract: ' + abstract)
            try:
                print(abs_complete)
                if not os.path.exists('./Abstracts20170711'):
                    os.makedirs('./Abstracts20170711')
                target_dir = r"./Abstracts20170711"
                fullname = os.path.join(target_dir, filename)
                with open(fullname, "w") as f:
                        f.write(abs_complete)
                f.close()
                print("   stored in %s" % filename)
            except:
                print("   FAILURE: could not store in %s !" % filename)

def preProcess(dataDict):
    temp = list()
    for k in dataDict.keys():
        stopset = set(nltk.corpus.stopwords.words('english'))
        stopset.update(('end', 'and', 'of', 'to', ':', '', 'use', 'show', 'uses', 'also', 'new', 'using', 'give', 'given', 'based' , 'used', 'one', 'two', 'three'))
        words = word_tokenize(dataDict[k][5].strip().lower()) # Abstracts
        words2 = word_tokenize(dataDict[k][4].strip().lower()) # Titles
        stopped_tokens = [i for i in words if not i in stopset and len(i) > 2] # Abstracts
        stopped_tokens2 = [i for i in words2 if not i in stopset and len(i) > 2] # Titles
        stopped_combined = stopped_tokens + stopped_tokens2
        # print (len(stopped_combined), stopped_combined)
        # According to NLTK documentation:
        # "Observe that the Porter stemmer correctly handles the word lying
        # (mapping it to lie), while the Lancaster stemmer does not."
        porter = nltk.PorterStemmer()
        stemmedWords = [porter.stem(t) for t in stopped_tokens]
        stemmedWords2 = [porter.stem(t) for t in stopped_tokens2]
        stemmedWords3 = [porter.stem(t) for t in stopped_combined]

        #print(stemmedWords)
        #dataDict[k].append(Counter(stemmedWords))
        #dataDict[k].append(stopped_tokens) # preProcessed Abstracts
        #dataDict[k].append(stopped_tokens2) # preProcessed Titles
        # print('stemmedWords', stemmedWords)
        # print('stemmedWords2', stemmedWords2)
        dataDict[k].append(stemmedWords)  # preProcessed Abstracts
        dataDict[k].append(stemmedWords2)  # preProcessed Titles
        dataDict[k].append(stemmedWords3)  # preProcessed Titles

        #dataDict[k].append(Counter(stopped_tokens2)) # Unique list of Title Words

    #print(dataDict[k][6])
    #print(dataDict[k][7])
    # print(dataDict[k][8])

    return dataDict


if __name__ == '__main__':
    pass