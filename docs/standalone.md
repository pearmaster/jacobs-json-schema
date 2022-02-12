# Standalone Mode

## Dependencies

In standalone mode, there aren't any dependencies.  Everything is implemented in pure Python3.

It requires Python 3.5 or later.

## Conformance

Standalone mode doesn't _fully_ conform with any of the JSON Schema drafts.  It fails conformance with schemas that use `$id` and has some conformance issues with complicated `$ref` usage.  

With those exceptions, standalone mode implements: Draft-04, Draft-06, and Draft-07 versions of the JSON Schema specification.

## Usage

## Examples