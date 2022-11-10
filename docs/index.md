# Overview

## Introduction to the JSON Schema standard 

JSON Schema is a way of validating that a JSON structure has a particular form. 

This project is a JSON Schema validator.  Given a schema and a structure, it validates that the structure conforms to the contraints of the schema.

The JSON Schema specification has several versions:

 * Draft-04
 * Draft-06
 * Draft-07
 * Draft-2019-09
 * Draft-2020-12
 * Maybe more since the writing of this document.

## Alternatives

There are other python libraries that do JSON Schema validation.  This project aims to be slightly different from alternatives in these aspects:

 * More memory efficient (perhaps at the expense of speed).
 * Minimize external dependencies.

## Open Source

The project is open source MIT licensed.  Contributions can be made through the [GitHub site](https://github.com/pearmaster/jacobs-json-schema). 