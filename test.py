import os, csv, re, json, random

genres = {}
metadata = {}

#preprocess of metadata
#genre: {'genre_name_i': 'count'}, metadata: {'file_name_i': {lines of metadata with keys}}

with open("harmonixset/dataset/metadata.csv") as file:
	reader = csv.DictReader(file)
	for line in reader:
		genre = line["Genre"]
		genres[genre] = genres.get(genre, 0)+1
		metadata[line["File"]] = line

allowed_genres = set([
	"Pop",
	"Country",
	"Rock"
])

#boolen: True for file with genre in allowed_genres and no 'Ultra Dance' in release
def is_allowed_file(basefile):
	return (metadata[basefile]["Genre"] in allowed_genres) \
		and ("Ultra Dance" not in metadata[basefile]["Release"])

#preprocess of segments
#select files satisfying is_allowed_file to process
#segments: [{"boundary_time_stamp_i": , "label_i": },...]
#all_segments: {"file_name_i": segments_i, ...} if there's label == section, kick off

def get_all_segments():
	all_segments = {}
	fieldnames = ["boundary_time_stamp", "label"]
	dirname = "harmonixset/dataset/segments"
	segment_filenames = os.listdir(dirname)
	for filename in segment_filenames:
		basefile = os.path.splitext(filename)[0]
		if not is_allowed_file(basefile):
			continue
		with open(os.path.join(dirname, filename)) as file:
			reader = csv.DictReader(file, delimiter=" ", fieldnames=fieldnames)
			segments = list(reader)

			'''
			# change 1:
			end_t = segments[-1]["boundary_time_stamp"]
			for i in range(len(segments)-1,-1,-1):
				tmp = segments[i]["boundary_time_stamp"]
				segments[i]["boundary_time_stamp"] = end_t - segments[i]["boundary_time_stamp"]
				end_t = tmp
			'''

			good_segments = True
			for section in segments:
				if section["label"] == "section":
					good_segments = False
			if good_segments:
				all_segments[basefile] = segments
	return all_segments




#get all_segments
#find labels (segment feature) and store them in types
all_segments = get_all_segments()




types = set()
for file, segments in all_segments.items():
	for segment in segments:
		types.add(segment["label"])

merge_segments = {
	"altchorus": "chorus",
	"bigoutro": "outro",
	"bre": "break",
	"breakdown": "solo",
	"build": "transition",
	"chorus_instrumental": "instrumental",
	"chorushalf": "chorus",
	"chorusinst": "instrumental",
	"choruspart": "chorus",
	"drumroll": "instrumental",
	"fadein": "intro",
	"fast": "instrumental",
	"gtr": "solo",
	"gtrbreak": "solo",
	"guitar": "solo",
	"guitarsolo": "solo",
	"inst": "instrumental",
	"instbridge": "instrumental",
	"instchorus": "instrumental",
	"instintro": "intro",
	"instrumentalverse": "instrumental",
	"intchorus": "instrumental",
	"introchorus": "intro",
	"intropt": "intro",
	"introverse": "verse",
	"mainriff": "instrumental",
	"miniverse": "verse",
	"oddriff": "solo",
	"opening": "intro",
	"outroa": "outro",
	"postverse": "verse",
	"preverse": "verse",
	"quietchorus": "chorus",
	"raps": "verse",
	"refrain": "chorus",
	"rhythmlessintro": "intro",
	"saxobeat": "instrumental",
	"section": "unknown",
	"silence": "quiet",
	"slow": "instrumental",
	"slowverse": "verse",
	"stutter": "solo",
	"synth": "instrumental",
	"transitiona": "transition",
	"verse_slow": "verse",
	"versea": "verse",
	"verseinst": "instrumental",
	"versepart": "verse",
	"vocaloutro": "outro",
	"worstthingever": "instrumental"
}

# merge same type labels
def clean(label):
	label = re.sub(r'[0-9]+', '', label)
	label = merge_segments.get(label, label)
	return label
# clean types (segment features)
def get_clean_types():
	return list(set([clean(x) for x in types]))

# print clean types (segment features)
def print_clean_types():
	print(get_clean_types())

# occ: {'type_i': count_type_i, ...}
def print_occurrances():
	occ = {}
	for file, segments in all_segments.items():
		for segment in segments:
			type = clean(segment["label"])
			occ[type] = occ.get(type, 0)+1
	print(occ)

print_clean_types()
print_occurrances()

def get_segments_time_info(): 
	all_segments_timeinfo = {}
	fieldnames = ["start_time", "beat","bar"]
	dirname = "harmonixset/dataset/beats_and_downbeats"
	time_info_filenames = os.listdir(dirname)
	for filename in time_info_filenames:
		basefile = os.path.splitext(filename)[0]
		if not is_allowed_file(basefile):
			continue
		with open(os.path.join(dirname, filename)) as file:
			time_info_lst = []
			for line in file:
				neaten_line = dict(zip(fieldnames,line.split()))
				time_info_lst.append(neaten_line)
			all_segments_timeinfo[basefile] = time_info_lst
	return all_segments_timeinfo

all_segments_timeinfo = get_segments_time_info()

def get_segment_duration(all_segments_timeinfo,all_segments):
	main_timeinfo = {} #{filenamei:timeinfo...}
	
	for filename, segments in all_segments.items():
		
		raw_time_info = all_segments_timeinfo[filename] 
		time_points = [segment["boundary_time_stamp"] for segment in segments]
		labels = [segment["label"] for segment in segments]
		pairs = dict(zip(time_points,labels))

		time_points_info = []
		for e in raw_time_info:
			if e["start_time"] in time_points:
				e["label"] = clean(pairs[e["start_time"]])
				del e["start_time"]
				time_points_info.append(e)
		main_timeinfo[filename] = time_points_info
	# print(main_timeinfo)
	return main_timeinfo

