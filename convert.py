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
        return (header, samples)

def read_TSV(filename):
    infile = open(args.filename)
    reader = csv.reader(infile, delimiter="\t", quotechar='"')
    headers = next(reader,None)
    return (headers, reader)

format = detect_format(args.filename)

if format == "MCON":
   header, samples = read_MCON(args.filename)
   version = header["version"]
   nested = "non-nested"
   if header["nested"] == True:
       nested = "nested"
   print(f"Read {len(samples)} samples of {nested} MCON version {version} with {len(samples[0])} fields.")

elif format == "TSV":
    header, reader = read_TSV(args.filename)
    inc=0
    for line in reader:
        inc += 1
    print(f"Read {inc} samples of TSV with {len(header)} fields.")

else:
    print("Unknown format!")
    sys.exit(1)

