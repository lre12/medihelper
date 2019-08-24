from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import medicine
from konlpy.tag import Twitter
from openpyxl import load_workbook

import json
import math, sys


def index(request):
	return render(request, 'medihelper/index.html')

def result(request):
	q = request.GET.get('q')

	if q:
		bf = BayesianFilter()
		xl = load_workbook("C:\\test.xlsx", data_only = True) # inverted index를 위한 excel파일
		xl_symptom = xl['Sheet1']
		xl_category = xl['Sheet2']

		for i in range(2, len(xl_category['A']) + 1):
			row = xl_category[i]
			bf.set_category_size(row[0].value, row[1].value)

		bf.fit(xl_symptom)
		xl.close()
		pre, second, third, scorelist = bf.predict(q)
	first_medi = medicine.objects.filter(information__contains=pre)
	second_medi = medicine.objects.filter(information__contains=second)
	third_medi = medicine.objects.filter(information__contains=third)
	context = {
		'first_medi':first_medi,
		'second_medi':second_medi,
		'third_medi':third_medi,
		'pre':pre,
		'second':second,
		'third':third
		}

	return render(request, 'medihelper/result.html', 
		context
		)

def list(request):
	medilist = medicine.objects.all()
	context = {'medilist':medilist}
	return render(request, 'medihelper/list.html',context)

def stormache(request):
	pre = request.GET.get('pre')
	stormache = medicine.objects.filter(information__contains=pre)
	context = {
		'stormache':stormache,
	}
	return render(request, 'medihelper/stormache.html', context)

class BayesianFilter:

    def __init__(self):
        self.word_dict = {} # 카테고리별 단어
        self.category_dict = {} # 카테고리 score
        self.category_size = {} # 카테고리 size

    def set_category_size(self, category , size):
        weight = 105 # 가중치를 고려한 사이즈 ( 15위까지의 가중치 )
        self.category_size[category] = size + weight

    # 형태소 분석하기 --- 입력 값
    def split(self, text):
        results = []
        twitter = Twitter()
        # 단어의 기본형 사용
        malist = twitter.pos(text, norm=True, stem=True)
        for word in malist:
            # 어미/조사/구두점 등은 대상에서 제외
            if not word[1] in ["Josa", "Eomi", "Punctuation", "KoreanParticle", "Number", "Foreign"]:
                if word[0] in self.word_dict.keys():
                    results.append(word[0])
        return results

    def word_list(self, word, symptom, weight):
        # 단어를 카테고리에 추가하기
        if not symptom in self.word_dict: # 역색인을 위한 증상 카테고리가 없으면 추가
            self.word_dict[symptom] = {}

        if not word in self.word_dict[symptom]: # 단어+가중치 추가
            self.word_dict[symptom][word] = weight


    # 카테고리 추가 // 예측에 사용될 진짜 카테고리
    def category_list(self, category):
        if not category in self.category_dict:
            self.category_dict[category] = math.log(self.category_size[category]/sum(self.category_size.values()))

    # 단어 학습하기
    def fit(self, index_file):
        for i in range(2, len(index_file['A']) + 1):
            row = index_file[i]
            self.word_list(row[2].value, row[0].value, row[1].value) # word, symptom, weight
            self.category_list(row[2].value) # 카테고리로 사용될 word


    # 단어 리스트에 점수 매기기
    def score(self, words): # words: 입력값
        for word in words:
            for category in self.word_dict[word]: #그 단어로 카테고리마다 스코어 추가시켜줌
                self.category_dict[category] += math.log(self.word_prob(category, word))
            for leftover in self.category_dict.keys():
                if leftover not in self.word_dict[word]:
                    self.category_dict[leftover] += math.log(1 / self.category_size[leftover])


    # 예측하기
    def predict(self, text):
        first = None
        second = None
        third = None
        max_score = -sys.maxsize
        second_score = -sys.maxsize
        third_score = -sys.maxsize
        words = self.split(text)
        self.score(words)

        for category in self.category_dict.keys():
            if self.category_dict[category] > max_score:
                max_score = self.category_dict[category]
                first = category
            elif self.category_dict[category] > second_score:
                second_score = self.category_dict[category]
                second = category
            elif self.category_dict[category] > third_score:
                third_score = self.category_dict[category]
                third = category
        return first, second, third, self.category_dict

    # 카테고리 내부의 단어 출현 계산
    def word_prob(self, category, symptom):
        n = self.word_dict[symptom][category] + 1
        d = self.category_size[category]
        return n / d