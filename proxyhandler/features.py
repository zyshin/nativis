from __future__ import print_function
from django.conf import settings
import sys
from nltk import stem
STEMMER = stem.snowball.EnglishStemmer()


class Feature(object):
	"""docstring for Feature"""
	def __init__(self, calc_token=None, calc_sentence=None, calc=None):
		super(Feature, self).__init__()
		self.calc_token = calc_token or (lambda text, lemma, pos: 1/0)	# default: not implemented exception
		self.calc_sentence = calc_sentence or (lambda tokens, tree, deps: sum(self.calc_token(*t) for t in tokens))
		self.calc = calc or (lambda sentences: sum(self.calc_sentence(tokens, tree, deps) for tokens, tree, deps in sentences))

class PairWiseFeature(object):
	"""docstring for PairWiseFeature"""	
	trees = []
	# subsettrees = []

	def __init__(self, calc_pair, init_tree=False, use_tree=False, use_subsettree=False, full_pair=False):
		super(PairWiseFeature, self).__init__()
		self.calc_pair = calc_pair
		self.init_tree = init_tree
		self.use_tree = use_tree
		self.use_subsettree = use_subsettree
		self.full_pair = full_pair
	
	def calc(self, sentences):
		vec = self.calc_vec(sentences)
		return sum([v for i, j, v in vec])

	def calc_vec(self, sentences):
		n = len(sentences)
		if n < 2:
			return []
		# if self.init_tree:
			# from tree import readtree
			# PairWiseFeature.trees = [readtree(tree) for tokens, tree, deps in sentences]	# time consuming!
		# if self.use_subsettree and not self.subsettrees:
		# 	from tree import subsettrees
		# 	self.subsettrees = [subsettrees(tree) for tree in PairWiseFeature.trees]
		# items = (self.use_tree and PairWiseFeature.trees) or sentences	# (self.use_subsettree and self.subsettrees) or 
		items = sentences
		r = []
		if self.full_pair:
			for i, i1 in enumerate(items):
				for j, i2 in enumerate(items):
					if i < j:
						v = self.calc_pair(i1, i2)
						if hasattr(settings, 'DEBUG'):
							print('%.3f' % v, sep=' ', end=' ', file=sys.stderr)
						r.append((i, j , v))
				if hasattr(settings, 'DEBUG'):
					print('', file=sys.stderr)
		else:
			for i in xrange(n - 1):
				i1, i2 = items[i], items[i + 1]
				# try:
				# 	r += tree_similarity(readtree(tree1), readtree(tree2))
				# except Exception, e:
				# 	print e
				# 	print(tree1)
				# 	print(tree2)
				# 	exit()
				r.append((i, i+1, self.calc_pair(i1, i2)))
		return r

class RatioFeature(object):
	"""docstring for Feature"""
	def __init__(self, f1, f2):
		super(RatioFeature, self).__init__()
		self.f1, self.f2 = f1, f2
		self.calc = lambda fv, fk: float(fv[fk.index(f1)]) / float(fv[fk.index(f2)]) if fv[fk.index(f2)] else 0


sentence_count = Feature(calc=lambda sentences: len(sentences))
token_count = Feature(calc_sentence=lambda tokens, tree, deps: len(tokens))
word_count = Feature(lambda text, lemma, pos: 1 if _isword(text, lemma) else 0)
syllable_count = Feature(lambda text, lemma, pos: _syllables(text) if _isword(text, lemma) else 0)
complex_count = Feature(lambda text, lemma, pos: 1 if _isword(text, lemma) and _syllables(text) >= 3 else 0)
letter_count = Feature(lambda text, lemma, pos: len(text) if _isword(text, lemma) else 0)
not_feature = Feature(lambda text, lemma, pos: 1 if lemma == 'not' else 0)
and_feature = Feature(lambda text, lemma, pos: 1 if lemma == 'and' else 0)
# TODO: comparison! passive_feature = Feature(calc_sentence=lambda tokens, tree, deps: 1 if 'auxpass' in deps else 0)
passive_feature = Feature(calc_sentence=lambda tokens, tree, deps: deps.count('auxpass'))


