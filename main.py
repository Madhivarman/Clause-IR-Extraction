"""
   Problem Approach
   raw_statement -> (Entity,Relation) Match its Entity to corresponding Preposition
   Method : Clause-Based Open Information Extraction
   Clause -> group of words that contain this pattern (Subject , Verb)
   Steps : 
   	    1. Convert the statement into Triplet form (E1,R,E2) [E1,E2 Entities, R Relations] Entities are (NN,NNP)
   	    2. Resolve NN that refers to Specific Entity.(NN->NNP)
   	    3. Remove all dominant rules and keep only Relevant ones
   	    4. Remove static words

   There are total 12 Categories of Clause Based Extraction
   Basic Clause -> SV,SVC,SVA,SVO,SVOO,SVOA,SVOC

   Theory Referred from : (http://resources.mpi-inf.mpg.de/d5/clausie/clausie-www13.pdf)
"""

import spacy as sp
from spacy.symbols import nsubj,acomp,advcl,advmod,agent,amod,appos,attr,aux,auxpass,cc,ccomp,complm
from spacy.symbols import conj,cop,csubj,csubjpass,dep,det,dobj,expl,hmod,hyph,infmod,intj,iobj,mark,meta,neg
from spacy.symbols import nmod,nn,npadvmod,nsubjpass,num,number,oprd,obj,obl,parataxis,partmod,pcomp,pobj,poss 
from spacy.symbols import possessive,preconj,prep,prt,punct,quantmod,rcmod,root,xcomp,acl,LAW,VERB

class bcolors:
	GREEN = '\033[92m'
	HEAD = '\033[95m'
	BLUE = '\033[94m'
	ENDC = '\033[0m'

#import the english language
nlp = sp.load('en')

#write to the file
def write_to_output_file(subj,relation,objects):
	with open("output.txt","a") as fp:
		fp.write("{},{},{}".format(subj,relation,objects))
		fp.write("\n") #new line

#Dependency Tree
def generate_dependency_tree(doc):
	dp = []
	for token in doc:
		dp.append((token.text,
			bcolors.GREEN+token.dep_+bcolors.ENDC,
			token.head.text,
			bcolors.HEAD+token.head.pos_+bcolors.ENDC,
			[child for child in token.children]))

	return dp

def generate_chunked_subjects(doc):
	chunked_nouns = [] 
	#We need to do Noun chunks
	for chunk in doc.noun_chunks:
		chunked_nouns.append((chunk.text,
			  chunk.root.text,
			  chunk.root.dep_,
			  chunk.root.head.text))

	return chunked_nouns

def check_if_any_subtrees_present(token):
	bool = False
	subjects = list(token.lefts)
	objects = list(token.rights)
	if len(subjects)==0 and len(objects) == 0:
		bool = True
	
	return bool

def e1_r_sentence(root,subjects):
	per_s_r = [[],[]]
	for left_side in subjects:
			if(check_if_any_subtrees_present(left_side)):
				if left_side.dep == nsubj or left_side.dep == mark:
					per_s_r[0].append(left_side)
				#helping words
				if left_side.dep == aux or left_side.dep == neg:
					per_s_r[1].append(left_side)

	#append root
	per_s_r[1].append(root)

	#return the subject and relation
	return per_s_r

def generate_the_sentence(doc,root,init_track,call_from):
	#generated_sentece
	subj_rel = None
	generated_sentence = [[],[],[]]
	#call_from
	call_from = 0
	i=1
	#check variable to generate a new sentence
	check_variable = None
	#check left and right
	#nsubj is present in left
	subjects = list(root.lefts) #words that appears to left
	objects = list(root.rights)#words that appears to right
	n_subjects = len(subjects) #length of the subjects
	n_objects = len(objects) #length of the objects


	if n_subjects == 1 and n_objects == 1:
		sub = subjects[0] #type <class Spacy.tokens.token.Token>
		obj = objects[0]
		for descendant in sub.subtree:
			assert sub is descendant or sub.is_ancestor(descendant)
			generated_sentence[0].append(descendant.text)

		#append the root
		generated_sentence[1].append(root)

		for descendant in obj.subtree:
			assert obj is descendant or obj.is_ancestor(descendant)
			generated_sentence[2].append(descendant)
		#write in the output file
		write_to_output_file(generated_sentence[0],generated_sentence[1],generated_sentence[2])

	else:
		if init_track == 1:
			subj_rel = e1_r_sentence(root,subjects)
			init_track += 1 #increment the loop
		#if length of the subtree is not zero
		if n_subjects != 0:
			#LEFT SUBTREE TO TRAVERSE
			#LST for next iterations
			if init_track > 1:
				for left_ST in subjects:
					#if it has nsubj then we can create a new sentence
					if left_ST.dep == nsubj or left_ST.dep == advmod:
						check_variable = 1
						generated_sentence[0].append(left_ST)
					#helping words
					if left_ST.dep == aux or left_ST.dep == neg or left_ST.dep == mark:
						generated_sentence[1].append(left_ST)

		#append root
		generated_sentence[1].append(root)
		#if RST is present
		if n_objects != 0 :
			for right_ST in objects:
				#check if they have subtree
				if(check_if_any_subtrees_present(right_ST)):
					#write the new sentence into a file
					if check_variable == 1:
						#write
						write_to_output_file(generated_sentence[0],generated_sentence[1],[right_ST])
						check_variable = 0  #reinitialize the variable

					generated_sentence[2] = right_ST
					print(generated_sentence)
					#write to the output file
					if call_from != 1:
						write_to_output_file(subj_rel[0],subj_rel[1],[right_ST])
					else:
						write_to_output_file(subj_rel[0],subj_rel[1],generated_sentence)
				else:
					#call the function
					call_from = 1
					generate_the_sentence(doc,right_ST,init_track,call_from)



if __name__ == '__main__':
	#raw document
	doc = nlp(u'So I am not asking you to decide anything right now because\
				 I just called to give you some information so that anytime may be now or\
				  in the near future if you plan to expand your business or do some renovations or \
				  purchase any equipment or get another store or anything like that you can contact us at that time okay')
	#DP
	dependency_tree = generate_dependency_tree(doc)
	#Chunked nouns
	chunked_nouns = generate_chunked_subjects(doc)
	#start iterating through tree to generate Clause Sentences
	#find the root
	root = [token for token in doc if token.head == token][0] #length of the root is always one
	#initial_track the variable
	init_track = 1
	#call from
	call_from = None
	#generate the sentence
	generate_the_sentence(doc,root,init_track,call_from)

