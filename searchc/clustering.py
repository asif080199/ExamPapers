import os
path = os.getcwd()+"/searchc/"
import json
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import KMeans
import datetime
from DBManagement.models import *


def buildOnlineCluster(clusterType,dataName,allQuestion):
	key = []
	data = []
	allKey,allVectors = readData(dataName)

	
	# get vector
	for question in allQuestion:
		questionKey = int(question.id[22:])
		key.append(questionKey)	#this id is searchQueryId 
		for i in range(len(allKey)):
			if questionKey == allKey[i]:
				data.append(allVectors[i])
		
	# build cluster
	
	#number cluster
	auto = int(len(allQuestion)/4)
	noCluster = min(15,max(2,auto))	
		
	#build cluster
	clusters =  buildHcluster(key,data,noCluster,dataName)
	
	#format result
	finalResult = []
	i = 0
	for cluster in clusters[0]:
		finalCluster = []
		clusterQuestion = []
		finalCluster.append(i)	# cluster ID 0 
		i+=1
		finalCluster.append(cluster[1])	# cluster name 1
		for questionKey in cluster[0]:	
			clusterQuestion.append(Question.objects.get(id = str(questionKey)))
		finalCluster.append(clusterQuestion)		# cluster question 2
		finalCluster.append(len(clusterQuestion))	# cluster size 3
		finalCluster.append(min(150,(int(float(len(clusterQuestion))/len(allQuestion)*len(clusters[0])*40 +80))))	# cluster font size for display 3
		finalResult.append(finalCluster)
	return finalResult
	
def buildCluster(clusterType,dataName,noCluster):
	key,data = readData(dataName)
	if clusterType == "K":
		clusters,start,end = buildKcluster(key,data,noCluster,dataName)
		writeCluster(clusters,"K",dataName)
		writeLog(clusters,"K",dataName,start,end)
	elif clusterType == "H":
		clusters,start,end = buildHcluster(key,data,noCluster,dataName)
		writeCluster(clusters,"H",dataName)
		writeLog(clusters,"H",dataName,start,end)
	else: print "Invalid cluster type"
	return clusters
	
def buildKcluster(key,data,noCluster,dataName):
	# train cluster
	start = datetime.datetime.now()
	kmeans = KMeans(init='k-means++', n_clusters=noCluster)
	kmeans.fit(data)	
	end = datetime.datetime.now()
	
	# cluster centroid
	centroid = kmeans.cluster_centers_
	
	# cluster name
	featureAll = readFeature(dataName)

	name = nameCluster(centroid,featureAll)
	
	# data label
	label =  kmeans.labels_ 
	
	# pack data [[...data point...],name,centroid]
	clusters = packCluster(key,data,label,name,centroid)
	
	return clusters, start, end
def buildHcluster(key,data,noCluster,dataName):
	# train cluster
	start = datetime.datetime.now()
	ahc = AgglomerativeClustering(n_clusters=noCluster, linkage='ward'). fit(data)
	end = datetime.datetime.now()
	
	featureAll = readFeature(dataName)
	
	# cluster centroid
	centroid = calculateCentroid(ahc,noCluster,featureAll,data)
	
	# cluster name
	name = nameCluster(centroid,featureAll)
	
	# data label
	label =  ahc.labels_ 
	
	# pack data [[...data point...],name,centroid]
	clusters = packCluster(key,data,label,name,centroid)
	
	return clusters, start, end
def readData(name):
	"Input: Data name"
	"Output: Key array and data array"
	key = []
	data = []
	file = open(path+'/data/'+name+'.vector')
	for line in file:
		tem = json.loads(line)
		for item in tem:
			key.append(item[0])
			data.append(item[1:])
	return key,data
def nameCluster(centroid,featureAll):
	name = []
	for c in centroid:
		sname = ""
		m = max(c)
		index = [i for i, j in enumerate(c) if j == m]

		for i in index:
			theName = featureAll[i]
			theName = theName.replace("_"," ").title()+", "	#for nice display
			sname+=theName
			#break 				#only 1 name
		sname = sname[:-2]
		name.append(sname)
	return name
def writeCluster(clusters,type,dataName):
	print "Writing cluster..."
	t = len(clusters)
	with open(path+'/data/'+type+'.'+str(t)+'.'+dataName+'.cluster','w') as outfile:
		json.dump(clusters, outfile)	
	return
def writeLog(clusters,type,dataName,start,end):
	print "Writing log..."
	t = len(clusters)
	log = type + "\t" + str(t)
	log+= "\nDate:\t" + str(start.date())
	log+= "\nTime:\t" + str(end.time())
	log+= "\nDuration:\t" + str(end - start)
	log+= "\n-------------------"
	for cluster in clusters:
		log+= "\n"+str(len(cluster[0]))
		log+= "\t" + cluster[1]
	with open(path+'/log/'+type+'.'+str(t)+'.'+dataName+'.cluster','w') as outfile:
		outfile.write(log)
	return
def readFeature(name):
	file = open(path+'/data/'+name+'.feature')
	for line in file:
		return  (json.loads(line))
def packCluster(key,data,label,name,centroid):
	clusters = []
	for i in range(len(centroid)):
		cluster = []
		member = []
		for j in range(len(data)):
			if label[j] == i:
				member.append(key[j])
		cluster.append(member)
		cluster.append(name[i])
		cluster.append(list(centroid[i]))
		clusters.append(cluster)
	return clusters
def readCluster(name):
	file = open(path+'/data/'+name+'.cluster')
	for line in file:
		return  json.loads(line)
def calculateCentroid(clusters,noCluster,featureAll,data):
	centroid = []
	theClusters= []
	for i in range((noCluster)):
		cluster = []
		for j in range(len(list(clusters.labels_))):
			if list(clusters.labels_)[j] == i:
				cluster.append(data[j])
		theClusters.append(cluster)
	for cluster in theClusters:	
		sumFeature = [0 for feature in featureAll]
		for i in range(len(sumFeature)):
			for item in cluster:
				sumFeature[i] += item[i]
		averageFeature =  [float(sum)/(len(cluster)) for sum in sumFeature]	
		centroid.append(averageFeature)
	return centroid
#buildCluster("H","formula",50)
#buildCluster("K","formula",50)