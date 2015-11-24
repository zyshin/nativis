from django.shortcuts import render
import requests, json, math
from itertools import chain
from operator import itemgetter
from lxml import html

from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .features import *
from .features import _left_branching
from .tree import readtree


# Create your views here.
def make_response(status=200, content_type='text/plain', content=None):
	""" Construct a response to an upload request.
	Success is indicated by a status of 200 and { "success": true }
	contained in the content.

	Also, content-type is text/plain by default since IE9 and below chokes
	on application/json. For CORS environments and IE9 and below, the
	content-type needs to be text/html.
	"""
	response = HttpResponse()
	response.status_code = status
	response['Content-Type'] = content_type
	response.content = content
	return response


@csrf_exempt
def proxy(request):
	try:
		if request.method == 'GET':
			url = request.GET.get('url')
			params = json.loads(request.GET.get('params'))
			r = requests.get(url, params=params)
		elif request.method == 'POST':
			url = request.POST.get('url')
			params = json.loads(request.POST.get('params'))
			r = requests.post(url, params=params)
		# if r.status_code == requests.codes.ok:
		return make_response(content=r.content)
	except:
		raise Http404('Bad request')
	raise Http404('Invalid request type')


@csrf_exempt
def evaluate(request):
	if request.method == 'POST':
		text = request.POST.get('text')
		if not text:
			raise Http404('Bad request')
		text = ' '.join(text.split())
		sentences = _parse(text)
		r, sim_vec = _evaluate2(sentences)
		r += _evaluate1(sentences, sim_vec)
		return make_response(content=json.dumps(r), content_type='application/json')
	raise Http404('Invalid request type')


def _evaluate1(sentences, sim_vec):
	r = []
	for s in sentences:
		avg_feature = [f.calc([s[:3]]) for name, f in average_features]
		features, sim = _get_features([(s[-2], s[-1], avg_feature)])
		data = _get_decision_data(s)
		# dt = len(data[0])
		# if not data[0]:	# this is a cat
		# 	scores[1] = max(0.5, scores[0])
		scores = _score(features)
		scores[5] = 1
		r.append({'text': s[3], 'scores': scores, 'data': data})
	n = float(len(sentences));
	for i, j, v in sim_vec:
		penalty = (1-v) / (n-1)
		# if i - j <= 4 and j - i <= 4:
		r[i]['scores'][5] -= penalty
		r[j]['scores'][5] -= penalty
		# r[i]['scores'][5] = min(v, r[i]['scores'][5])
		# r[j]['scores'][5] = min(v, r[j]['scores'][5])
	# print len(features), 'features calculated:', ' '.join(['%d:%.3g' % kv for kv in enumerate(features)])
	return r


def _evaluate2(sentences):
	r = []
	sample = [(s[-2], s[-1], [f.calc([s[:3]]) for name, f in average_features]) for s in sentences]
	sample, sim_vec = _get_features(sample)
	x1, x2 = WI[-1](SCALING_PARAMS)[0]
	sim_vec = [(i, j, (v-x1)/x2) for i, j, v in sim_vec]
	# print ' '.join(['%d-%d=%.3f' % o for o in sim_vec])
	# print ' '.join(['%d-%d=%.3f' % (o[0], o[1], _dot([o[2], 0, 1], FW[-1])) for o in sim_vec])
	sim_vec = [(i, j, 1-_sigmoid(_dot([v, 0, 1], FW[-1]))) for i, j, v in sim_vec]
	# sim_vec = [(i, j, v) for i, j, v in sim_vec if v < 0.5]
	# sim_vec.sort(key=lambda x: x[2])
	print '\n'.join(['%d-%d=%.3f' % o for o in sim_vec])
	scores = _score(sample, multi=True)
	r.append({'text': ' '.join([s[3] for s in sentences]), 'scores': scores, 'data': []})
	# print len(features), 'features calculated:', ' '.join(['%d:%.3g' % kv for kv in enumerate(features)])
	return r, sim_vec