# with open(settings.COMMON_WORD_LIST) as fin1, open(settings.FUNCTION_WORD_LIST) as fin2:
with open('data/Dale-Chall 3000.txt') as fin1, open('data/function 150.txt') as fin2:
	COMMON_WORDS = frozenset(fin1.read().split())
	FUNCTION_WORDS = frozenset(fin2.read().split())
	CLAUSE_WORDS = frozenset(['either', 'neither', 'nor', 'whether', 'yet', 'that', 'what', 'whatever', 'which', 'whichever', 'that', 'what', 'whatever', 'whatsoever', 'which', 'who', 'whom', 'whosoever', 'whose', 'how', 'however', 'whence', 'whenever', 'where', 'whereby', 'whereever', 'wherein', 'whereof', 'why', 'because', 'though', 'although', 'if', 'until', 'till'])
common_word_feature = Feature(lambda text, lemma, pos: 1 if lemma in COMMON_WORDS else 0)
function_word_feature = Feature(lambda text, lemma, pos: 1 if lemma in FUNCTION_WORDS else 0)


import re
def _isword(word, lemma):	# not punctuation (except eg. etc.), numbers, proper noun.
	return re.match('^[\w\\.]+$', lemma) and not re.search('[0-9A-Z]', word)

def _syllables(word):
	last = False
	count = 0
	for c in word.lower():
		cur = (c in 'aeiouy')
		if not last and cur:
			count += 1
		last = cur
	return count

short4_word_feature = Feature(lambda text, lemma, pos: 1 if _isword(text, lemma) and len(lemma) < 4 else 0)
short5_word_feature = Feature(lambda text, lemma, pos: 1 if _isword(text, lemma) and len(lemma) < 5 else 0)
conjunction_feature = Feature(lambda text, lemma, pos: 1 if _isword(text, lemma) and pos == 'CC' else 0)
fragment_feature = Feature(calc_sentence=lambda tokens, tree, deps: tree.count('(FRAG'))
dep_feature = Feature(calc_sentence=lambda tokens, tree, deps: deps.count('dep('))
no_s_feature = Feature(calc_sentence=lambda tokens, tree, deps: 1 if '(S\n' not in tree else 0)
clause_feature = Feature(calc_sentence=lambda tokens, tree, deps: tree.count('(SBAR'))


def _tree_depth(tree):
	r = depth = 0
	for c in tree:
		if c == '(':
			depth += 1
			r = max(r, depth)
		elif c == ')':
			depth -= 1
	return r

# def _left_branching(tokens):
# 	index = -1
# 	for i, (text, lemma, pos) in enumerate(tokens):
# 		if pos.startswith('VB'):
# 			index = i
# 			break
# 	return index + 1

def _left_branching(target, tree, level=0):
	r = depth = tokens = 0
	tgdepth = sys.maxint
	for i, c in enumerate(tree):
		if c == '(':
			depth += 1
			if tree[i+1:i+3] == target:
				if depth < tgdepth and depth >= level:
					tgdepth = depth
					r = tokens
		elif c == ')':
			depth -= 1
			if tree[i-1] != ')':
				tokens += 1
	return r, tgdepth

def _left_branching2(tree):
	vp, level = _left_branching('VP', tree)
	# np = 0
	# for i in xrange(level, tree.count('(')):
	# 	np, level2 = _left_branching('NP', tree, i)
	# 	if np > 0:
	# 		break
	np, level2 = _left_branching('NP', tree, level)
	if np > vp: np = 0
	return vp - np

def _left_branching_tree(target, tree):
	r = depth = nodes = 0
	tgdepth = len(tree)
	for i, c in enumerate(tree):
		if c == '(':
			depth += 1
			nodes += 1
			if tree[i+1:i+3] == target:
				if depth < tgdepth:
					tgdepth = depth
					r = nodes
		elif c == ')':
			depth -= 1
	return r

def _branching_factor(tree):
	r = 0
	stack = []
	for c in tree:
		if c == '(':
			stack.append(0)
		elif c == ')':
			r += stack.pop()
			if len(stack) > 0:
				stack[-1] += 1
	return r

