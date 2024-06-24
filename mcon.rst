==================================
Monte-Carlo Object Notation (MCON)
==================================

.. sectnum::
.. contents:: Table of Contents

Introduction
------------

Monte-Carlo Object Notation (MCON) is an inter-operable file format for recording Monte Carlo samples and associated meta-data.
The format can represent samples from Markov chain Monte Carlo (MCMC), Sequential Monte Carlo (SMC), and other algorithms.
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

  {"fields": ["iter"], "nested": false, "format": "MCON", "version": "0.1"}
  {"iter": 10, "x": [1.1, 2.2, 3.3], "pi": {"A":0.3, "T":0.7}, "y": [1,2]}
  {"iter": 20, "x": [1.2, 2.3, 3.1], "pi": {"A":0.4, "T":0.6}, "y": [3]}

However, it is sometimes important to be able to convert this more flexible format back to a format like CSV or TSV.
The MCON format thus specifies a method of doing so.
For example, the above MCON file would be translated to CSV as::

  iter,x[1],x[2],x[3],pi[A],pi[T]
  10,1.1,2.2,3.3,0.3,0.7
  20,1.2,2.3,3.1,0.4,0.6

Such a conversion drops fields (e.g. "y" above) whose structure is not fixed.

Header line
-----------
The header line *must* contain the following keys:

- "format": "MCON"
- "version": *string*

These fields declare that the file conforms to the MCON specification, and which version is conforms to.

The header line *may* contain the following keys:

- "nested": *boolean*
- "atomic": *boolean*
- "fields": *array* of *string*

Other keys are allowed, but are ignored.

"atomic"
~~~~~~~~
If the value is ``true``, then all field values are guaranteed not be to arrays or objects.
This does not change the interpretation of the file -- it just allows the reader of the file
to know that all the values are atomic before looking at later lines.

"nested"
~~~~~~~~
If the value is ``false``, the file is treated as Non-Nested MCON.  Otherwise the file is treated as Nested MCON.

"fields"
~~~~~~~~
The ``fields`` attribute in the header line specifies the order of fields when translated to a table-based format such as CSV or TSV.
Any fields not mentioned in the "fields" attribute occur after all the mentioned fields.
Such fields can occur in any order.


Non-Nested MCON
---------------
The (key,value) pairs in non-nested JSON object directly represent (field,value) pairs.

Nested MCON
-----------
In a nested JSON object, only the last character of a key can be "/".
A key that ends with an "/" is *nested*.
All other keys are *non-nested*.
The non-nested keys represent (field,value) pairs directly.
The nested keys represent a set of (field,value) pairs.

The value for a nested key *must* be a JSON object.
The set of (field,value) pairs represented by a nested key (k,v) is simply the union of all the (field,value) pairs for ``v`` with ``k`` prepended to the field name.
For example, the (field,value) pairs for ("key1/", {"key2":2, "key3":2}) are given by the set {"key1/key2": 2, "key1/key3": 2}.

