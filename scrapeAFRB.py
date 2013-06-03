''' scrapeAFRB.py
	by Sean Herman
	download_one inspired by PabloG @ http://stackoverflow.com/revisions/22776/3
'''

import urllib, urllib2, json
import string
import os, sys, argparse
from datetime import date
from time import sleep
#import fileDownloader

head = {"Host":"www.frbatlanta.org",
		"User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.20 Safari/537.36",
		"Referer":"http://www.frbatlanta.org/banking/reporting/fry6/" }
reqUrl = 'http://www.frbatlanta.org/banking/reporting/fry6/reader.cfm'
docUrlPrefix = 'https://www.frbatlanta.org/banking/reporting/fry6/docs/'
masterFile = 'masterlist.txt'
logFile = 'scrapelog_' + str(date.today()) + '.txt'
defaultDir = os.path.join(os.path.expanduser('~'),'Downloads','scrapeAFRB')
errorFile = 'errorlog_' + str(date.today()) + '.txt'

def get_args():
	parser = argparse.ArgumentParser(description='Specializedfrbatlanta.org FR Y-6 document scraper')

	parser.add_argument('-o',default=defaultDir,
						dest='workDir',
						help='Sets a custom output directory. An asbolute path is required.\n\
							 Default output path is \'atlantaFRB\', below user\'s home directory.\n')
	parser.add_argument('--max',default=None,
						dest='maxFiles',
						type=int,
						help='Limits the number of files downloaded \
						during the session.\n')

	parser.add_argument('-v',
						dest='verbose',
						action='store_true',
						help='Enables verbose mode. With verbose enabled, each \n\
							file downloaded will be displayed in the console.\n')

	pathStr = vars(parser.parse_args())['workDir']
	pathList = deconstruct_path(pathStr)
	maxFiles = vars(parser.parse_args())['maxFiles']
	verbose = vars(parser.parse_args())['verbose']
	
	return pathList, maxFiles, verbose

def get_response(req):
	# response is JSON
	resp = urllib2.urlopen(req)
	tempJson = resp.read()
	cleanJson = clean_response(tempJson)
	jData = json.loads(cleanJson)
	return jData

def get_years():
	# URL pulled from header GET request sent by browser visiting http://www.frbatlanta.org/banking/reporting/fry6/
	# This GET request provides a list of years
	url = reqUrl + '?{%22reader%22:%22getYearList%22}'
	
	# build the years request
	req = urllib2.Request(url, headers=head)
	# Response provides a list of Year unicode string values. Unpack these as normal strings.
	years = [ str(y) for y in get_response(req) ]
	return years

def clean_response(thisStr):
	thisStr = thisStr.replace('\r','')
	thisStr = thisStr.replace('\n','')
	thisStr = thisStr.replace('\t','')
	thisStr = thisStr.strip()
	return thisStr

def get_all_data(yList):
	d = {}
	# add a new year key for each year retrieved
	for year in yList:
		d[year] = get_data(year)
	return d

def unpack_year_data(jData):
	yearData = []
	# builds new list of dictionaries
	# each list item pairs the appropriate COLUMNS heading with its DATA
	for datum in jData['DATA']:
			yearData.append( { jData['COLUMNS'][i]:datum[i] for i in range(len(datum)) } )
	return yearData

def get_data(y):
	# URL pulled from GET request header sent by browser visting http://www.frbatlanta.org/banking/reporting/fry6/
	# This GET request provides a list of results for a given input docyear (embedded in the URL)
	url = reqUrl + '?{%22reader%22:%22getDocs%22,%22dataStruct%22:{%22docyear%22:%22'+str(y)+'%22}}'
	
	# build the data request
	req = urllib2.Request(url, headers=head)
	jData = get_response(req)
	data = unpack_year_data(jData)
	return data

