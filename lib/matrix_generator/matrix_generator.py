###############################################################################
#
#       Matrix generator script
#
###############################################################################
#
#                                IMPORTS
#
###############################################################################
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import pandas as pd
import datetime
import re
import os

from logger.logger import Logger

class MatrixGenerator():
    wordMatrixSaveFileName = 'document_term_matrix.csv'
    logger_instance = Logger.getInstance()
    lem = WordNetLemmatizer()

    def __init__(self, cache_file, words_file, output_folder, lemmatize, cutted, types_csv, generate_model, binarize = False):
        self.cache_file = pd.read_pickle(cache_file)
        excel = pd.ExcelFile(words_file)
        self.words = pd.read_excel(excel)

        if os.path.isdir(output_folder) == False:
            os.mkdir(output_folder)

        self.finalSavedFilePath = output_folder

        self.lemmatize = lemmatize
        self.cutted = cutted

        if (os.path.exists(types_csv)):
            self.types_csv = pd.read_csv(types_csv)

        self.generate_model = generate_model

        self.binarize = binarize

    def lemmatizeText(self, text):
        lemmatizedText=''
        text = text.replace(',', ' ')
        text = text.replace('.' ,' ')
        for word in text.split():
            lemmatizedText += ' ' + self.lem.lemmatize(word)
        return lemmatizedText

    def getResearchMethod(self, title):
        for index, row in self.types_csv.iterrows():
            title = os.path.splitext(title)[0]
            types_title = os.path.splitext(row['title'])[0]

            if title == types_title:
                return row['research_method']

    def isfloat(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def countOfWords(self, rawPhrase, rawText):

        positions = []
        counter = 0
        index = 0
        ## counter to calculate the position of the word in the text
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
                                ## found an phrase
                                counter += 1
                                positions.append(round((charCounter - matchesWordLength + 1)/allChar*100))
                                index = 0
                        else: index = 0

                    elif len(phrase) == index:
                        ## found an phrase
                        counter += 1
                        positions.append(round((charCounter - matchesWordLength + 1)/allChar*100))
                        index = 0

            wordCounter += 1

        if ((self.binarize == True) & (counter > 0)):
            return 1
        else: return counter

    def getAllPhrase(self):
        counter = 0
        for w in self.words['words']:
            counter += 1

        return counter

    def generate_matrix(self):
        # initialize dataFrame
        data_original = {'title': [], 'word':[], 'word_counter':[], 'research_method': []}

        data_original_lemmatized = {'title': [], 'word':[], 'word_counter':[], 'research_method': []}

        data_cutted = {'title': [], 'word':[], 'word_counter':[], 'research_method': []}

        data_cutted_lemmatized = {'title': [], 'word':[], 'word_counter':[], 'research_method': []}

        if (self.generate_model == False):
            del data_original['research_method']
            del data_original_lemmatized['research_method']
            del data_cutted['research_method']
            del data_cutted_lemmatized['research_method']

        # iterate through the articles original text
        self.logger_instance.log('info', 'Starting counting phrases in original text...')

        phraseCounter = 0
        allPhrase = self.getAllPhrase()

        for w in self.words['words']:
            w = w.lower()
            articleCounter = 0
            phraseCounter += 1
            self.logger_instance.log('info', 'Phrase: ' + w + ' ' + str(phraseCounter) + '/' + str(allPhrase))

            for index, row in self.cache_file.iterrows():
                count_original = 0
                count_original_lemmatized = 0

                articleCounter += 1

                # ORIGINAL TEXT
                count_original = self.countOfWords(w, row['originalText'])
                data_original['title'].append(row['name'])
                data_original['word'].append(w)
                data_original['word_counter'].append(count_original)

                if (self.generate_model):
                    data_original['research_method'].append(self.getResearchMethod(row['name']))

                if (self.lemmatize):
                    # ORIGINAL LEMMATIZED
                    count_original_lemmatized = self.countOfWords(w, self.lemmatizeText(row['originalText']))
                    data_original_lemmatized['title'].append(row['name'])
                    data_original_lemmatized['word'].append(w)
                    data_original_lemmatized['word_counter'].append(count_original_lemmatized)

                    if (self.generate_model):
                        data_original_lemmatized['research_method'].append(self.getResearchMethod(row['name']))

                if (self.cutted):
                    # CUTTED
                    count_cutted = self.countOfWords(w, row['text'])
                    data_cutted['title'].append(row['name'])
                    data_cutted['word'].append(w)
                    data_cutted['word_counter'].append(count_cutted)

                    if (self.generate_model):
                        data_cutted['research_method'].append(self.getResearchMethod(row['name']))

                if (self.cutted & self.lemmatize):
                    # CUTTED LEMMATIZED
                    count_cutted_lemmatized = self.countOfWords(w, self.lemmatizeText(row['text']))
                    data_cutted_lemmatized['title'].append(row['name'])
                    data_cutted_lemmatized['word'].append(w)
                    data_cutted_lemmatized['word_counter'].append(count_cutted_lemmatized)

                    if (self.generate_model):
                        data_cutted_lemmatized['research_method'].append(self.getResearchMethod(row['name']))

        self.logger_instance.log('info', 'Calculating has been finished, generating the word matrix')

        ## making the pivot table
        data_original = pd.DataFrame(data_original).pivot_table(index='title', columns='word', values='word_counter')

        if (self.lemmatize):
            data_original_lemmatized = pd.DataFrame(data_original_lemmatized).pivot_table(index='title', columns='word', values='word_counter')

        if (self.cutted):
            data_cutted = pd.DataFrame(data_cutted).pivot_table(index='title', columns='word', values='word_counter')

        if (self.cutted & self.lemmatize):
            data_cutted_lemmatized = pd.DataFrame(data_cutted_lemmatized).pivot_table(index='title', columns='word', values='word_counter')

        ## merging with the types csv if the option is to make model
        if (self.generate_model):
            self.types_csv.drop(['Unnamed: 0'], axis=1, inplace=True)
            merged_original = pd.merge(self.typeFile, data_original, on='title')

            if (self.lemmatize):
                merged_original_lemmatized = pd.merge(self.typeFile, data_original_lemmatized, on='title')

            if (self.cutted):
                merged_cutted = pd.merge(self.typeFile, data_cutted, on='title')

            if (self.cutted & self.lemmatize):
                merged_cutted_lemmatized = pd.merge(self.typeFile, data_cutted_lemmatized, on='title')

        else:
            merged_original = data_original
            merged_original_lemmatized = data_original_lemmatized
            merged_cutted = data_cutted
            merged_cutted_lemmatized = data_cutted_lemmatized

        ## save to csv files
        pd.DataFrame(merged_original).to_csv(self.finalSavedFilePath + '/' + self.wordMatrixSaveFileName)

        if (self.lemmatize):
            pd.DataFrame(merged_original_lemmatized).to_csv(self.finalSavedFilePath + '/'  + self.wordMatrixSaveFileName)
        if (self.cutted):
            pd.DataFrame(merged_cutted).to_csv(self.finalSavedFilePath + '/' + self.wordMatrixSaveFileName)
        if (self.cutted & self.lemmatize):
            pd.DataFrame(merged_cutted_lemmatized).to_csv(self.finalSavedFilePath + '/' + self.wordMatrixSaveFileName)

        self.logger_instance.log('info', 'Document-term matrix generating is completed.')