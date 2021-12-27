****************
aas-core-codegen
****************

Aas-core-codegen generates code to handle asset administration shells based on the meta-model.

``--help``
==========

.. Help starts: aas-core-codegen --help
.. code-block::

    usage: aas-core-codegen [-h] --model_path MODEL_PATH --snippets_dir
                            SNIPPETS_DIR --output_dir OUTPUT_DIR --target
                            {csharp,jsonschema,rdf-shacl,xsd}

    Generate different implementations and schemas based on an AAS meta-model.

    optional arguments:
      -h, --help            show this help message and exit
      --model_path MODEL_PATH
                            path to the meta-model
      --snippets_dir SNIPPETS_DIR
                            path to the directory containing implementation-
                            specific code snippets
      --output_dir OUTPUT_DIR
                            path to the generated code
      --target {csharp,jsonschema,rdf-shacl,xsd}
                            target language or schema

.. Help ends: aas-core-codegen --help