Example::

  The nested sample line
     {"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"x":20, "y":4.13}}
  corresponds to the non-nested sample line
     {"iter": 10, "S1/x": 10, S1/y": 3.14, "S2/x": 20, "S2/y": 4.13}

..
  We COULD forbid an object to contain both "key/" and "key".
  That would make "key/" more like a directory in a filesystem path.

Transformations:
----------------
     
Unnesting
~~~~~~~~~~~~~~~~~~~~~~~~~
This transformation only applies to Nested MCON.

1. The header line is modified to replace ``"nested": true`` with ``"nested": false``.
2. Each sample line is replaced with a JSON object containing the union of the (field,value) pairs represented by the keys in the original nested file.


Simplification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This transformation only applies to Nested MCON.

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

Example:

``{"iter": 10, "S1/: {"x": 10, "y": 3.14}, "S2/": {"z":20, "w":4.13}}``
becomes
``{"iter": 10, "x": 10, y": 3.14, "z": 20, "w": 4.13}``

The Simplification procedure also creates a corresponding "short name" for each field:

* ``iter`` ↔ ``iter``
* ``S1/x`` ↔ ``x``
* ``S1/y`` ↔ ``y``
* ``S2/z`` ↔ ``z``
* ``S2/w`` ↔ ``w``

Atomic values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It is possible to translate sample lines so that every value is atomic.
This transformation is useful when converting MCON files to TSV files, for example.
It applies to both nested and non-nested files.

To do this that we recursively visit each entry of a structured value, adding "[{key}]" to the end of the field name. For an array, "{key}" is the 1-based index, and for an object the "{key"} is the key.
When we finally come to a value that is atomic, we record the (field,value) pair.

Examples:

*  ``"x": [1,4,10]`` is translated to ``"x[1]": 1, "x[2]": 4, "x[3]": 10``
*  ``"pi": {"A":0.1, "C": 0.2, "G": 0.3, "T":0.4}`` is translated to ``"pi[A]": 0.1, "pi[C]": 0.2, "pi[G]": 0.3, "pi[T]": 0.4``
*  ``"y": [[1,2],[3,4]]`` is translated to ``"y[1][1]": 1, "y[1][2]": 2, "y[2][1]": 3, "y[2][2]": 4``

Issue: this could *in theory* create name conflicts, if the object that contained "pi"
also contained an object called "pi[A]".

Dropping fields with variable structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The structure of a value is given by the collection of suffixes used when transformation to a set of atomic values.
For example, ``"x": [1,2]`` has the structure ``{"[1]","[2]"}``.
If the structure of a variable is different in different samples, then wish to drop all of its values.

Note that it could be that ``x[1]`` has variable fields, while ``x[2]`` does not.
In such a case, we probably want to drop only ``x[2]``, while marking ``x[1]`` as variable structure.

Conversion to other formats
-----------------

Conversion to TSJ
~~~~~~~~~~~~~~~~~
Since JSON values never contain unescaped tab characters, it is possible to construct TSV files where each value is a JSON value.  We refer to this as tab-separate JSON (TSJ) format.

Issues: how might this interact with TSV escapes?  Presumably we can say that such files should be read with no tsv escapes...

Issues: normally, we simplify first.  But instead of simplifying each line, we would like
to construct a mapping from "long names" to "short names".

In order to convert an MCON file to TSJ, we need to

1. convert it to non-nested MCON
2. drop variable fields
3. fail if not every sample line contains the same fields
4. determine an order for the fields, taking into account the header line
5. write the field names separated by tabs as a header line
6. for each sample line, write the JSON values separated by tabs in the correct order.

Issue: instead of failing, can we drop keys that

1. don't occur in every sample
2. have different structures in different samples?

For example, if we have "x":[1,2] and "x":[3] in different samples, we should drop "x"
altogether, instead of keeping "x[1]".
   
Conversion to TSV
~~~~~~~~~~~~~~~~~

In order to convert an MCON file to TSV, we need to convert it to atomic MCON, and then 

1. Drop fields with variable structure.
2. convert it to atomic MCON
3. convert it to TSJ

Since every JSON value is atomic, such a file can be read by software that expects atomic values.

However, it can contain strings, booleans, and null in addition to numbers.

.. 
  Records and data types
  ----------

  In order to represent more complex objects than arrays and objects, we introduce a special notation.

  If a field value contains the keys ``@$record`` and ``@$value`` then we consider it to represent a record type.
  The value for the key ``@$value`` must be an object, and its keys represent the fields for that object.

  Thus if we have::

    "rates": {"@$record": "DiscreteDistribution",
              "@$value":  {"weights": [0.2, 0.3, 0.5],
                           "values": [0.2, 1.1, 3.4] } }

  Then we consider this to represent a record shape ``DiscreteDistribution`` with fields ``weights`` and ``values``.
  In order to multiple record shapes to be part of the same data type, we allow an additional key ``@$type``.
  In languages like C++ or Java, the record shape would be considered a type.
  However, in languages with algebraic data types (such as Rust), a data type can include multiple record shapes.

  The purpose of this feature is to indicate the meaning of the values in each Monte Carlo sample so that appropriate summary measures can be computed.
  For example, we might have a record type that indicates that the JSON value for "N" describes a population size history through time for a coalescent model.

    

..
  How should we handle translation of MCON files to TSV?
  By default, we want to simplify.
  But I think we want the simplification to simply create a mapping from long names -> short names.
  We don't want to run simplify( ) on each line separately.

  Should we separate translation to TSV from removal of fields that
  (a) are not always present or
  (b) have variable structure?