tree_depth_feature = Feature(calc_sentence=lambda tokens, tree, deps: _tree_depth(tree))
left_branching_length_feature = Feature(calc_sentence=lambda tokens, tree, deps: _left_branching('VP', tree)[0])
left_branching_length_feature2 = Feature(calc_sentence=lambda tokens, tree, deps: _left_branching2(tree))
# left_branching_ratio_feature = Feature(calc_sentence=lambda tokens, tree, deps: _left_branching(tokens) / float(len(tokens)) if tokens else 0)
left_branching_tree_feature = Feature(calc_sentence=lambda tokens, tree, deps: _left_branching_tree('VP', tree))
# left_branching_tree_ratio_feature = Feature(calc_sentence=lambda tokens, tree, deps: _left_branching_tree(tree) / float(tree.count('(')) if '(' in tree else 0)
branching_factor_feature = Feature(calc_sentence=lambda tokens, tree, deps: _branching_factor(tree))
# branching_factor_ratio_feature = Feature(calc_sentence=lambda tokens, tree, deps: _branching_factor(tree) / float(tree.count('(')) if '(' in tree else 0)


TSG_PATTERNS = [
	r'\(NP \(NNP \w+?\) \(CD',	# (Model) (1)
	r'\(NP \(DT [Tt]hese\)\)',	# six of (these)
	r'\(NP \(DT [Tt]hat\) \(NN ',	# in (that) (language)
	r'\(NP \(DT [Tt]his\)\)',	# we did (this) using ...
	r'\(VP \(VBN used\)\n +?\(S',	# (used) (to describe it)
	r'\(NP .*?\n +? \(, ,\)\n +?\(NP .*?\n +? \(, ,\)\n +?\(CC and\)\n +?\(NP',	# (X), (Y), (and) (Z)
	r'\(NP \(DT each\)\)',	# (each) consists of ...

	r'\(VP \(VBZ is\)\n +?\(VP ',	# it (is) (shown below) == passive voice
	r'\(VP \(VBN .*?\n +?\(PP \(IN as\)\n +?\(NP',	# (considered) (as) (a term)
	r'\(NP \(JJ \w+?\) \(JJ \w+?\) \(NN',	# in (other) (large) (corpus). NN includes NNS etc.
	r'\(NP \(DT \w+\) \(JJ \w+\) \(CD one\)\)',	# (a) (correct) (one). //only one?
	r'\(NP \(DT the\) \(NN \w+\) \(NNS ',	# seen in (the) (test) (data)
	r'\(NP \(DT that\)\)',	# larger than (that) of ...
	r'\(PP \(IN about\)\n +?\(NP \(CD ',	# (about) (200,000) words. Other parsers may be r'\(QP \(IN about\) \(CD '
]
tsg_features = [Feature(calc_sentence=lambda tokens, tree, deps, pattern=pattern: len(re.findall(pattern, tree))) for pattern in TSG_PATTERNS]

def _tree_node_length(target, tree):
	r = 0
	stack = []
	tt = tree.split()
	for t in tt:
		if t[0] == '(':
			stack.append([t[1:], 0])
		while t[-1] == ')':
			t = t[:-1]
			tag, length = stack.pop()
			if tag == target:
				r += length
			if len(stack) > 0:
				stack[-1][1] += 1
	return r

def _missing_dt(tokens):
	r = 0
	for i in xrange(len(tokens)):
		if tokens[i][2] == 'NN':
			missing = True
			for word, lemma, pos in tokens[i+1: i+3]:
				if pos in ['DT', 'POS', 'PRP$', 'WDT', 'WP', 'WP$', 'IN', '-LRB-']:
					break
				elif pos.startswith('NN'):
					missing = False
					break
			for word, lemma, pos in reversed(tokens[max(i-4, 0): i]):
				if pos in ['DT', 'POS', 'PRP$', 'WDT', 'WP', 'WP$', '-LRB-', 'CD']:
					missing = False
					break
				elif pos in ['VB', 'VBD', 'VBP', 'VBZ', '-RRB-']:
					break
			if missing:
				r += 1
	return r

