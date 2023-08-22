#!/usr/bin/env python3

import sys
import argparse
import json
import csv

parser = argparse.ArgumentParser(description="Convert MCON files")
parser.add_argument("filename",nargs='?', default=None,help="file to convert")
parser.add_argument("--unnest",help="convert nested MCON -> non-nested MCON")
parser.add_argument("--nest",help="convert non-nested MCON -> nested MCON")
parser.add_argument("--output",help="output format")
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
    return keys

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

    def get_keys(self):
        if self.nested:
            return get_keys_nested(self.samples[0])
        else:
            return get_keys_non_nested(self.samples[0])
            
    def dump_TSV(self,**kwargs):
        writer = csv.writer(kwargs["file"], delimiter='\t', quoting=csv.QUOTE_NONE)

        fields = []
        if self.fields is not None:
            fields = self.fields
        fields1=set(self.fields)
        all_fields = self.get_keys()

        for field in all_fields:
            if field not in fields1:
                fields.append(field)

        nfields = len(fields)
        writer.writerow(fields)
                
        for sample in self.samples:
            row = []
            for i in range(nfields):
                row.append(json.dumps(sample[fields[i]]))
            writer.writerow(row)

def detect_format(infile, filename):
    firstline = infile.readline().rstrip()
    # this shouldn't have any chars that need to be escaped in TSV.
    # assert( ??? )

    
    # want unquoted TSV.  Therefore, we can just read the first line 
    try:
        header = json.loads(fileLine)
        if "format" in header and header["format"] == "MCON" and "version" in header:
            return ("MCON", firstline)
        else:
            # If this is JSON, then its not TSV
            return None
    except:
        return ("TSV", firstline)
    
def read_MCON(firstline,infile):
    header = json.loads(firstline)
    samples = []
    for line in infile:
        samples.append(json.loads(line))
    return LogFile(header, samples)

def read_TSV(firstline, infile):
    tsv_fields = firstline.split('\t')
    nfields = len(tsv_fields)

    header = dict()
    header["format"] = "MCON"
    header["version"] = "0.1"
    header["fields"] = tsv_fields
    header["nested"] = False

    reader = csv.reader(infile, delimiter="\t", quotechar='"')

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

def read_logfile(infile,filename):
    format, firstline  = detect_format(infile, filename)
    if format == "MCON":
        return read_MCON(firstline, infile)
    elif format == "TSV":
        return read_TSV(firstline, infile)
    elif format is None:
        print(f"Unknown format for file '{filename}'")
    else:
        print(f"Unknown format {format} for file '{filename}'")
    exit(1)
    
infile = sys.stdin
if args.filename is not None:
    infile = open(args.filename)

logfile = read_logfile(infile, args.filename)
if args.output == "tsv":
    logfile.dump_TSV(file=sys.stdout)
else:
    logfile.dump_MCON(file=sys.stdout)