def _parse(text):
	url = 'http://nlp.stanford.edu:8080/corenlp/process'
	params = {'input': text, 'outputFormat': 'json'}
	r = requests.post(url, params=params)
	document = html.fromstring(r.text)
	s = document.xpath('//pre/text()')[0]
	parsed = json.loads(' '.join(s.split()))['sentences']
	sentences = []
	for r in parsed:
		begin, end = int(r['tokens'][0]['characterOffsetBegin']), int(r['tokens'][-1]['characterOffsetEnd'])
		tokens = [(t['word'], t['lemma'], t['pos']) for t in r['tokens']]
		fulltokens = [(t['word'], t['lemma'], t['pos'], int(t['characterOffsetBegin']), int(t['characterOffsetEnd'])) for t in r['tokens']]
		tokens[0] = (tokens[0][0][0].lower() + tokens[0][0][1:], tokens[0][1], tokens[0][2])	# set first character of sentence to lower
		stems = [STEMMER.stem(lemma) for word, lemma, pos in tokens]
		tree = r['parse']
		deps = '\n'.join(['%(dep)s(%(governorGloss)s-%(governor)s, %(dependentGloss)s-%(dependent)s)' % d for d in r['basic-dependencies']])
		sentences.append((tuple(tokens), tree, deps, text[begin:end], fulltokens, stems, readtree(tree)))
	return sentences


def _get_features(sample):
	new_fields = [name for name, f in average_features]
	size = len(sample)
	fields = [name for name, f in average_features]
	trees = [tree for tokens, tree, ff in sample]
	xx = [[v for i, v in enumerate(ff) if fields[i] in new_fields] for tokens, tree, ff in sample]
	xx = [sum(x) for x in zip(*xx)]
	m = float(size)
	n = float(xx[new_fields.index('word count')])
	avgfeatures2 = [x / m for x in xx]
	avgfeatures = [x / n for x in xx]
	ratiofeatures = [f.calc(xx, new_fields) for k, f in ratio_features]
	sim_vec = [f.calc_vec(trees) for k, f in similarity_features]	# sim is in array
	simfeatures = [sum([v for i, j, v in vec])/(m*(m - 1)/2) if m > 1 else 0 for vec in sim_vec]
	rbfeatures = [f(xx, new_fields, m) for k, f in readability_features]
	unifeatures = [f(sample) / m for k, f in unique_features]
	unifeatures2 = [f(sample) / (math.log(m)+1) for k, f in unique_features]
	return avgfeatures + avgfeatures2 + ratiofeatures + simfeatures + rbfeatures + unifeatures + unifeatures2, sim_vec[0]


def _get_decision_data(sentence):
	tokens, tree, deps, text, fulltokens, stems, tree2 = sentence
	offset = fulltokens[0][3];
	
	d1 = []
	# for i in xrange(len(fulltokens)):
	# 	if fulltokens[i][2] == 'NN' and (i == len(fulltokens)-1 or fulltokens[i+1][2] != 'NNS'):
	# 		missing = True
	# 		for word, lemma, pos, start, end in fulltokens[max(i-4, 0): i]:
	# 			if pos in ['DT', 'POS', 'PRP$', 'WDT', 'WP', 'WP$']:
	# 				missing = False
	# 				break
	# 		if missing:
	# 			d1.append([fulltokens[i][3]-offset, fulltokens[i][4]-offset])
	for i in xrange(len(fulltokens)):
		if fulltokens[i][2] == 'NN':
			missing = True
			for word, lemma, pos, start, end in fulltokens[i+1: i+3]:
				if pos in ['DT', 'POS', 'PRP$', 'WDT', 'WP', 'WP$', 'IN', '-LRB-']:
					break
				elif pos.startswith('NN'):
					missing = False
					break
			for word, lemma, pos, start, end in reversed(fulltokens[max(i-4, 0): i]):
				if pos in ['DT', 'POS', 'PRP$', 'WDT', 'WP', 'WP$', '-LRB-', 'CD']:
					missing = False
					break
				elif pos in ['VB', 'VBD', 'VBP', 'VBZ', '-RRB-']:
					break
			if missing:
				d1.append([fulltokens[i][3]-offset, fulltokens[i][4]-offset])

	d2 = []
	for word, lemma, pos, start, end in fulltokens:
		if stems.count(STEMMER.stem(lemma)) > 1 and lemma not in ['be'] and pos not in ['IN', 'CC', 'DT', 'POS', 'PRP$', 'WDT', 'WP', 'WP$', ',', '.', '(', ')', '--', ':']:
			d2.append([start-offset, end-offset])
		elif (lemma in COMMON_WORDS or lemma in FUNCTION_WORDS) and len(lemma) < 4 and (pos.startswith('VB') or pos.startswith('NN') or pos.startswith('JJ') or pos.startswith('RB')):	# or lemma in FUNCTION_WORDS
			d2.append([start-offset, end-offset])

	d3 = []
	for word, lemma, pos, start, end in fulltokens:
		if lemma in CLAUSE_WORDS:
			d3.append([start-offset, end-offset])

	d4 = []
	vp, level = _left_branching('VP', tree)
	for i in xrange(level, tree.count('(')):
		np, level2 = _left_branching('NP', tree, i)
		if np > 0:
			break
	if np > vp: np = 0
	if vp > 0 and vp < len(fulltokens):
		d4.append([fulltokens[np][3]-offset, fulltokens[vp][4]-offset])
	
	return [d1, d2, d3, d4]


