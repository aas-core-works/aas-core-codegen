# AAS JSON-LD Experiments
<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [AAS JSON-LD Experiments](#aas-json-ld-experiments)
    - [Parsing: jsonld->ttl](#parsing-jsonld-ttl)
        - [Round-tripping: jsonld->ttl->jsonld](#round-tripping-jsonld-ttl-jsonld)
    - [Serialization: ttl->jsonld](#serialization-ttl-jsonld)
        - [Round-tripping: ttl->jsonld->ttl](#round-tripping-ttl-jsonld-ttl)
- [Conclusions](#conclusions)
    - [Next Steps](#next-steps)

<!-- markdown-toc end -->

Task: https://github.com/admin-shell-io/aas-specs/issues/386

I tried to use https://github.com/aas-core-works/aas-core-codegen/blob/main/test_data/jsonld_context/context.jsonld
with some of the examples.
I used tools described here https://github.com/gs1/EPCIS/tree/master/Ontology#conversion-to-jsonld and here https://github.com/gs1/EPCIS/tree/master/Turtle#jsonld-cli
(`jsonld, riot, ttl2jsonld`) each of which has its limitations.

## Parsing: jsonld->ttl

I tried some JSON examples:
- https://github.com/admin-shell-io/aas-specs/blob/master/schemas/json/examples/generated/Entity/maximal.json .
  I dropped this because it starts with `submodels`, which is not defined as top-level element in the context.
- https://github.com/admin-shell-io/aas-specs/blob/master/schemas/json/examples/generated/AssetAdministrationShell/maximal.json: saved as `AssetAdministrationShell.json`

I tried 3 variants of modifying the files:
- Embedded context (pasted `context.jsonld` inside): `AssetAdministrationShell-withContext.jsonld`.
`riot -formatted ttl -syntax jsonld AssetAdministrationShell-withContext.jsonld > AssetAdministrationShell-withContext.ttl`
  - This works, and seems to produce correct info (to be confirmed by round-tripping).
- Network context: `AssetAdministrationShell.jsonld`, with `"@context":"...",` link added on the first line.
Used this command:
`riot -formatted ttl -syntax jsonld AssetAdministrationShell.jsonld`
  - `context.jsonld`: 
Doesn't work because `riot` doesn't take a local file.
`15:07:30 ERROR riot            :: Context URI is not absolute [context.jsonld].`
  - https://github.com/aas-core-works/aas-core-codegen/raw/main/test_data/jsonld_context/context.jsonld (github):
Doesn't work because it doesn't return correct Content-Type
`15:16:18 ERROR riot            :: There was a problem encountered loading a remote context [code=LOADING_REMOTE_CONTEXT_FAILED].`
  - https://rawgit2.com/aas-core-works/aas-core-codegen/main/test_data/jsonld_context/context.jsonld (github hosting site):
We're getting closer, but still doesn't work because the file is missing the `@context` key
`15:17:44 ERROR riot            :: Imported context does not contain @context key and is not valid JSON-LD context.`
  - So I added this key in my branch https://github.com/VladimirAlexiev/aas-core-codegen/raw/main/test_data/jsonld_context/context-fixed.jsonld ,
    and consume it as https://rawgit2.com/VladimirAlexiev/aas-core-codegen/main/test_data/jsonld_context/context-fixed.jsonld .
    - This works, and produces the same result as `AssetAdministrationShell-withContext.ttl`
    - With a minimal difference: two types are rendered with full URLs (eg `<https://admin-shell.io/aas/3/0/AssetAdministrationShell>`) instead of with the prefix `aas:`
    - I'd put this on an implementation quirk in jena riot.
  - I also tried with another tool (`jsonld` is the same that powers the JSONLD Playground), and the results are the same:
  `jsonld format -q AssetAdministrationShell.jsonld | riot -syntax nt -formatted ttl > AssetAdministrationShell-jsonld.ttl`
- Externally-specified local context: `AssetAdministrationShell.json` (original), with a command-line option.
  - Neither `riot` nor `ttl2json` have such option so I cannot convert to ttl

### Round-tripping: jsonld->ttl->jsonld

Let's try round-tripping.

- `riot` produces a bunch of blank node IDs that the other tools won't be able to eliminate.
AAS uses *tons* of blank nodes, but never **shares** them.
```
# riot --formatted jsonld AssetAdministrationShell.ttl
{
    "@graph": [
        {
            "@id": "_:b0",
            "https://admin-shell.io/aas/3/0/AbstractLangString/text": "something_1e73716d",
            "https://admin-shell.io/aas/3/0/AbstractLangString/language": "de-CH"
```
- `ttl2jsonld` doesn't make blank nodes, but cannot use a context, so it emits full URLs rather than JSON keys:
```
# ttl2jsonld AssetAdministrationShell.ttl
{
  "https://admin-shell.io/aas/3/0/Environment/assetAdministrationShells": {
    "@type": "https://admin-shell.io/aas/3/0/AssetAdministrationShell",
    "https://admin-shell.io/aas/3/0/AssetAdministrationShell/assetInformation": {
```

- `jsonld` cannot read turtle files.

So I used two tools in combination:
```
ttl2jsonld AssetAdministrationShell.ttl | jsonld compact -c https://rawgit2.com/VladimirAlexiev/aas-core-codegen/main/test_data/jsonld_context/context-fixed.jsonld > AssetAdministrationShell-ttl2jsonld.jsonld
```

To check the round-tripping, I used `jq` to pretty-print and sort JSON keys:
```
jq -S . AssetAdministrationShell.jsonld > AssetAdministrationShell-sorted.jsonld
jq -S . AssetAdministrationShell-ttl2jsonld.jsonld > AssetAdministrationShell-ttl2jsonld-sorted.jsonld
```
The two files are the same, except for the array `preferredName` (which is `@collection:@set` not an `rdf:List` and so the order of elements is not guaranteed).


## Serialization: ttl->jsonld

Then I tried a turtle file:
- https://github.com/admin-shell-io/aas-specs/blob/master/schemas/rdf/examples/generated/AssetAdministrationShell/maximal.ttl (Saved as `AAS.ttl`)

This example has some defects:
- Doesn't specify `@base` but uses relative URLs like `<something_142922d6>`. This is a very bad practice.
  If you read it with `riot --formatted ttl AAS.ttl`, you'll see that's resolved to a URL using the current working directory, eg
  `<file:///d:/Onto/proj/aas/aas-core-codegen/test_data/jsonld_context/trials/something_142922d6>`
- Doesn't use almost any CURIES.
- Uses datatype `^^xs:string` which is the default thus superfluous.

Let's convert to JSONLD using the technique from the last section:
```
ttl2jsonld AAS.ttl | jsonld compact -c https://rawgit2.com/VladimirAlexiev/aas-core-codegen/main/test_data/jsonld_context/context-fixed.jsonld > AAS.jsonld
```

This looks almost reasonable, but has some defects:
- It starts with the same relative URL `"@id": "something_142922d6"`.
- In the context, `@type` is aliased to `modelType` at the top level, which causes these problems:
  - Instead of `"@type": ...` it emits the long form `"http://www.w3.org/1999/02/22-rdf-syntax-ns#type": {"@id": ...}`
  - It converts `globalAssetId "something_eea66fa1"^^xs:string` to this:
```
    "globalAssetId": {
      "modelType": "xs:string",
      "@value": "something_eea66fa1"
    }
```

I fixed this last problem by changing `context-fixed.jsonld`: from this:
```
  "modelType": "@type",
```
to this weaker form
```
  "modelType": {"@type": "@id", "@id": "rdf:type"},
```

### Round-tripping: ttl->jsonld->ttl
Because of the relative subject URL, we have to specify `--base`.
But even with that option, `riot` omits it when reading jsonld:
```
riot --formatted ttl --base=https://base/ AAS.jsonld
com.apicatalog.jsonld.deseralization.JsonLdToRdf build
WARNING: Non well-formed subject [something_142922d6] has been skipped.
```
So I first convert to NTriples using `jsonld`.

AAS uses blank nodes excessively, so comparing NTriple files is no fun since the blank node identifiers are not stable
(The RDF Canonicalization algorithm produces a deterministic serialization of an RDF graph, even in the face of blank nodes; but is not widely available.)

So I convert both the original and the round-tripped result to formatted Turtle:
```
riot --formatted ttl --base=https://base/ AAS.ttl > AAS-riot.ttl
jsonld format -q AAS.jsonld | riot -syntax nt --formatted ttl --base=https://base/ > AAS-jsonld-riot.ttl
```
Despite these efforts, `AAS-jsonld-riot.ttl` is defective in that it doesn't have a root subject.

So I added the following to `AAS.ttl`
```
@base <https://base/>.
```
And then repeated the conversions:
```
ttl2jsonld AAS.ttl | jsonld compact -c https://rawgit2.com/VladimirAlexiev/aas-core-codegen/main/test_data/jsonld_context/context-fixed.jsonld > AAS.jsonld
riot --formatted ttl AAS.ttl > AAS-riot.ttl
jsonld format -q AAS.jsonld | riot -syntax nt --formatted ttl > AAS-jsonld-riot.ttl
```

The two files are equivalent, with only stylistic differences:
- Use of `a` vs `rdf:type`
- Use of `aas:` prefix for types vs full URLs
- The order of `embeddedDataSpecifications` elements is not guaranteed


# Conclusions

`JSON-LD <-> RDF` round-tripping kind of works for one file, if the following things are fixed:
- Don't use relative URLs, or use `@base` (both in Turtle and JSON)
- Wrap the context in `@context`
- Don't alias `@type` to `modelType`

## Next Steps

- Produce a holistic Turtle example that includes as many submodels as possible, including numbers (decimal/float) and langStrings with real lang tags
- Load some realistic AAS data in a semantic repository, and work on a Frame to produce several JSON messages according to JSON schemas
- The context should live in https://github.com/admin-shell-io/aas-specs/, not in https://github.com/aas-core-works/aas-core-codegen/blob/main/test_data/jsonld_context/aas_core_meta.v3/output/
- The context needs to be served from some permanent URL, with Content Type `application/ld+json`

Enrich the context to cover:
- langStrings (https://github.com/admin-shell-io/aas-specs/issues/382)
  by mapping `language, text` to `@language, @value`. So instead of this:

```ttl
... <https://admin-shell.io/aas/3/0/DataSpecificationIec61360/preferredName>
  [ rdf:type  aas:LangStringPreferredNameTypeIec61360 ;
    <https://admin-shell.io/aas/3/0/AbstractLangString/language> "x-Sw4u3ZDO-nJLabnE" ;
    <https://admin-shell.io/aas/3/0/AbstractLangString/text> "something_5282e98e" ].
... <https://admin-shell.io/aas/3/0/Referable/displayName>
  [ rdf:type  aas:LangStringNameType ;
    <https://admin-shell.io/aas/3/0/AbstractLangString/language> "de-CH" ;
    <https://admin-shell.io/aas/3/0/AbstractLangString/text> "something_1e73716d" ].
```

We should have this:

```
... <https://admin-shell.io/aas/3/0/DataSpecificationIec61360/preferredName> "something_5282e98e"@x-Sw4u3ZDO-nJLabnE.
... <https://admin-shell.io/aas/3/0/Referable/displayName> "something_1e73716d"@de-CH.
```
Please note that the types `aas:LangStringPreferredNameTypeIec61360, aas:LangStringNameType` mean the same and are useless.

- Datatyped literals (https://github.com/admin-shell-io/aas-specs/issues/284).
  This will 
- More prefixes to shorten the Turtle representation (https://github.com/admin-shell-io/aas-specs/issues/43).
  Eg the above can be shortened to:

```ttl
... aas_dataSpec:preferredName
  [ rdf:type  aas:LangStringPreferredNameTypeIec61360 ;
    aas_str:language "x-Sw4u3ZDO-nJLabnE" ;
    aas_str:text "something_5282e98e" ].
... aas_ref:displayName
  [ rdf:type  aas:LangStringNameType ;
    aa_str:language "de-CH" ;
    aa_str:text "something_1e73716d" ].
```
