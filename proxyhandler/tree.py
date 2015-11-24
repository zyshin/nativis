StringTypes = [type(''), type(u'')]

def readtree( text ):
	text.strip()
	# print text
	po = 0
	cnt = 0
	left = 0
	tree = []
	word = ""
	length = len(text)
	leaf = True
	while po < length:
		char = text[po]
		if char == "\n": 
			po += 1
			continue
		elif char == "(":
			if word != "" and cnt == 1:
				tree.append(word)
			word = ""
			cnt += 1
			if cnt == 2: 
				left = po
		elif char == ")":
			cnt -= 1
			if cnt == 1:
				leaf = False
				newTree = readtree(text[left:po+1])
				tree.append(newTree)
				word = ""
		elif char != " ":
			word += char
		elif char == " ":
			if word != "" and cnt == 1:
				tree.append(word)
			word = ""
		po += 1
	if leaf and word != "": tree.append(word)
	if tree[0] == "ROOT" and tree[1][0] == "S":
		tree = tree[1]
		length = len(tree)
		if tree[length-1] == [".","."]:
			tree = tree[0:length-1]
	return tree

def countleaf(tree):
	if type(tree[1]) in StringTypes:
		# print tree
		return 1
	else:
		size = len(tree)
		cnt = 0
		for i in range(1, size):
			cnt += countleaf(tree[i])
		return cnt

def calculable(label):
	three = ["ADVP","DFL","IP"]
	two = ["NN","NR","NP","VV","VE","VA","VP"]
	zero = ["PU"]
	if label in three: return 3
	elif label in two: return 2
	elif label in zero: return 0
	return 1

def calcuRR(tree1, tree2, a, b):
	son = calculable(tree1[a][0]) * calcuSizeRatio(tree1,a) + calculable(tree2[b][0]) * calcuSizeRatio(tree2,b)
	size1 = len(tree1); size2 = len(tree2)
	sum = 0
	for i in range(1,size1):
		sum += calculable(tree1[i][0]) * calcuSizeRatio(tree1,i)
	for j in range(1,size2):
		sum += calculable(tree2[j][0]) * calcuSizeRatio(tree2,j)
	return 1.0 * son/sum

def calcuSizeRatio(tree, po):
	allSize = countleaf(tree)
	size = countleaf(tree[po])
	return 1.0 * size / allSize

def sizePenal(tree1, tree2):
	size1 = countleaf(tree1)
	size2 = countleaf(tree2)
	min = size1; max = size2
	if size2 < size1:
		min = size2; max = size1
	ratio = 1.0 * ( min + 1 ) / max
	if ratio > 1: ratio = 1
	return ratio

def calcuF(tree1,tree2):
	if type(tree1[1]) in StringTypes or type(tree2[1]) in StringTypes:
		if tree1[0] == tree2[0]: return 1
		return 0
	size1 = len(tree1)
	size2 = len(tree2)
	lcs_l = [[0 for col in range(size2)] for row in range(size1)]
	lcs_f = [[-1 for col in range(size2)] for row in range(size1)]
	for i in range(1,size1):
		for j in range(1,size2):
			if tree1[i][0] == tree2[j][0]:
				lcs_l[i][j] = lcs_l[i-1][j-1] + 1
				lcs_f[i][j] = 2
			elif lcs_l[i-1][j] >= lcs_l[i][j-1]:
				lcs_l[i][j] = lcs_l[i-1][j]
				lcs_f[i][j] = 1
			else:
				lcs_l[i][j] = lcs_l[i][j-1]
				lcs_f[i][j] = 3
	i = size1-1
	j = size2-1
	sim = 0
	unmatched = 0
	allwoads = countleaf(tree1) + countleaf(tree2)
	while i > 0 and j > 0:
		if lcs_f[i][j] == 2:
			RR = calcuRR(tree1, tree2, i, j)
			sim += RR * tree_similarity(tree1[i],tree2[j]) * sizePenal(tree1[i],tree2[j])
			i -= 1; j -= 1
		elif lcs_f[i][j] == 1:
			unmatched += countleaf(tree1[i])
			i -= 1
		elif lcs_f[i][j] == 3:
			unmatched += countleaf(tree2[j])
			j -= 1
	while i > 0:
		unmatched += countleaf(tree1[i])
		i -= 1
	while j > 0:
		unmatched += countleaf(tree2[j])
		j -= 1
	sim *= 1.0 * (allwoads - unmatched) / allwoads
	if sim < 0: sim = 0
	return sim

