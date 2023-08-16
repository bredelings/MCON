Monte-Carlo Object Notation (MCON)
==================================

Introduction
------------

Monte-Carlo Object Notation (MCON) is a data format for recording samples from Monte-Carlo algorithms.
The format accomodates multiple different algorithms, including Markov chain Monte Carlo (MCMC), Sequential Monte Carlo (SMC), etc.
Each line is a JSON object, following the `JSON Lines <https://jsonlines.org>`_ format.
The first line is called the "header line".
All other lines are called "sample lines".
Each sample line represents a Monte Carlo sample as a collection of (key,value) pairs.

Many Monte Carlo programs record their samples using a *table-based* format such as CSV or TSV.
Each column represents a random variable and each row represents a Monte Carlo sample.
Usually the first line of the file gives the name for each random variable.
This format requires that the number of variables remains constant, and usually also requires that the value for each variable is a single number.

The MCON format is designed to circumvent limitations of table-based formats by enabling

1. fields to have structured values, such as arrays.
2. the number and structure of fields to change over time.

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

Such a translation leaves out fields (e.g. "y") whose structure changes over time.

Header
------
The header line can contain the following keys:

1. "version": string
2. "fields": array of string
3. "nested": boolean

The "fields" attribute in the header line specifies the order of fields when translated to a table-based format such as CSV or TSV.
Any fields not mentioned in the "fields" attribute occur after all the mentioned fields.
The can occur in any order.
   
Unnested
--------
The (key,value) pairs in unnested JSON object directly represent (field,value) pairs.

Nested
------
In a nested JSON object, a key that ends with an unescaped "/" is called a nested key.
Other keys are called unnested keys.
The unnested keys represent (field,value) pairs directly.

To interpret a nested key "field/", we

1. **translate** its JSON value into a set of (field,value) pairs.  The value may also contain nested keys, so this translation is recursive.
2. **replace** each of the sub-field names "name" "{field}/{name}".

Example::
  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"x":20, "y":4.13}}
  corresponds to the unnested sample line
     {"iter": 10, "S1/x": 10, S1/y": 3.14, "S2/x": 20, "S2/y": 4.13}
  
Issue: currently, we are translating to short names when unnesting.
     
Escape characters
~~~~~~~~~~~~~~~~~
We interpret the backslash "\" as an escape character.
The escape character applies only to itself and the "/" character.
It also applies only at the end of a string that ends with "/".

Thus, for a key that ends with "/", we

1. count the number M of preceding escape characters
2. compute the integer N = M/2, rounding down.
3. replace the M escape characters with N escape characters.
4. count the key as nested if M is odd, and as unnested if M is even.

Thus

- "a\/" corresponds to an unnested key "a/"
- "a\\/" corresponds to a nested key "a\/"
- "a\\\/" corresponds to an unnested key "a\/"
- "a\\\\/" corresponds to a nested key "a\\/"

Short names
-----------
When unnesting fields, each field has a "long name" and a "short name".

The long name applies all prefixes to each variable name.

The short name applies a prefix only when it is necessary to avoid ambiguity.

Example::
  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"z":20, "w":4.13}}
  long names:
     {"iter": 10, "S1/x": 10, S1/y": 3.14, "S2/x": 20, "S2/y": 4.13}
  long names:
     {"iter": 10, "x": 10, y": 3.14, "z": 20, "w": 4.13}

To create the unnested value with short names, we simply lift the fields from a sub-object into the current object
if no name clashes are introduced by doing so.

The prefix is either remove from all sub-fields are none of them.  So, if we have the sub-objects
"S1/": {"x": 10, "y":20} and "S2/": {"x":30, "z":40}, then we do not lift the fields "S1.y" and S2.z"
(which do not conflict) because the fields S1.x and S2.x do conflict.

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
1. convert it to unnested MCON 
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

