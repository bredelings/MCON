Monte-Carlo Object Notation (MCON)
==================================

Introduction
------------

Monte-Carlo Object Notation (MCON) is a data format for recording samples from Monte-Carlo algorithms.
The format accomodates multiple different algorithms, including Markov chain Monte Carlo (MCMC), Sequential Monte Carlo (SMC), etc.
Each line is a JSON object, following the JSON Lines format.
The first line is called the "header line".
All other lines are called "sample lines".
Each sample line represents a Monte Carlo sample as a collection of (key,value) pairs.

Many Monte Carlo programs record their samples using a table-based format such as CSV or TSV.
Each column represents a random variable. The first line usually give the variable name for each column.
Each row represents the value for each variable in a given Monte Carlo sample.
This format requires that the number of variables remains constant.
Like the MCON format, each line represents a Monte Carlo sample.
It usually also requires that value for each variable have a value that is a single number.

The MCON format is designed to circumvent limitations of table-based formats by
1. allowing fields to have structured values, such as arrays.
2. allowing the number and structure of fields to change over time.
Each sample line specified a number of (field,value) pairs.

Example::

  {"fields": ["iter","x"], nested: false, version: 0.1}
  {"iter": 10, "x": [1.1, 2.2, 3.3], "pi": {"A":0.3, "T":0.7}}
  {"iter": 20, "x": [1.2, 2.3, 3.1]}, "pi": {A":0.4, "T":0.6}}

However, it is sometimes important to be able to convert this more flexible format back to a format like CSV or TSV.
The MCON format thus specifies a method of doing so.
For example, the above MCON file would be translated to

Example::

  iter,x[1],x[2],x[3],pi[A],pi[T]
  10,1.1,2.2,3.3,0.3,0.7
  20,1.2,2.3,3.1,0.4,0.6

Such a translation will only work when each sample line contains the same fields,
and each field has the same structure.

Header
------
The header line can contain the following fields.

1. "version": string
2. "fields": array of string
3. "nested": boolean

The "fields" attribute in the header line specifies the order of fields when translated to a table-based format such as CSV or TSV.
Any fields not mentioned in the fields attribute occur after all the mentioned fields.
The can occur in any order.
   
Unnested
--------
The (key,value) pairs in unnested JSON object represents (field,value) pairs directly.

Nested
------
In a nested JSON object, a key that ends with an unescaped "/" is called a nested key.
Other keys are called unnested keys.
The unnested keys represent (field,value) pairs directly.

To interpret a nested key "field/", we
1. translate its JSON value into a set of (field,value) pairs.  The value may also contain nested keys, so this translation is recursive.
2. we prefix each field name with "field.".

Example::
  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"x":20, "y":4.13}}
  corresponds to the unnested sample line
     {"iter": 10, "S1.x": 10, S1.y": 3.14, "S2.x": 20, "S2.y": 4.13}
  
Issue: currently, we are translating to short names when unnesting.
     
Escape characters
~~~~~~~~~~~~~~~~~
We interpret the backslash "\" as an escape character at the end of the key.
Thus
- "a\/" corresponds to an unnested key "a/"
- "a\\/" corresponds to a nested key "a\/"
- "a\\\/" corresponds to an unnested key "a\/"

However, note that when such a field name is written in a language like python with its own escaping, escape backslashes must be added.
So, in python, one would have to write "a\\/" to represent "a\/";
  
Short names
-----------
When unnesting fields, each field has a "long name" and a "short name".

The long name applies all prefixes to each variable name.

The short name applies a prefix only when it is necessary to avoid ambiguity.

Example::
  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"z":20, "w":4.13}}
  long names:
     {"iter": 10, "S1.x": 10, S1.y": 3.14, "S2.x": 20, "S2.y": 4.13}
  long names:
     {"iter": 10, "x": 10, y": 3.14, "z": 20, "w": 4.13}

To create the unnested value with short names, we simply lift the fields from a sub-object into the current object
if no name clashes are introduced by doing so.

The prefix is either remove from all sub-fields are none of them.  So, if we have the sub-objects
"S1/": {"x": 10, "y":20} and "S2/": {"x":30, "z":40}, then we do not lift the fields "S1.y" and S2.z"
(which do not conflict) because the fields S1.x and S2.x do conflict.


Conversion to TSV
-----------------
It is possible to convert MCON fields to TSV files where each value is an atomic JSON value.

This requires translating array and object values to multiple atomic fields.
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
