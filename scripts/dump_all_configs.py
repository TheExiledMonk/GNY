#!/usr/bin/env python3
"""
Dump all config documents from the database for debugging.
Outputs all plugin, pipeline, and system configs as pretty-printed JSON.
All logs go to logs/ folder.
"""
import os
import json
from pymongo import MongoClient

LOGDIR = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(LOGDIR, exist_ok=True)
LOGFILE = os.path.join(LOGDIR, 'dump_all_configs.log')

def log(msg):
    with open(LOGFILE, 'a') as f:
        f.write(msg + '\n')

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB = os.environ.get('MONGO_DB', 'orchestrator')

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def dump_collection(col_name):
    print(f'\n===== {col_name} =====')
    log(f'===== {col_name} =====')
    for doc in db[col_name].find({}):
        doc_str = json.dumps(doc, default=str, indent=2)
        print(doc_str)
        log(doc_str)

def main():
    for col in [
        'plugin_configs',
        'pipeline_configs',
        'system_config',
    ]:
        dump_collection(col)

if __name__ == '__main__':
    main()
