Monte-Carlo Object Notation (MCON)
==================================

Introduction
------------

Monte-Carlo Object Notation (MCON) is a file format for recording samples from Monte-Carlo algorithms.
The format accomodates multiple different algorithms, including Markov chain Monte Carlo (MCMC), Sequential Monte Carlo (SMC), etc.
Each line is a JSON object, following the `JSON Lines <https://jsonlines.org>`_ format.
The first line is called the "header line".
All other lines are called "sample lines".
Each sample line represents a Monte Carlo sample as a collection of (key,value) pairs.

Many software programs record Monte Carlo samples using a *table-based* file format such as CSV or TSV.
Each column represents a random variable and each row represents a Monte Carlo sample.
Usually the first line of the file gives the name for each random variable.
Such formats require that the number of variables remains constant.
They also usually require that the value for each variable is a single number.

The MCON format is designed to circumvent limitations of table-based formats by

1. enabling fields to have *structured values*, such as arrays.
2. enabling the number and structure of fields to *change over time*.

Example::

  {"fields": ["iter","x"], nested: false, version: 0.1}
  {"iter": 10, "x": [1.1, 2.2, 3.3], "pi": {"A":0.3, "T":0.7}, "y": [1,2]}
  {"iter": 20, "x": [1.2, 2.3, 3.1]}, "pi": {A":0.4, "T":0.6}}, "y": [3]

However, it is sometimes important to be able to convert this more flexible format back to a format like CSV or TSV.
The MCON format thus specifies a method of doing so.
For example, the above MCON file would be translated to

Example::

  iter,x[1],x[2],x[3],pi[A],pi[T]
  10,1.1,2.2,3.3,0.3,0.7
  20,1.2,2.3,3.1,0.4,0.6

Such a conversion drops fields (e.g. "y" above) whose structure is not fixed.

Header
------
The header line *must* contain the following keys:

- "format": "MCON"
- "version": string

These fields declare that the file conforms to the MCON specification, and which version is conforms to.

The header line *may* contain the following keys:

- "nested": boolean
- "atomic": boolean
- "fields": array of string

Other keys are allowed, but are ignored.

"atomic"
~~~~~~~~
If the value is `true`, then all field values are guaranteed not be to arrays or objects.
This does not change the interpretation of the file -- it just allows the reader of the file
to know that all the values are atomic without looking at later lines.

"nested"
~~~~~~~~
If the value is `true`, the file is treated as Nested MCON.  Otherwise the file is treated as Non-Nested MCON.

"fields"
~~~~~~~~
The "fields" attribute in the header line specifies the order of fields when translated to a table-based format such as CSV or TSV.
Any fields not mentioned in the "fields" attribute occur after all the mentioned fields.
Such fields can occur in any order.

   
Non-Nested
--------
The (key,value) pairs in non-nested JSON object directly represent (field,value) pairs.

Nested
------
In a nested JSON object, only the last character of a key can be "/".
A key that ends with an "/" is *nested*.
Other keys are *non-nested*.
The non-nested keys represent (field,value) pairs directly.

To interpret a nested key ("field/",value), we

1. **translate** its JSON value into a set of (field2,value2) pairs.  The value may also contain nested keys, so this translation is recursive.
2. **replace** each of the sub-field names `field2` with "{field/}{field2}".

Example::
  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"x":20, "y":4.13}}
  corresponds to the non-nested sample line
     {"iter": 10, "S1/x": 10, S1/y": 3.14, "S2/x": 20, "S2/y": 4.13}

Unnesting
-----------
When unnesting fields, each field has a "long name" and a "short name".

The long name applies all prefixes to each variable name.

The short name applies a prefix only when it is necessary to avoid ambiguity.

Example::
  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"z":20, "w":4.13}}
  long names:
     {"iter": 10, "S1/x": 10, S1/y": 3.14, "S2/x": 20, "S2/y": 4.13}
  short names:
     {"iter": 10, "x": 10, y": 3.14, "z": 20, "w": 4.13}

To create the non-nested value with short names, we simply lift the fields from a sub-object into the current object
if no name clashes are introduced by doing so.

The prefix is either removed from all sub-fields are none of them.  So, if we have the sub-objects
"S1/": {"x": 10, "y":20} and "S2/": {"x":30, "z":40}, then we do not lift the fields "S1.y" and S2.z"
(which do not conflict) because the fields S1.x and S2.x do conflict.

Simplification
--------------
To simplify a nested JSON sample J, we

1. Consider each nested (field/,value) pair in J.

   a. replace the value with the simplified value.

2. Consider each nested (field/,value) pair in J.

   a. increment seen["field/"]
   b. consider each (field2,value2) pair inside the value object.

      i. increment seen["field2"]

3. Consider each nested (field/value) pair in J.

   a. consider each (field2,value2) pair inside the value object.
   b. if seen[field2] > 1 for any field2, then we do nothing.
   c. otherwise, we

      i. remove the key "field/" from J.
      ii. add all (field2,value2) pairs to the parent JSON object J.

Example::
  {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"z":20, "w":4.13}}
  becomes
  {"iter": 10, "x": 10, y": 3.14, "z": 20, "w": 4.13}


Atomic values
-------------
It is possible to translate sample lines so that every value is atomic.
This is useful when converting to TSV files, for sample.

To do this that we recursively visit each entry of a structured value, adding "[{key}]" to the end of the field name. For an array, "{key}" is the 1-based index, and for an object the "{key"} is the key.
When we finally come to a value that is atomic, we record the (field,value) pair.

Example::
  "x": [1,4,10]

  is translated to "x[1]": 1, "x[2]": 4, "x[3]": 10


  "pi": {"A":0.1, "C": 0.2, "G": 0.3, "T":0.4}

  is translated to "pi[A]": 0.1, "pi[C]": 0.2, "pi[G]": 0.3, "pi[T]": 0.4

  "y": [[1,2],[3,4]]

  is translated to "y[1][1]": 1, "y[1][2]": 2, "y[2][1]": 3, "y[2][2]": 4


Issue: this could *in theory* create name conflicts, if the object that contained "pi"
also contained an object called "pi[A]".

Conversion to other formats
-----------------

Conversion to TSJ
~~~~~~~~~~~~~~~~~
Since JSON values never contain unescaped tab characters, it is possible to construct TSV files where each value is a JSON value.  We refer to this as tab-separate JSON (TSJ) format.

Issues: how might this interact with TSV escapes?  Presumably we can say that such files should be read with no tsv escapes...

In order to convert an MCON file to TSJ, we need to

1. convert it to non-nested MCON
2. fail if not every sample line contains the same fields
3. determine an order for the fields, taking into account the header line
4. write the field names separated by tabs as a header line
5. for each sample line, write the JSON values separated by tabs in the correct order.

Conversion to TSV
~~~~~~~~~~~~~~~~~

In order to convert an MCON file to TSV, we need to convert it to atomic MCON, and then 

1. convert it to atomic MCON
2. convert it to TSJ

Since every JSON value is atomic, such a file can be read by software that expects atomic values.

However, it can contain strings, booleans, and null in addition to numbers.

Records and data types
----------

In order to represent more complex objects than arrays and objects, we introduce a special notation.

If a field value contains the keys "@$record" and "@$value" then we consider it to represent a record type.
The value for the key "@$value" must be an object, and its keys represent the fields for that object.

Thus if we have::

  "rates": {"@$record": "DiscreteDistribution", "@$value": {"weights": [0.2,0.3,0.5], "values": [0.2, 1.1, 3.4]}}

Then we consider this to represent a record shape "DiscreteDistribution" with fields "weights" and "values".

The purpose of this feature is to indicate the meaning of the values in each Monte Carlo sample so that appropriate summary measures can be computed.
For example, we might have a record type that indicates that the JSON value for "N" describes a population size history through time for a coalescent model.

In order to multiple record shapes to be part of the same data type, we allow an additional key "@$type".
In languages like C++ or Java, the record shape would be considered a type.
However, in languages with algebraic data types (such as Rust), a data type can include multiple record shapes.