def calcuTheta(label):
	if label == "S" or "ROOT": return 1
	elif label == "NP" or label == "NN" or label == "NR": return 0.2
	return 0.5

def tree_similarity(tree1, tree2):
	label = tree1[0]
	theta = calcuTheta(label)
	sim = theta * calcuF(tree1,tree2) + (1 - theta)
	return sim

def sent_similarity(tree1,tree2):
	printfloor(tree1)
	print(tree1)
	printfloor(tree2)
	print(tree2)
	sim = tree_similarity(tree1,tree2)
	min1 = tree_similarity(tree1,tree1)
	min2 = tree_similarity(tree2,tree2)
	if min1 < min2: sim = sim / min1
	else: sim = sim / min2
	return sim

def printfloor(tree):
	size = len(tree)
	out = ""
	for i in range(1,size):
		out += " " + tree[i][0]
	print out

from itertools import product
import operator, math
def _nsubsettrees(tree, setsbuffer):
	if type(tree[1]) is not list:
		count = 1
	else:
		count = reduce(operator.mul, [_nsubsettrees(subtree, setsbuffer) + 1 for subtree in tree[1:]], 1)
	setsbuffer.append(count)
	return count

def nsubsettrees(tree):
	setsbuffer = []
	_nsubsettrees(tree, setsbuffer)
	return sum(setsbuffer)
	# return math.log(sum(setsbuffer))

def _traversetree(tree, setsbuffer):
	if type(tree[1]) is list:
		for subtree in tree[1:]:
			_traversetree(subtree, setsbuffer)
	setsbuffer.append(tree)

def _subsettree_kernel(t1, t2):
	if t1[0] != t2[0]:
		return 0
	# assert t1[0] == t2[0]
	if type(t1[1]) is not list and type(t2[1]) is not list:
		return 1 if t1[1] == t2[1] else 0
	subtrees1 = [subtree[0] for subtree in t1[1:]]
	subtrees2 = [subtree[0] for subtree in t2[1:]]
	if subtrees1 != subtrees2:
		return 0
	count = reduce(operator.mul, [_subsettree_kernel(t1[i+1], t2[i+1]) + 1 for i in xrange(len(t1)-1)], 1)
	return count

def subsettree_kernel(t1, t2):
	l1, l2 = [], []
	_traversetree(t1, l1)
	_traversetree(t2, l2)
	r = sum(_subsettree_kernel(st1, st2) for st1, st2 in product(l1, l2))
	# return r if r < 1000 else 0
	return math.log(r) if r else 0

def subsettree_kernel2(t1, t2):
	l12 = subsettree_kernel(t1, t2)
	if not l12:
		return 0
	l1, l2 = nsubsettrees(t1), nsubsettrees(t2)
	# return l12 / float(l1 + l2 - l12)
	return math.log(l12) / math.log(l1 + l2 - l12)