def get_old_data(pathList):
	# open current master list (if available)
	filename = os.path.join(os.path.join(*pathList), masterFile)
	if not os.path.exists(filename):
		outfile = open(filename, 'w')
		outfile.close()
	infile = open(filename, 'r' )
	oldFiles = []
	for line in infile:
		oldFiles.append(line.rstrip())
	infile.close()
	return oldFiles

def get_changes(data, pathList):
	# pull filenames from masterlist
	oldFiles = get_old_data(pathList)
	# pull filenames from scraped data
	newData = [ results['FILENAME'] for year in data.keys() for results in data[year] ]

	# compare oldFiles and newData filenames
	# create an empty list to collect filenames that are not common to both lists
	newFiles = [ filename for filename in newData if not filename in oldFiles ]
	return newFiles

def output_data(data, pathList, maxFiles, verbose):
	# reconstruct output path strings
	pathStr = os.path.join(*pathList)
	logPath = os.path.join(pathStr,'logs')
	docPath = os.path.join(pathStr, 'docs')

	# open files
	masterOut = open(os.path.join(pathStr,masterFile), 'a')
	logOut = open(os.path.join(logPath,logFile), 'w')
	errorOut = open(os.path.join(logPath,errorFile), 'w')

	# when maxFiles is None, update value to full length of data list
	if maxFiles == None:
		maxFiles = len(data)
	
	# write to files
	for i in range(maxFiles):
		#if verbose:
			#print ' %d/%d' % (i+1, maxFiles),
			#sys.stdout.write('%d/%d' % (i+1,maxFiles)),
		download_one(data[i], docPath, verbose, masterOut, logOut, errorOut)

	# close files
	masterOut.close()
	logOut.close()
	errorOut.close()
	# fin.

def download_one(file, docPath, verbose, masterOut, logOut, errorOut):
	# compose full url and file path
	thisUrl = docUrlPrefix + urllib.quote(file)
	thisFile = os.path.join(docPath, file)

	# open download file, prepare download handlers
	downFile = open(thisFile, 'wb')
	block, fileSize = 8192, 0 # 8KB blocks

	try:
		u = urllib2.urlopen(thisUrl)
		metadata = u.info()
		urlSize = int(metadata['content-length'])
		while True:
			dataBuffer = u.read(block)
			if not dataBuffer:
				break
			downFile.write(dataBuffer)
			fileSize = fileSize + len(dataBuffer)
			if verbose:
				sys.stdout.write('\r %s: %d/%d KB (%0.0f%%) ... ' % (file, fileSize, urlSize, fileSize * 100. / urlSize) ),
		u.close()
		sys.stdout.write('Done\n')
		masterOut.write('\n' + file)
		logOut.write('\n' + file)
	except:
			if verbose:
				sys.stdout.write('Download failed!\n')
			errorOut.write('\n' + file)
	downFile.close()

	

def deconstruct_path(pathStr):
	'''Transforms a path string into a list of directory strings, in order.
		Index 0 includes root/mount (e.g., 'C:\\' or '/') '''
	pathList = []
	head, tail = os.path.split(pathStr)
	while not os.path.ismount(head):
		pathList.append(tail)
		head, tail = os.path.split(head)
	pathList.append(tail)
	pathList.append(head)
	pathList.reverse()
	return pathList

def check_path(pathList):
	# check required paths
	basePath = os.path.join(*pathList)
	docPath = os.path.join(basePath, 'docs')
	logPath = os.path.join(basePath, 'logs')
	if not os.path.exists(basePath):
		os.makedirs(basePath)
	if not os.path.exists(docPath):
		os.makedirs(docPath)
	if not os.path.exists(logPath):
		os.makedirs(logPath)

def main():
	# parse arguments from command line
	workDir, maxFiles, verbose = get_args()

	# check for required directories below workDir
	check_path(workDir)

	# scrape data from frbatlanta.org
	years = get_years()
	data = get_all_data(years)
	
	# list of new FILENAME values from scrape
	newData = get_changes(data, workDir)
	# update master list, write logs, download files
	output_data(newData, workDir, maxFiles, verbose)

if __name__ == '__main__':
	main()