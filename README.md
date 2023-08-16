# MCON

This repo contains the specification for the Monte Carlo Object Notation (MCON) format.

It is based on JSON Lines (https://jsonlines.org) and attempts to overcome limitations of table-based formats such as CSV and TSV:
* values can be arrays, dictionaries, or other structured objects
* the number of structure of fields is not fixed over time.

It is also designed to allow conversion to and from CSV/TSV, when the
number and structure of fields is constant.