if __name__ == '__main__':
	# I don't know who you are.
	sample1 = "(ROOT (S (NP (PRP I)) (VP (VBP do) (RB n't) (VP (VB know) (SBAR (WHNP (WP who)) (S (NP (PRP you)) (VP (VBP are)))))) (. .)))"
	# He know what it is.
	sample2 = "(ROOT (S (NP (PRP He))(VP (VBP know)(SBAR(WHNP (WP what))(S(NP (PRP it))(VP (VBZ is)))))(. .)))"
	# My dog also likes eating sausage
	sample3 = "(ROOT(S(NP (PRP$ My) (NN dog))(ADVP (RB also))(VP (VBZ likes)(S(VP (VBG eating) (NP (NN sausage)))))(. .)))"
	# I love driving car
	sample4 = "(ROOT(S(NP (PRP I)) (VP (VBP like)(S(VP (VBG driving)(NP (NN car)))))))"
	# There is no car
	sample5 = "(ROOT(S(NP (EX There)) (VP (VBZ is) (NP (DT no) (NN car)))))"
	# There are three apples
	sample6 = "(ROOT(S(NP (EX There))(VP (VBP are)(NP (CD three) (NNS apples)))))"
	# Let me go
	sample7 = "(ROOT(S(VP (VB Let)(S(NP (PRP me))(VP (VB go))))))"

	# this group , born after 1980 and often referred to as the Millennial generation or digital natives , has received a great deal of research attention on their digital technology use , e.g. , in terms of its purpose for them , and their skills .
	tree1 = u'(ROOT\n  (S\n    (NP\n      (NP (DT This) (NN group))\n      (, ,)\n      (VP\n        (VP (VBN born)\n          (PP (IN after)\n            (NP (CD 1980))))\n        (CC and)\n        (VP\n          (ADVP (RB often))\n          (VBN referred)\n          (S\n            (VP (TO to)))\n          (PP (IN as)\n   (NP\n              (NP (DT the) (JJ Millennial) (NN generation))\n   (CC or)\n              (NP (JJ digital) (NNS natives))))))\n      (, ,))\n (VP (VBZ has)\n      (VP (VBN received)\n        (NP\n          (NP\n  (NP\n              (NP (DT a) (JJ great) (NN deal))\n              (PP (IN of)\n                (NP\n                  (NP (NN research) (NN attention))\n              (PP (IN on)\n                    (NP (PRP$ their) (JJ digital) (NN technology) (NN use))))))\n            (, ,) (FW e.g.) (, ,))\n          (PP (IN in)\n            (NP\n              (NP (NNS terms))\n              (PP (IN of)\n                (NP\n                  (NP (PRP$ its) (NN purpose))\n          (PP (IN for)\n                    (NP (PRP them)))))))\n          (, ,)\n          (CC and)\n          (NP (PRP$ their) (NNS skills)))))\n    (. .)))'
	# yet even as information and communications technology grows more integral to young people 's lives , a question remains as to how this generation -- immersed in ICT since childhood -- manages their online behavior .
	tree2 = u"(ROOT\n  (S (RB Yet)\n    (SBAR (RB even) (IN as)\n      (S\n        (NP (NN information)\n          (CC and)\n          (NNS communications) (NN technology))\n        (VP (VBZ grows)\n          (ADJP (RBR more) (JJ integral)\n (PP (TO to)\n              (NP\n                (NP (JJ young) (NNS people) (POS 's))\n                (NNS lives)))))))\n    (, ,)\n    (NP (DT a) (NN question))\n    (VP (VBZ remains)\n      (PP (IN as)\n        (PP (TO to)\n          (SBAR\n            (WHADVP (WRB how))\n            (S\n              (NP\n        (NP (DT this) (NN generation))\n                (PRN (: --)\n       (VP (VBN immersed)\n                    (PP (IN in)\n  (NP (NN ICT)))\n                    (PP (IN since)\n                      (NP(NN childhood))))\n                  (: --)))\n              (VP (VBZ manages)\n                (NP (PRP$ their) (JJ online) (NN behavior))))))))\n    (. .)))"

	# however , with some exceptions , research has not addressed how and to what extent ICT use might be associated with stress in these young people .
	tree3 = u"(ROOT(S(ADVP (RB however))(, ,)(PP (IN with)(NP (DT some) (NNS exceptions))) (, ,)  (NP (NN research)) (VP (VBZ has) (RB not)    (VP (VBN addressed)     (UCP(FRAG(WHADVP (WRB how)))(CC and)(SBAR(WHPP (TO to)(WHNP (WDT what) (NN extent)))(S(NP (NNP ICT) (NN use))(VP (MD might)(VP (VB be)(VP (VBN associated)(PP (IN with)(NP(NP (NN stress))(PP (IN in)(NP (DT these) (JJ young) (NNS people)))))))))))))(. .)))"

	# however , in a later study , high ICT usage without breaks was found to be associated with current , but not prolonged stress , and only for young women .
	tree4 = u"(ROOT(S(ADVP (RB however)) (, ,)    (PP (IN in)    (NP (DT a) (JJ later) (NN study))) (, ,)  (NP  (NP (JJ high) (NN ICT) (NN usage))  (PP (IN without)  (NP (NNS breaks))))  (VP (VBD was)(VP (VBN found)  (S  (VP (TO to)   (VP (VB be)(VP (VBN associated)  (PP  (PP (IN with)(NP  (NP (JJ current))   (, ,)  (CONJP (CC but)    (RB not))  (NP (JJ prolonged) (NN stress)))) (, ,)(CC and) (RB only)  (PP (IN for)    (NP (JJ young) (NNS women)))))))))) (. .)))"

	# in this paper , we investigate the detailed ICT usage of a sample of the Millennial generation .
	tree5 = u"(ROOT (S (PP (IN in) (NP (DT this) (NN paper))) (, ,) (NP (PRP we)) (VP (VBP investigate) (NP (NP (DT the) (JJ detailed) (NN ICT) (NN usage)) (PP (IN of) (NP (NP (DT a) (NN sample)) (PP (IN of) (NP (DT the) (JJ Millennial) (NN generation))))))) (. .)))"
	
	# with ICT , the multitude of social media sites provide ample opportunities for switching .
	tree6 = u"(ROOT (S (PP (IN with) (NP (NN ICT))) (, ,) (NP (NP (DT the) (NN multitude)) (PP (IN of) (NP (JJ social) (NNS media) (NNS sites)))) (VP (VBP provide) (NP (NP (JJ ample) (NNS opportunities)) (PP (IN for) (NP (NN switching))))) (. .)))"
	
	# definition 2 . 3 -LRB- Pre-terminals -RRB- .
	test1 = u"(ROOT(NP(NP(NP (NN Definition)) (SBAR(S   (NP (CD 2) (. .))))) (NP (NP (CD 3)) (PRN (-LRB- -LRB-) (NP (NNS Pre-terminals)) (-RRB- -RRB-)))(. .)))"

	# . , in which case it form , where for Definition guage of Let is defined if is the skeletal .
	test2 = u"(ROOT (NP (NP (. .)) (PRN (, ,) (SBAR(WHPP (IN in) (WHNP (WDT which) (NN case)))(S (NP (PRP it)) (VP (VBP form))))(, ,))(SBAR  (WHADVP (WRB where))  (S  (PP (IN for)  (NP (NNP Definition))) (NP  (NP (NN guage))    (PP (IN of)   (NP (NNP Let)))) (VP (VBZ is)  (VP (VBN defined) (SBAR (IN if)(S (VP (VBZ is)  (NP (DT the) (JJ skeletal)))))))))  (. .)))"
	
	s1 = '(ROOT (S (NP (DT this)) (VP (VBZ is) (NP (NP (DT a) (NN cat)) (SBAR (WHNP (WDT that)) (S (VP (VBZ runs) (ADVP (RB fast))))))) (. .)))'
	s2 = '(ROOT (S (NP (DT that)) (VP (VBZ is) (NP (DT a) (JJ beautiful) (NN dog))) (. .)))'

	# print tree_similarity(readtree(sample1),readtree(sample2))
	print tree_similarity(readtree(s1),readtree(s2))