main_timeinfo = get_segment_duration(all_segments_timeinfo,all_segments)
		
'''
		for segment in segments:
			timeinfoblock["start_beatposition"] = all_segments_timeinfo[filename]
		end_t = segments[-1]["boundary_time_stamp"]
		for i in range(len(segments)-1,-1,-1):
			tmp = segments[i]["boundary_time_stamp"]
			segments[i]["boundary_time_stamp"] = end_t - segments[i]["boundary_time_stamp"]
			end_t = tmp

		main_timeinfo[filename] = main_timeinfo.get(filename, timeinfo)'''


def probs_from_prev2_occ():
	probs = {}
	for file, segments in all_segments.items():
		occ = {}
		prevprev = "none"
		prev = "start"
		for segment in segments:
			type = clean(segment["label"]) #type = 'intro' | 'chorus'

			twoprev = prevprev+","+prev #twoprev = 'None,start' | 'start,intro'
			occ[twoprev] = occ.get(twoprev, 0)+1 #occ = {'None,start': 1} | {'None,start': 1, 'start,intro': 1}
			twoprev = twoprev + " " + str(occ[twoprev]) #twoprev = 'None,start 1' | 'start,intro 1'

			probs[twoprev] = probs.get(twoprev, {}) #probs = {'None,start 1':{}} | {'None,start 1':{}, 'start,intro 1':{}}
			probs[twoprev][type] = probs[twoprev].get(type, 0)+1 #probs = {'None,start 1':{'intro':1}} | {'None,start 1':{'intro':1}, 'start,intro 1':{'chorus':1}}

			prevprev = prev #preprev = 'start' | 'intro'
			prev = type #preprev = 'intro' | 'chorus'

	# print(json.dumps(probs))
	

# probs_from_prev2_occ()

# determine next section by looking at how many times the last two sections have occurred
def probs_from_prev2_num_chorus():
	probs = {}
	for file, segments in all_segments.items():
		chorus = 0
		since_chorus = 0
		prevprev = "none"
		prev = "start"
		for segment in segments:
			type = clean(segment["label"]) #type = 'intro' | 'chorus'

			twoprev = prevprev+","+prev #twoprev = 'none,start' | 'start,intro'
			twoprev = twoprev + " " + str(chorus) + "," + str(since_chorus) #twoprev = 'none,start 0,0' | 'start,intro 0,1'

			probs[twoprev] = probs.get(twoprev, {}) #probs = {'none,start 0,0': {}} | {'none,start 0,0': {}, 'start,intro 0,1': {}}
			probs[twoprev][type] = probs[twoprev].get(type, 0)+1 #probs = {'none,start 0,0': {'intro':1}} | {'none,start 0,0': {'intro':1}, 'start,intro 0,1': {'chorus':1}}

			
			if type == "chorus" and prev != "chorus":
				chorus += 1 #chorus = 0 | 1
				since_chorus = 0 #since_chorus = 0 | 0
			else:
				since_chorus += 1 #since_chorus = 1 | 0

			prevprev = prev #prevprev = 'start'
			prev = type #prev = 'intro'

	#print(json.dumps(probs))
	'''with open('new_file_2.json', 'w') as f:
		json.dump(probs, f)'''
	return probs

probs_from_prev2_num_chorus()

def generate_that(seed):
	random.seed(seed)
	probs = probs_from_prev2_num_chorus()

	chorus = 0
	since_chorus = 0
	prevprev = "none"
	prev = "start"
	output = []
	while prev != "end":
		twoprev = prevprev+","+prev
		twoprev = twoprev + " " + str(chorus) + "," + str(since_chorus)

		type = random.choices(list(probs[twoprev].keys()), weights=probs[twoprev].values())[0]

		if type == "chorus" and prev != "chorus":
			chorus += 1
			since_chorus = 0
		else:
			since_chorus += 1

		prevprev = prev
		prev = type

		output.append(type)
	
	return output

# get clean types (segment features)
# get minified types: {'clean_type_0: 'A', ...}
clean_types = get_clean_types()
minified_types = {}
for i in range(len(clean_types)):
	minified_types[clean_types[i]] = chr(ord('A')+i)

# ret: a string of minified types
def minify(types):
	ret = ""
	for type in types:
		ret += minified_types[type]
	return ret

# minified_dataset: {'a string of minified types': 'file_name_i', ...}
minified_dataset = {}
for file, segments in all_segments.items():
	types = []
	for segment in segments:
		types.append(clean(segment["label"]))
	minified_dataset[minify(types)] = file


for i in range(0, 100):
	types = generate_that(i)
	minified = minify(types)
	print(minified_dataset.get(minified, "nope"), minified, types)


# mapping beat info with segments


# count_diff = {}
# pcfirst = 0
# npcfirst = 0
# for file, segments in all_segments.items():
# 	pc = 0
# 	npc = 0
# 	prev = "start"
# 	pcscore = 0
# 	npcscore = 0
# 	for segment in segments:
# 		type = segment["label"]
# 		if type == "chorus" and prev != "chorus":
# 			if prev == "prechorus":
# 				npcscore += npc
# 				pc += 1
# 			elif prev == "verse":
# 				pcscore += pc
# 				npc += 1
# 		prev = type
# 	pcfirst += pcscore
# 	npcfirst += npcscore

# print(pcfirst, npcfirst)