SCALING_PARAMS = [(x1, x2 - x1) for x1, x2 in [
	(1.05954, 2.96341), (0, 1), (2.31111, 5.96257), (0.633333, 2.20104), (0, 0.431655), (0, 0.0454545), (0, 0.111111), (0, 0.0941176), (0.202703, 0.909091), (0.108108, 0.588235), (0.299517, 0.801471), (0.429268, 0.9666670000000001), (0, 0.111111), (0, 0.129032), (0, 0.6046510000000001), (0, 0.322581), (0, 0.15942), (0.399381, 1.70968), (0, 1.06612), (0, 2.45652), (1.84824, 5.48837), (0, 0.0434783), (0, 0.0113636), (0, 0.0138889), (0, 0.0148148), (0, 0.0150376), (0, 0.0322581), (0, 0.0131579), (0, 0.0588235), (0, 0.0240385), (0, 0.0294118), (0, 0.0188679), (0, 0.0289855), (0, 0.0141844), (0, 0.00460829), (0.288136, 1.63953), (0, 0.376471), (0.0227273, 0.244186), (0.227027, 1.25735), (0, 0.317647), (0.0227273, 0.236842), (0, 0.52439), (0, 0.0962567), (0.00813008, 0.297521), (0, 0.22619), (0.666667, 3.33721), (6.6, 48.85), (3.1, 39.9), (10.8, 205), (3.4, 73.3), (0, 11.4), (0, 0.466667), (0, 2.4), (0, 1.15), (0.9, 28.1), (0.6, 19.3), (1.9, 18.3), (2, 25.2), (0, 2.6), (0, 2.1), (0, 6.5), (0, 1), (0, 2.3), (4.9, 17.7), (0, 14.4), (0, 46.3), (10.9, 90.7), (0, 0.8), (0, 0.2), (0, 0.3), (0, 0.35), (0, 0.3), (0, 0.3), (0, 0.25), (0, 0.7), (0, 0.5), (0, 0.4), (0, 0.3), (0, 0.4), (0, 0.2), (0, 0.1), (3.1, 19.2), (0, 7.5), (0.1, 6.9), (1.1, 14.9), (0, 6.3), (0.1, 7), (0, 7.13333), (0, 2.9), (0.1, 3.6), (0, 5.1), (6.3, 41.65), (0, 0.786885), (0, 1.09091), (0, 1.07), (0.354839, 1.36111), (1.65138, 2.74757), (0.0017703, 0.111532), (-0.107842, 144.12), (-4.60667, 22.342), (2.66909, 27.0932), (3.1291, 22.4176), (-2.22089, 19.3035), (-6.59149, 23.2734), (3.04, 18.9), (0.6, 7.4), (0.3, 4.6), (9.68938, 166.006), (1.81676, 72.0763), (0.9083790000000001, 44.6017),
]]