np_feature = Feature(calc_sentence=lambda tokens, tree, deps: tree.count('(NP'))
vp_feature = Feature(calc_sentence=lambda tokens, tree, deps: tree.count('(VP'))
prep_feature = Feature(calc_sentence=lambda tokens, tree, deps: tree.count('(PP'))
nn_feature = Feature(lambda text, lemma, pos: 1 if pos.startswith('NN') else 0)
vb_feature = Feature(lambda text, lemma, pos: 1 if pos.startswith('VB') else 0)
in_feature = Feature(lambda text, lemma, pos: 1 if pos == 'IN' else 0)
jj_feature = Feature(lambda text, lemma, pos: 1 if pos.startswith('JJ') else 0)
rb_feature = Feature(lambda text, lemma, pos: 1 if pos.startswith('RB') else 0)
dt_feature = Feature(lambda text, lemma, pos: 1 if pos == 'DT' else 0)
dt_missing_feature = Feature(calc_sentence=lambda tokens, tree, deps: _missing_dt(tokens))
nominal_feature = Feature(lambda text, lemma, pos: 1 if (pos.startswith('NN') and (text.endswith('ity') or text.endswith('ness') or text.endswith('tion') or text.endswith('ment') or text.endswith('ing'))) or pos == 'VBG' else 0)
np_length_feature = Feature(calc_sentence=lambda tokens, tree, deps: _tree_node_length('NP', tree))


from tree import tree_similarity, subsettree_kernel, subsettree_kernel2
similarity_feature0 = PairWiseFeature(tree_similarity, init_tree=False, use_tree=True, full_pair=True)
# similarity_feature = PairWiseFeature(tree_similarity, init_tree=False, use_tree=True)
similarity_kernel_feature = PairWiseFeature(subsettree_kernel, init_tree=False, use_tree=True, full_pair=True)
similarity_kernel_feature2 = PairWiseFeature(subsettree_kernel2, init_tree=False, use_tree=True, full_pair=True)


from math import sqrt
# def _vp_np(fv, fk):
# 	x= float(fv[fk.index('VP')])
# 	y = float(fv[fk.index('NP')])
# 	if not y:
# 		return 0
# 	return x / y

# def _vb_nn(fv, fk):
# 	x = float(fv[fk.index('VB_')])
# 	y = float(fv[fk.index('NN_')])
# 	if not y:
# 		return 0
# 	return x / y

# def _jj_nn(fv, fk):
# 	x = float(fv[fk.index('JJ_')])
# 	y = float(fv[fk.index('NN_')])
# 	if not y:
# 		return 0
# 	return x / y

# def _nn_np(fv, fk):
# 	x = float(fv[fk.index('NN_')])
# 	y = float(fv[fk.index('NP')])
# 	if not y:
# 		return 0
# 	return x / y

def _flesch_kincaid_reading_ease(fv, fk, sentences):
	words = float(fv[fk.index('word count')])
	syllables = float(fv[fk.index('syllable count')])
	if not sentences or not words:
		return 0
	return 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

def _flesch_kincaid_grade_level(fv, fk, sentences):
	words = float(fv[fk.index('word count')])
	syllables = float(fv[fk.index('syllable count')])
	if not sentences or not words:
		return 0
	return 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59

def _gunning_fog_score(fv, fk, sentences):
	words = float(fv[fk.index('word count')])
	complexWords = float(fv[fk.index('complex words')])
	if not sentences or not words:
		return 0
	return 0.4 * ( (words/sentences) + 100 * (complexWords/words) )

def _smog_index(fv, fk, sentences):
	complexWords = float(fv[fk.index('complex words')])
	if not sentences:
		return 0
	return 1.0430 * sqrt( 30 * complexWords/sentences ) + 3.1291

def _coleman_liau_index(fv, fk, sentences):
	words = float(fv[fk.index('word count')])
	characters = float(fv[fk.index('letter count')])
	if not words:
		return 0
	return 5.89 * (characters/words) - 0.3 * (sentences/words) - 15.8

