###############################################################################
#
#   Created by: Bence Magos at: 2024. 03. 05.
#       Generates .pkl cache file, containing article text, and filename
#           handles the text cutting based on the xlsx file containing the words
#           and the cutting points
#
###############################################################################
#
#                                IMPORTS
#
###############################################################################

from os.path import basename
from zipfile import ZipFile
import pandas as pd
import pdfplumber
import datetime
import re
import os
from os import path
from sympy import false
from tika import parser
import fitz # pip install pymupdf
from logger import logger

###############################################################################
#
#                               FUNCTIONS
#
###############################################################################
class CacheCreator:
    finalDataFrameFileName = '_article_cache.pkl'
    
    stopWordExtender = [".", ",", "(", ")", "`", "’","~", ".", "-", "!", "%", "/", "the", "\'", ":", "&", "@", "?", "[", "]", '\"', "´", "˘", "˛", "-", "“", "‘", "–", "#", ";", "'s", "”"]
    
    logger_instance = logger.Logger.getInstance()
    
    is_cutting = False

    def __init__(self, articles_location, file_for_cutting = '', types_csv = 'types.csv', cache_with_types = False):
        self.file_for_cutting = file_for_cutting
        self.articles_location = articles_location
        if (path.exists(types_csv)):
            self.types_csv = pd.read_csv(types_csv)
        self.cache_with_types = cache_with_types

    def start_generating(self):
        needToUseLowerCase = True
        self.is_cutting = path.exists(self.file_for_cutting)
        average = self.calculateAverageCharNumber4Pages()
        self.loadPdf(average)
        self.logger_instance.log('info', 'Eof')

    def isfloat(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False
    
    def getResearchMethod(self, title):
        for index, row in self.types_csv.iterrows():
            title = os.path.splitext(title)[0]
            types_title = os.path.splitext(row['title'])[0]
    
            if title == types_title:
                return row['research_method']
    
    def removeWritingSings(self, word):
        for item in self.stopWordExtender:
            if item in word:
                word = word.replace(item, ' ')
        return word.lower()
    
    
    def getPosition(self, rawText, rawPhrase):
        positions = []
        counter = 0
        index = 0
        wordCounter = 0
        charCounter = 0
    
        text = str(rawText).split()
    
        allWords = len(text)
        allChar = len(rawText)
        phrase = rawPhrase.lower().split()
    
        ## this is stores the length of a word
        ## if matches with the searching pattern
        ## this will be extracted from the matches word position
        matchesWordLength = 0
    
        for word in text:
            charCounter += len(word) + 1
    
            if(self.isfloat(word) == False):
                words = ' '.join(word.split()).lower()
                if index == 0:
                    if (phrase[0] == words):
                        # matching word
                        index += 1
                        matchesWordLength += len(word) + 1
                    if (phrase[0] == words) & (len(phrase) == 1):
                        ## found an phrase
                        counter += 1
                        positions.append(round((charCounter - matchesWordLength + 1)/allChar*100))
                        index = 0
                elif index != 0:
                    if len(phrase) > index:
                        if (phrase[index] == words):
                            # matching word
                            index += 1
                            matchesWordLength += len(word) + 1
                            if index == len(phrase):
                                ## found a phrase
                                counter += 1
                                positions.append(round((charCounter - matchesWordLength + 1)/allChar*100))
                                index = 0
                        else: index = 0
                            
                    elif len(phrase) == index:
                        ## found a phrase
                        counter += 1
                        positions.append(round((charCounter - matchesWordLength + 1)/allChar*100))
                        index = 0
    
            wordCounter += 1
        return positions
    
    # determine the words position in the text  
    def getPositionDictionary(self, rawText, rawPhrase):
        ## return data for find cutting points function
        returnData = {"positions": [], "charStart": []}
    
        positions = []
        counter = 0
        index = 0
        ## counter to calculate the position of the word in the text
        wordCounter = 0
        charCounter = 0
    
        text = str(self.removeWritingSings(rawText)).split()
    
        allWords = len(text)
        allChar = len(rawText)
        phrase = rawPhrase.lower().split()
    
        ## this is stores the length of a word
        ## if matches with the searching pattern
        ## this will be extracted from the matches word position
        matchesWordLength = 0
    
        for word in text:
            charCounter += len(word) + 1
    
            if(self.isfloat(word) == False):
                words = ' '.join(word.split()).lower()
                if index == 0:
                    if (phrase[0] == words):
                        # matching word
                        index += 1
                        matchesWordLength += len(word) + 1
                    if (phrase[0] == words) & (len(phrase) == 1):
                        ## found a phrase
                        counter += 1
                        returnData['positions'].append(round((charCounter - matchesWordLength + 1)/allChar*100))
                        returnData['charStart'].append(charCounter - matchesWordLength + 1)
    
                        index = 0
                elif index != 0:
                    if len(phrase) > index:
                        if (phrase[index] == words):
                            # matching word
                            index += 1
                            matchesWordLength += len(word) + 1
                            if index == len(phrase):
                                ## found a phrase
                                counter += 1
    
                                returnData['positions'].append(round((charCounter - matchesWordLength + 1)/allChar*100))
                                returnData['charStart'].append(charCounter - matchesWordLength + 1)
                                index = 0
                        else: index = 0
                            
                    elif len(phrase) == index:
                        ## found a phrase
                        counter += 1
                        returnData['positions'].append(round((charCounter - matchesWordLength + 1)/allChar*100))
                        returnData['charStart'].append(charCounter - matchesWordLength + 1)
                        index = 0
    
            wordCounter += 1
        return returnData
    
    
    def searchForCuttingPoints(self, text, fileName):
       # cutting point before the text
        before = 0
        # number of all words
        allWords = len(text)
        # cutting point after the text
        after = allWords
    
        counter = 0
        # get the phrases and the position limits
        phrasesExcelFile = pd.ExcelFile(self.file_for_cutting)
        phrases = pd.read_excel(phrasesExcelFile, 'for_cutting')
    
        for phrase in phrases['phrase']:
            phrase = phrase.lower()
    
            self.logger_instance.log('debug', 'Actual phrase: ' + phrase)
    
            ## get positions of the actual phrase
            phrasePositions = self.getPositionDictionary(text, phrase)
    
            self.logger_instance.log('debug', 'Phrase positions PHRASE --> ' +  phrase  + ' positions --> ' + str(phrasePositions))
    
            for position, charStart in zip(phrasePositions['positions'], phrasePositions['charStart']):
                self.logger_instance.log('debug', 'Actual word while searching for cutting points: ' + phrase)
                self.logger_instance.log('debug', 'Looking for best cutting point: actual_percent: ' + str(position) + ' charStart: ' + str(charStart) + ' min: ' + str(phrases['min'][counter]) + ' max: ' + str(phrases['max'][counter]))
                if ((position < phrases['min'][counter]) & (charStart > before)):
                    before = charStart
                if ((position > phrases['max'][counter]) & (charStart < after) & (phrases['max'][counter] != 0)):
                    after = charStart
                self.logger_instance.log('debug', 'Actual cutting points: before: ' + str(before) + ' after: ' + str(after))
    
            self.logger_instance.log('debug', 'Table min: ' + str(phrases['min'][counter]) + ', actual min: ' + str(before) + ' table max: ' + str(phrases['max'][counter]) + ' actual max: ' + str(after))
            counter += 1
    
        if before + after == allWords:
            self.logger_instance.log('warn', 'This article ( ' + fileName + ' ) cant be reduced, because of the phrase limits.')
            return text
        else:
            self.logger_instance.log('info', 'Found the best cutting point before: ' + str(before) + ', after: ' + str(after) + '; calling the cutting funciton to reduce the text...')
            self.logger_instance.log('info', str(before) + ' ; ' + str(after))
            return text[before:after]
    
    def searchPhrases(self, text):
        # get the list of phrases
        phrasesExcelFile = pd.ExcelFile(self.file_for_cutting)
        phrases = pd.read_excel(phrasesExcelFile, 'for_searching')
    
        for phrase in phrases['find']:
            phrase = phrase.lower()
    
            # debug part of searching pharses
            self.logger_instance.log('debug', 'text --> ' + str(len(text)))
            self.logger_instance.log('debug', 'Phrase --> ' + phrase)
            self.logger_instance.log('debug', 'Positions --> ' + str(self.getPosition(text, phrase)))
    
            if len(self.getPosition(text, phrase)) != 0:
                return 1
        
        return 0
    
    def calculateAverageCharNumber4Pages(self):
        self.logger_instance.log('info', 'Calculating the average char number of 4 pages...')
        counter = 0
        sum = 0
        for fileName in os.listdir(self.articles_location):
            pdfTextLength = 0
            counter += 1
            file = os.path.join(self.articles_location, fileName)
            with fitz.open(file) as doc:
                for page in doc:
                    text = page.get_text()
                    pdfTextLength += len(text)
    
    
        self.logger_instance.log('info', 'Calculating done. Average char number is: ' + str(int(round(sum/counter, -3))))
    
        # round to nearest 1000
        return int(round(sum/counter, -3))
    
    
    def loadPdf(self, average):
        shortPdf = 0 # this is a counter for invalid pdfs ( which has less than 4 pages )
        pdfDoesNothavePhrases = 0
        pdfNoCuttingPoints = 0
        shortPdfAfterCut = 0
    
        # article names which has no cutting points
        articlesWithoutCuttingPoints = []
    
        # initialization of the final dataframe
        data = {'name':[], 'research_method':[],  'text':[], 'before_filtering':[], 'after_filtering':[], 'originalText':[]}
    
        for fileName in os.listdir(self.articles_location):
            file = os.path.join(self.articles_location, fileName)
    
            if path.exists(file) == False:
                self.logger_instance.log('info', 'PDF (' + file + ') not exists!')
                continue
    
            self.logger_instance.log('info', 'Loading pdf: ' + file)
    
            pdf = pdfplumber.open(file)
            pdfText = ''
   
            if len(pdf.pages) < 4 & self.is_cutting == True:
                self.logger_instance.log('warn', 'This file has less then 4 pages, so throw out: ' + fileName)
                shortPdf += 1
                continue

            with fitz.open(file) as doc:
                for page in doc:
                    text = page.get_text()
                    pdfText += text
    
            pdfText = pdfText.lower()
    
            pdfText = self.removeWritingSings(pdfText)
    
            pdfText = " ".join(pdfText.split())

            if (self.is_cutting == True):
                # size of the article before filtering
                self.logger_instance.log('debug', 'Length of the article before filtering: ' + str(len(pdfText)))
    
                # if article does not have any of the phrases, it is useless
                if self.searchPhrases(pdfText) == 0:
                    self.logger_instance.log('warn', 'Found an article, which is invalid, because does not contain any of the phrases: ' + fileName)
                    pdfDoesNothavePhrases += 1
                    continue
    
                reducedText = self.searchForCuttingPoints(pdfText, fileName)
                if len(pdfText) == len(reducedText):
                    self.logger_instance.log('debug', 'reducedText length: ' + str(len(reducedText)) + ' original text length: ' + str(len(pdfText)))
                    pdfNoCuttingPoints += 1
                    articlesWithoutCuttingPoints.append(file)
                    continue
                else:
                    # check if article has less than 4 pages ( at this point it we should inspect the number of chars it has )
                    if (len(reducedText) < average):
                        self.logger_instance.log('warn', 'This article is useless, beacuse after the cutting it is small: ' + fileName)
                        shortPdfAfterCut += 1
                        continue
    
                # length of the articles after successfully filtered
                self.logger_instance.log('debug', 'Length of the articles after filtering: ' + str(len(reducedText)))
    
            data['name'].append(fileName)

            if (self.cache_with_types == True):
                data['research_method'].append(self.getResearchMethod(fileName))

            data['originalText'].append(pdfText)

            if (self.is_cutting == True):
                data['text'].append(reducedText)
                data['before_filtering'].append(str(len(pdfText)))
                data['after_filtering'].append(str(len(reducedText)))

        if (self.is_cutting == False):
            del data['text']
            del data['before_filtering']
            del data['after_filtering']

        if (self.cache_with_types == False):
            del data['research_method']
    
        # save the dataframe to csv file
        dataFinal = pd.DataFrame(data)
        print(dataFinal)
        # saving it to excel not very good, because the cell char is limited to maximum 32k chars, and these articles are way more bigger than that limit
        # need to save dataframe into .pkl
        dataFinal.to_pickle(self.finalDataFrameFileName)