W = [
	1.68356444912118, -1.69582425780921, 1.69224329835223, -1.35442264848879, -3.46222428430927, -0.215887442903943, 0.803965660139810, -2.82007646280992, -0.744226524121453, 3.78002276289997, 0.678545768813331, -3.37863227595655, -4.80054736929325, -1.21080637946866, 0.941502625605778, 3.96200598124529, 0.941502625605778, 0.880056310582479
# 10+50+100 a
# Accuracy = 84.9237% (1780/2096)
# Precision = 84.8616% (981/1156)
# Recall = 87.4332% (981/1122)
# F-score = 0.861282
# selected
# Accuracy = 77.5122% (1589/2050)
# Precision = 76.8624% (877/1141)
# Recall = 81.6574% (877/1074)
# F-score = 0.791874
]

_WI = [[i-1 for i in l] for l in [
	[44, 44+46],	# DT, DT old
	[9, 105, 106, 107, 108, 109, 110],	# word richness, 
	[21, 21+46, 17+46, 18+46],	# clauses,
	[20, 2],	# left branching,
	[98, 2],	# similarity, 2
]]
WI = [itemgetter(*l) for l in _WI]
I = itemgetter(*chain(*_WI))

FW = [
	[5.70258343827032, -0.521698725505038, -0.285971450018067-0.5],
# Accuracy = 74.9614% (485/647)
# Precision = 74.6875% (239/320)
# Recall = 74.6875% (239/320)
# F-score = 0.746875
	[-2.04651692069912, -4.03806923689034, -1.31326372263172, 0.104496832811934, -3.81924200674602, -1.15200418784549, 0.0509999052742764, 4.38266330542254-0.1],
	# [4.49464231262337/4, -1.68342723769153-3, 1.08455769068912*3, 2.83523516758073, -4.23840437490407+3, 0.321530156355196, 2.26328229302143, 3.12511474796995-1],
# Accuracy = 67.4618% (1414/2096)
# Precision = 67.8282% (837/1234)
# Recall = 74.5989% (837/1122)
# F-score = 0.710526
	[0.583109956343988, -0.753879508274601, -4.05413167606074/2, -4.42165918495081/2, 3.61128131362827/2-0.5],
# Accuracy = 72.1088% (1590/2205)
# Precision = 71.5272% (932/1303)
# Recall = 79.2517% (932/1176)
# F-score = 0.751916
	[5.02962654442321, 0, -0.405807893229573-0.4],
# Accuracy = 74.4977% (482/647)
# Precision = 75.5776% (229/303)
# Recall = 71.5625% (229/320)
# F-score = 0.735152
	[6.13065111556998/2, 0, -0.680050183375308],
# Accuracy = 66.6508% (1397/2096)
# Precision = 67.9694% (800/1177)
# Recall = 71.3012% (800/1122)
# F-score = 0.695955
]


def _score(f, multi=False):
	if not f:
		return 0
	# normalize f to [-1, 1]
	# f = [2*(f[WI[i]-1] - x1)/x2-1 for i, (x1, x2) in enumerate(SCALING_PARAMS)]
	# print ' '.join(['%.4f' % x for x in f])
	# valid = [1 if x >= 0 else 0 for x in f+[1]]
	f = [(f[i] - x1)/x2 for i, (x1, x2) in enumerate(SCALING_PARAMS)]
	detail = [1 - _sigmoid(_dot(WI[i](f)+(1,), w)) for i, w in enumerate(FW)]
	detail = [x-(x-0.5)/2 if x > 0.5 else x for x in detail]	# turn down green
	# overall = [sum(detail) / len(detail)]
	overall = [_dot(detail, [0.2, 0.2, 0.2, 0.2, 0.2])]
	# overall = [(max(detail)+min(detail)) / 2]
	# overall = [1 - _sigmoid(_dot(f+[1], W))]
	# overall = [1 - _sigmoid(_dot(f+[1], W))] if multi else [(max(detail)+min(detail)) / 2]
	# overall = [(1 - _sigmoid(_dot(f+[1], W)) + (max(detail)+min(detail)) / 2) / 2]
	return overall + detail


def _sign(x):
	return 1 if x >= 0 else -1


def _sigmoid(x):
	return 1 / (1 + math.exp(-x))

def _dot(x, y):
	assert len(x) == len(y), '%d != %d !!!' % (len(x), len(y))
	return sum(a*b for a, b in zip(x, y))
