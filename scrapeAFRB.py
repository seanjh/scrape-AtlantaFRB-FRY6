# scrapeAFRB.py

import urllib, urllib2, json
import string
import os, sys
from datetime import date
from fileDownloader import DownloadFile
import argparse

def main():
	parser = argparse.ArgumentParser(description="Scrapes FR Y-6 files from www.frbatlanta.org/banking/reporting/fry6/docs/")
	parser.add_argument()
	args = parser.parse_args()

	years = get_years()
	data = get_all_data(years)

	#workDir = os.getcwd() + '\\sjh\\frbatlanta\\'
	workDir = 'C:\\Python27\\sjh\\frbatlanta\\'
	
	# list of new FILENAME values
	newData = get_changes(data, workDir)
	# update master list, write logs, download files
	output_data(newData, workDir)

if __name__ == '__main__':
	main()