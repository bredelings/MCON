#!/usr/bin/env python3

import sys
import argparse
import json
import csv

parser = argparse.ArgumentParser(description="Convert MCON files")
parser.add_argument("filename",help="file to convert")
parser.add_argument("--unnest",help="convert nested MCON -> non-nested MCON")
parser.add_argument("--nest",help="convert non-nested MCON -> nested MCON")
args = parser.parse_args()

def is_nested_key(key):
    assert(isinstance(key,str))
    if len(key) > 0 and key.endswith('/'):
        return True
    else:
        return False

def get_keys_non_nested(sample):
    keys = set()
    for key in sample:
        keys.add(key)
    return keys

def get_keys_nested(sample):
    keys = set()
    for key in sample:
        if is_nested_key(key):
            keys2 = get_keys_nested(sample[key])
            for key2 in keys2:
                keys.add(key + key2)
        else:
            keys.add(key)    

class LogFile(object):
    def __init__(self, header, samples):
        self.fields = header.get("fields",None)
        self.nested = header.get("nested",True)
        self.atomic = header.get("atomic",False)
        self.samples = samples

    def is_nested(self):
        return self.nested

    def is_atomic(self):
        return self.atomic

    def dump_MCON(self,**kwargs):
        header = dict()
        if self.fields is not None:
            header["fields"] = self.fields
        header["format"] = "MCON"
        header["version"] = "0.1"
        header["nested"] = self.nested
        print(json.dumps(header),**kwargs)
        for sample in self.samples:
            print(json.dumps(sample),**kwargs)

    def dump_TSV(self,**kwargs):
        fields = []
        if self.fields is not None:
            fields = self.fields


        
        


def detect_format(filename):
    try:
        with open(filename) as infile:
            fileLine = infile.readline().rstrip()
            header = json.loads(fileLine)
            if "format" in header and header["format"] == "MCON" and "version" in header:
                return "MCON"
            else:
                # If this is JSON, then its not TSV
                return None
    except:
        pass

    try:
        with open(args.filename) as infile:
            reader = csv.reader(infile, delimiter="\t", quotechar='"')
            headers = next(reader, None)
            return "TSV"
    except:
        return None
    
def read_MCON(filename):
    with open(filename) as infile:
        fileLine = infile.readline().rstrip()
        header = json.loads(fileLine)
        samples = []
        for line in infile:
            samples.append(json.loads(line))
        return LogFile(header, samples)

def read_TSV(filename):
    with open(args.filename) as infile:
        reader = csv.reader(infile, delimiter="\t", quotechar='"')
        tsv_fields = next(reader,None)
        nfields = len(tsv_fields)

        header = dict()
        header["format"] = "MCON"
        header["version"] = "0.1"
        header["fields"] = tsv_fields
        header["nested"] = False
    
        samples = []
        ignored_lines = 0;
        for tsv_line in reader:
            if len(tsv_line) != nfields:
                print(f"TSV line {1+len(samples)} has {len(tsv_line)} fields, but header has {nfields} fields.", file=sys.stderr)
                ignored_lines += 1
                break
            j = dict()
            for i in range(nfields):
                j[tsv_fields[i]] = json.loads(tsv_line[i])
            samples.append(j)

        for tsv_line in reader:
            ignored_lines += 1

        if ignored_lines > 0:
            print(f"Skipping the next {ignored_lines} lines.", file=sys.stderr)
        
        print(f"Read {len(samples)} samples of TSV with {len(header)} fields.", file=sys.stderr)
        return LogFile(header, samples)

def read_logfile(filename):
    format = detect_format(args.filename)
    if format == "MCON":
        return read_MCON(filename)
    elif format == "TSV":
        return read_TSV(filename)
    elif format is None:
        print(f"Unknown format for file '{filename}'")
    else:
        print(f"Unknown format {format} for file '{filename}'")
    exit(1)
        
    
logfile = read_logfile(args.filename)
logfile.dump_MCON()
