# # # # # # # # # # # # # # # # # # # # # #
# @author Alexander Novikov
#
# A simple search engine implementation
#

from main.models import Experiment, WordIndexEntry, DocIndexEntry

import math
import re

EXCLUDE_WORDS = sorted(["a", "the", "in", "this", "at", "an", "he", "she", "it"]);
KILL_PUNCT_PATTERN = r'[@\[\]\{\}\(\)\!\@\#\$%\^&\*\+-<>\.\,\;\"\']+'
SHIFT=16

def serializeFeatureVector(vec, wordObject):
    vals = []
    for key in vec:
        vals.append(str(key)+","+str(vec[key]))
    val = ";".join(vals)
    wordObject.svec = val

def deserializeFeatureVector(wordObject):
    result = {}
    rows=wordObject.svec.split(";")
    for entry in rows:
        if len(entry) > 0:
            key, value = entry.split(",")
        result[int(key)] = float(value)
    return result

def sparseVecDotProduct(vec1, vec2):
    #1. Perform multiplication, normalize later
    len1sq = 0.0
    len2sq = 0.0
    result = 0.0
    done   = set()
    for si in vec1:
        len1sq += vec1[si]*vec1[si]
        if si in vec2:
            done.add(si)
            result += vec1[si]*vec2[si]
    for sj in vec2:
        len2sq += vec2[sj]*vec2[sj]
    
    if (len1sq == 0 or len2sq == 0):
        return 0
    
    result = result / math.sqrt(len1sq * len2sq)
    return result

def sparseVecWeightedSum(vec1, w1, vec2, w2):
    result = {}
    for si in vec1:
        result[si] = w1 * vec1[si]
    for sj in vec2:
        if not sj in result:
            result[sj] = w2*vec2[sj]
        else:
            result[sj] += w2*vec2[sj] 
    return result


# Encode a trigram inside a 64-bit integer
def sparse_encode(pstr):
    pstr = map(lambda c: c, pstr)
    pstr.sort()
    val = 0
    for i in range(0, len(pstr)):
        val = val << SHIFT
        val = val ^ ord(pstr[i])
    return val
        
def build_trigrams(pword, entries):
    if len(pword) > 2:
        str = pword[0:3]
        val = sparse_encode(str)
        if not val in entries:
            entries[val] = 1
        pass
    
    for i in range(2, len(pword)-1):
        str = pword[i-1:i+2]
        val = sparse_encode(str)
        if not val in entries:
            entries[val] = 0
        entries[val] += 1
    

def get_words(impreciseStr):
    impreciseStr = re.sub(KILL_PUNCT_PATTERN, '', impreciseStr).lower()
    words = []
    for word in impreciseStr.split():
        if len(word) < 3:
            continue
        if not word in EXCLUDE_WORDS:
            words.append(word)
    return words

def get_word_features(wordstrs):
    wordfeatures = []
    for word in wordstrs:
        vfeat = {}
        build_trigrams(word, vfeat)
        wordfeatures.append(vfeat)
    return wordfeatures
    
def ranked_words(hashesColl):
    rankedWords = []
    ranks       = []
    
    for i in range(0, len(hashesColl)):
        rankedWords.append(-1)
        ranks.append(0)
    
    for wordInSystm in WordIndexEntry.objects.all():
        wordSystmFeatVec = deserializeFeatureVector(wordInSystm)
        for i in range(0, len(hashesColl)):
            candidateRank = sparseVecDotProduct(hashesColl[i], wordSystmFeatVec)
            if (candidateRank > ranks[i]):
                rankedWords[i] = wordInSystm.id
                ranks[i] = candidateRank
    return [rankedWords, ranks]
    
def get_query_features(wordObjects, ranks):
    svec = {}
    for wi in range(0, len(wordObjects)):
        svec[wordObjects[wi]] = ranks[wi]
    return svec

STATIC_ORDER_RANK_PENALTY = 1    

def ranked_docs(svec):
    docsRank = {}
    penalty = 0
    for docInSystem in DocIndexEntry.objects.all():
        docSystmFeatVec = deserializeFeatureVector(docInSystem)
        rank = sparseVecDotProduct(svec, docSystmFeatVec)
        docsRank[int(rank*(1 << 12) - penalty)] = docInSystem.doc
        penalty += STATIC_ORDER_RANK_PENALTY
    # TODO: In future, obsiously these have to be bounded, but ignore that
    # issue for now, we don't have that many documents
    return docsRank
        
def rank_experiments(impreciseStr):
    impreciseWords = get_words(impreciseStr)
    
    hashesCollection = get_word_features(impreciseWords)
    
    wordObjs = ranked_words(hashesCollection)
    
    wordVector = get_query_features(wordObjs[0], wordObjs[1])
    
    result_map = ranked_docs(wordVector)
    
    #TODO: adjust by votes!
    
    #for indexEntry in FeatureIndexRow.all():
    #    rank = sparseVecDotProduct(thisVec, indexEntry.features)
    #    result_map[1000 - int(rank*1000)] = indexEntry.experiment
    #
    
    return result_map

def search1(impreciseStr):
    result_map = rank_experiments(impreciseStr)
    map_keys = result_map.keys()
    map_keys.sort()
    map_keys.reverse()
    results = map(lambda index: result_map[index], map_keys)
    return results[:50]
    
def commitWords(words, features):
    pks = []
    for i in range(0, len(words)):
        has_word = False
        for wOldEntry in WordIndexEntry.objects.all():
            if wOldEntry.word == words[i]:            
                has_word = True
                pks.append(wOldEntry.id)
                break
        if not has_word:
            wentry = WordIndexEntry ()
            wentry.word = words[i]
            serializeFeatureVector(features[i], wentry)
            wentry.save()
            pks.append(wentry.id)
    return pks
    
def commitDoc(features, doc):
    doe = DocIndexEntry()
    doe.doc = doc
    serializeFeatureVector(features, doe)
    doe.save()

def addToIndex(exp):
    x_desc_str = "%s %s" % (exp.x_name, exp.x_units)
    y_desc_str = "%s %s" % (exp.y_name, exp.y_units)
    
    x_words = get_words(x_desc_str)
    y_words = get_words(y_desc_str)
    d_words = get_words(exp.description)
    
    x_featColl = get_word_features(x_words)
    y_featColl = get_word_features(y_words)
    d_featColl = get_word_features(d_words)
    
    x_wids = commitWords(x_words, x_featColl)
    y_wids = commitWords(y_words, y_featColl)
    d_wids = commitWords(d_words, d_featColl)
    
    x_vec = get_query_features(x_wids, map(lambda x: 1, range(0, len(x_wids))))
    y_vec = get_query_features(y_wids, map(lambda x: 1, range(0, len(y_wids))))
    d_vec = get_query_features(d_wids, map(lambda x: 1, range(0, len(d_wids))))
    
    result = sparseVecWeightedSum(y_vec, 1.0, x_vec, 0.8)
    result = sparseVecWeightedSum(result, 1.0, d_vec, 0.3)
    
    commitDoc(result,  exp)
    