def _automated_readability_index(fv, fk, sentences):
	words = float(fv[fk.index('word count')])
	characters = float(fv[fk.index('letter count')])
	if not sentences or not words:
		return 0
	return 4.71 * (characters/words) + 0.5 * (words/sentences) - 21.43

def _nunique_words(occurrence=0):
	def _inner(sentences):
		d = {}
		for stems, tree, ff in sentences:
			for l in stems:
				d[l] = d.get(l, 0) + 1
		return len([v for k, v in d.iteritems() if v >= occurrence])
	return _inner


# bow_feature1 = Feature(lambda text, lemma, pos: 1 if text == 'initial' else 0)
# bow_feature2 = Feature(lambda text, lemma, pos: 1 if text == 'techniques' else 0)
# bow_feature3 = Feature(lambda text, lemma, pos: 1 if text == 'probabilities' else 0)
# bow_feature4 = Feature(lambda text, lemma, pos: 1 if text == 'additional' else 0)
# bow_feature5 = Feature(lambda text, lemma, pos: 1 if text == 'fewer' else 0)
# bow_feature_1 = Feature(lambda text, lemma, pos: 1 if text == 'obtained' else 0)
# bow_feature_2 = Feature(lambda text, lemma, pos: 1 if text == 'proposed' else 0)
# bow_feature_3 = Feature(lambda text, lemma, pos: 1 if text == 'method' else 0)
# bow_feature_4 = Feature(lambda text, lemma, pos: 1 if text == 'morphological' else 0)
# bow_feature_5 = Feature(lambda text, lemma, pos: 1 if text == 'languages' else 0)


# style_feature1 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'used' and tokens[i+1][0] == 'to']))
# style_feature2 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][2] == 'JJR' and tokens[i+1][2] == 'NN']))
# style_feature3 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'has' and tokens[i+1][2] == 'VBN']))
# style_feature4 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'example' and tokens[i+1][0] == ',']))
# style_feature5 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'all' and tokens[i+1][0] == 'of']))
# style_feature6 = Feature(lambda text, lemma, pos: 1 if text == '\'s' else 0)
# style_feature7 = Feature(lambda text, lemma, pos: 1 if text == 'allow' else 0)
# style_feature8 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'has' and tokens[i+1][0].endswith('ed')]))
# style_feature9 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'may' and tokens[i+1][0] == 'be']))
# style_feature10 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == ';' and tokens[i+1][0] == 'and']))
# style_feature11 = Feature(lambda text, lemma, pos: 1 if text == 'e.g.' else 0)
# style_feature12 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'must' and tokens[i+1][2] == 'VB']))
# style_feature_1 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == ',' and tokens[i+1][0] == 'i.e.']))
# style_feature_2 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'have' and tokens[i+1][0] == 'to']))
# style_feature_3 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'the' and tokens[i+1][0].endswith('ing')]))
# style_feature_4 = Feature(lambda text, lemma, pos: 1 if text == 'thus' else 0)
# style_feature_5 = Feature(lambda text, lemma, pos: 1 if text == 'usually' else 0)
# style_feature_6 = Feature(lambda text, lemma, pos: 1 if text == 'mainly' else 0)
# style_feature_7 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == ',' and tokens[i+1][0] == 'because']))
# style_feature_8 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'the' and tokens[i+1][2] == 'VBN']))
# style_feature_9 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][2] == 'JJ' and tokens[i+1][0] == 'for']))
# style_feature_10 = Feature(lambda text, lemma, pos: 1 if text == 'cf' else 0)
# style_feature_11 = Feature(lambda text, lemma, pos: 1 if text == 'etc.' else 0)
# style_feature_12 = Feature(calc_sentence=lambda tokens, tree, deps: sum([1 for i in xrange(len(tokens) - 1) if tokens[i][0] == 'associated' and tokens[i+1][0] == 'to']))


