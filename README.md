# MCON

This repo contains the specification for the Monte Carlo Object Notation (MCON) format.

It is based on JSON Lines (https://jsonlines.org) and attempts to overcome limitations of table-based formats such as CSV and TSV:
* values can be arrays, dictionaries, or other structured objects
* the number of structure of fields is not fixed over time.

It is also designed to allow conversion to and from CSV/TSV, when the
number and structure of fields is constant.

# Examples

## Conversions
``` sh
./mcon-tool examples/E1.json -O tsv               # MCON -> TSV (short names)
./mcon-tool examples/E1.tsv                       # TSV -> MCON
./mcon-tool examples/E1.tsv | ./mcon-tool -O tsv  # TSV -> MCON -> TSV
```

## Transformations

``` sh
./mcon-tool examples/E1.json --unnest
./mcon-tool examples/E1.json --atomize
./mcon-tool examples/E1.json --unnest --atomize
./mcon-tool examples/E1.json --unnest --atomize -O tsv  # MCON -> TSV (long names)
```

