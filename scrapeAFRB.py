# scrapeAFRB.py

import urllib, urllib2, json
import string
import os, sys, argparse
from datetime import date
import fileDownloader

head = {"Host":"www.frbatlanta.org",
		"User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.20 Safari/537.36",
		"Referer":"http://www.frbatlanta.org/banking/reporting/fry6/" }
reqUrl = 'http://www.frbatlanta.org/banking/reporting/fry6/reader.cfm'
docUrlPrefix = 'https://www.frbatlanta.org/banking/reporting/fry6/docs/'
masterFile = 'masterlist.txt'
logFile = 'scrapelog_' + str(date.today()) + '.txt'


def get_args():
	parser = argparse.ArgumentParser(description='Hello, world')

	parser.add_argument('-o',default=os.getcwd(), 
						#metavar='output path (absolute)',
						dest='workDir',
						help='Sets a custom output directory.\n\
							An asbolute path is required.\n')
	parser.add_argument('--max',default=None,
						#metavar='maximum file downloads',
						dest='maxFiles',
						type=int,
						help='Limits the number of files downloaded \
						during the session.\n')

	parser.add_argument('-v',#default=False,
						#metavar='verbose mode',
						dest='verbose',
						action='store_true',
						#type=bool,
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
	# RSSDs = [ int(item[1]) for item in jData['DATA'] ]
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
	# reconstruct output path string
	pathStr = os.path.join(*pathList)

	# open files
	masterOut = open(os.path.join(pathStr,masterFile), 'a')
	logPath = os.path.join(pathStr,'logs')
	# make logs directory, if it does not exist
	if not os.path.exists(logPath):
		os.makedirs(logPath)
	logOut = open(os.path.join(logPath,logFile), 'w')
	
	docPath = os.path.join(pathStr, 'docs')
	if not os.path.exists(docPath):
		os.makedirs(docPath)

	# when maxFiles is None, update value to full length of data list
	if maxFiles == None:
		maxFiles = len(data)
	
	# write to files
	for i in range(maxFiles):
		masterOut.write('\n' + data[i])
		logOut.write('\n' + data[i])
		if verbose:
			print '# %d/%d' % (i+1, maxFiles),
		download_one(data[i], docPath, verbose)
		# do download
	#if confirm[0].upper() == 'Y':
	#	download_files(data, dir)

	# close files
	masterOut.close()
	logOut.close()
	if verbose:
		print "%d total files downloaded to %s" % (maxFiles, docPath)

def download_one(file, docPath, verbose):
	thisUrl = docUrlPrefix + '/' + urllib.quote(file)
	thisFile = os.path.join(docPath, file)
	downloader = fileDownloader.DownloadFile(thisUrl, thisFile)
	if verbose:
		print 'Downloading: %s ...' % (file),
	downloader.download()
	print "Done."

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

def main():
	workDir, maxFiles, verbose = get_args()
	#workDir = os.getcwd() + '\\sjh\\frbatlanta\\'
	#workDir = 'C:\\Python27\\sjh\\frbatlanta\\'

	years = get_years()
	data = get_all_data(years)
	
	# list of new FILENAME values
	newData = get_changes(data, workDir)
	# update master list, write logs, download files
	output_data(newData, workDir, maxFiles, verbose)

if __name__ == '__main__':
	main()