average_features = [
	('token count', token_count),
	('word count', word_count),
	('letter count', letter_count),
	('syllable count', syllable_count),
	('complex words', complex_count),
	('not', not_feature),
	('and', and_feature),
	('passive voice', passive_feature),
	('common words', common_word_feature),
	('function words', function_word_feature),
	('len(words) < 4', short4_word_feature),
	('len(words) < 5', short5_word_feature),
	('conjunctions', conjunction_feature),
	('fragments', fragment_feature),
	('unkown deps', dep_feature),
	('no_S', no_s_feature),
	('clauses', clause_feature),
	('tree depth', tree_depth_feature),
	('left branching', left_branching_length_feature),
	# ('left branching %', left_branching_ratio_feature),
	('left branching2', left_branching_length_feature2),	# ('left branching tree', left_branching_tree_feature),
	# ('left branching tree %', left_branching_tree_ratio_feature),
	('branching factor', branching_factor_feature),
	# ('branching factor %', branching_factor_ratio_feature),
	('TSG-1: NP > NNP CD', tsg_features[0]),
	('TSG-2: NP > (DT these)', tsg_features[1]),
	('TSG-3: NP > (DT that) NN', tsg_features[2]),
	('TSG-4: NP > (DT this)', tsg_features[3]),
	('TSG-5: VP > (VBN used) S', tsg_features[4]),
	('TSG-6: NP > NP, NP, (CC and) NP', tsg_features[5]),
	('TSG-7: NP > (DT each)', tsg_features[6]),
	('TSG+1: VP > (VBZ is) VP', tsg_features[7]),
	('TSG+2: VP > VBN (PP (IN as) NP)', tsg_features[8]),
	('TSG+3: NP > JJ JJ NN', tsg_features[9]),
	('TSG+4: NP > DT JJ (CD one)', tsg_features[10]),
	('TSG+5: NP > (DT the) NN NNS', tsg_features[11]),
	('TSG+6: NP > (DT that)', tsg_features[12]),
	('TSG+7: QP > (IN about) CD', tsg_features[13]),
	('NP', np_feature),
	('VP', vp_feature),
	('PREP', prep_feature),
	('NN_', nn_feature),
	('VB_', vb_feature),
	('IN', in_feature),
	('JJ_', jj_feature),
	('DT', dt_feature),	#('RB_', rb_feature),
	('DT missing', dt_missing_feature),
	('nominal', nominal_feature),
	('NP length', np_length_feature),
]

ratio_features = [
	# ('token/word', RatioFeature('token count', 'word count')),
	# ('letter/word', RatioFeature('letter count', 'word count')),
	# ('syllable/word', RatioFeature('syllable count', 'word count')),
	('VP/NP', RatioFeature('VP', 'NP')),
	('VB_/NN_', RatioFeature('VB_', 'NN_')),
	('JJ_/NN_', RatioFeature('JJ_', 'NN_')),
	('NN_/NP', RatioFeature('NN_', 'NP')),
	('Average NP length', RatioFeature('NP length', 'NP')),
]

similarity_features = [
	('similarity', similarity_feature0),
	# ('similarity_2', similarity_feature),
	# ('tree kernel (log)', similarity_kernel_feature),
	# ('tree kernel2 (log)', similarity_kernel_feature2),
]

readability_features = [
	('flesch_kincaid_reading_ease', _flesch_kincaid_reading_ease),
	('flesch_kincaid_grade_level', _flesch_kincaid_grade_level),
	('gunning_fog_score', _gunning_fog_score),
	('smog_index', _smog_index),
	('coleman_liau_index', _coleman_liau_index),
	('automated_readability_index', _automated_readability_index),
]

unique_features = [
	('unique 1', _nunique_words(1)),
	('unique 2', _nunique_words(2)),
	('unique 3', _nunique_words(3)),
	# ('unique 4', _nunique_words(4)),
	# ('unique 5', _nunique_words(5)),
]

# import itertools
# def _get_lemmas(sentences):
# 	return itertools.chain(*[[t[1] for t in tokens if _isword(t[0], t[1])] for tokens, tree, deps in sentences])

def _get_lemmas(tokens):
	return [t[1] for t in tokens if _isword(t[0], t[1])]

# unique_word_feature = Feature(calc=lambda sentences: len(frozenset([l for l in _get_lemmas(sentences)])))
