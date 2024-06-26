# MCON

This repo contains the specification for the Monte Carlo Object Notation (MCON) format.
MCON is intended to be an inter-operable file format for saving MCMC samples and associated meta-data.
It is based on JSON Lines (https://jsonlines.org).

MCON and attempts to overcome limitations of formats like CSV or TSV that have a fixed number of columns.  In MCON:
* values can be arrays, dictionaries, or other structured objects
* the number and structure of fields is not fixed over time.

MCON is also designed to allow conversion to and from CSV or TSV.
Fields that do not have a fixed structure are dropped in the conversion to CSV or TSV.

# Specification

See the [full specification](https://github.com/bredelings/MCON/blob/main/mcon.rst).

# Examples

## File
``` Non-nested
{"fields": ["iter"], "nested": false, "format": "MCON", "version": "0.1"}
{"iter": 10, "x": [1.1, 2.2, 3.3], "pi": {"A":0.3, "T":0.7}, "y": [1,2]}
{"iter": 20, "x": [1.2, 2.3, 3.1], "pi": {"A":0.4, "T":0.6}, "y": [3]}
```


## Conversions
``` sh
./mcon-tool examples/E1.json -O tsv               # MCON -> TSV (short names)
./mcon-tool examples/E1.tsv                       # TSV -> MCON
./mcon-tool examples/E1.tsv | ./mcon-tool -O tsv  # TSV -> MCON -> TSV
./mcon-tool examples/E3.json -O tsv               # Drops y as having variable structure.
./mcon-tool examples/E5.json -O tsv               # Drops y, pi, and z[2] as varying.
```

## Transformations

Transformations to flatten names and values:

``` sh
./mcon-tool examples/E1.json --unnest
./mcon-tool examples/E1.json --atomize
./mcon-tool examples/E1.json --unnest --atomize
./mcon-tool examples/E1.json --unnest --atomize -O tsv  # MCON -> TSV (long names)
```
