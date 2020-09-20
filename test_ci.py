from pymongo import MongoClient
import pandas as pd
from time import time
import os
from datetime import datetime
import sys

from alphapept.runner import run_alphapept
from alphapept.settings import load_settings



def main():
	print(sys.argv)
	
	password = sys.argv[1]
	settings_path = sys.argv[2]
	commit = sys.argv[3]
	branch = sys.argv[4]

	settings = load_settings(settings_path)

	start = time()
	settings = run_alphapept(settings)
	end = time()

	report = {}

	report['timestamp'] = datetime.now()
	report['settings'] = settings

	report['time_elapsed_min'] = (end-start)/60

	report['branch'] = branch
	report['commit'] = commit

	#File Sizes:
	report['file_sizes'] = {}
	report['file_sizes']['database'] = os.path.getsize(settings['fasta']['database_path'])/1024**2

	file_sizes = {}
	for _ in settings['experiment']['file_paths']:

		base, ext = os.path.splitext(_)
		file_sizes[base+"_ms_data"] = os.path.getsize(os.path.splitext(_)[0] + ".ms_data.hdf")/1024**2
		file_sizes[base+"_result"] = os.path.getsize(os.path.splitext(_)[0] + ".hdf")/1024**2

	report['file_sizes']['files'] = file_sizes
	report['file_sizes']['results'] = os.path.getsize(settings['experiment']['results_path'])/1024**2
	summary = pd.read_hdf('C:/testfolder/results.hdf','protein_table').describe()
	summary.columns = [_.replace('.','_') for _ in summary.columns.tolist()]
	summary = summary.to_dict()
	report['results'] = summary

	print('Uploading to DB')
	string = f"mongodb+srv://github_actions:{password}@ci.yue0n.mongodb.net/"
	client = MongoClient(string)

	post_id = client['github']['performance_runs'].insert_one(report).inserted_id

	print(f"Uploaded {post_id}.")

if __name__ == "__main__":
   main()
