import os
import re
import click
import pathlib
import urllib.parse
from datetime import date, datetime
import pkg_resources
from rdflib import Graph, Literal, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID, SKOS, DCAT, PROV, FOAF
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD

# DATASET_NAMESPACE = 'https://w3id.org/d2s/dataset/'

SCHEMA = Namespace("http://schema.org/")
DCTYPES = Namespace("http://purl.org/dc/dcmitype/")
PAV = Namespace("http://purl.org/pav/")
IDOT = Namespace("http://identifiers.org/idot/")
D2S = Namespace("https://w3id.org/d2s/vocab/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")


def create_dataset_prompt(sparql_endpoint, distribution_uri, g=Graph(), output_file=None):
    """Create a new dataset from questions asked in the prompt"""
    metadataArray = []
    # metadataArray.append({'id': 'dataset_id', 'description': 'Enter the identifier of your datasets, e.g. drugbank (lowercase, no space or weird characters)'})
    metadataArray.append({'id': 'name', 'description': 'Enter a human-readable name for this dataset, e.g. DrugBank'})
    metadataArray.append({'id': 'description', 'description': 'Enter a description for this dataset'})
    metadataArray.append({'id': 'downloadURL', 'default': 'https://www.drugbank.ca/releases/5-1-1/downloads/all-full-database', 'description': 'Enter the URL of the source data'})
    metadataArray.append({'id': 'license', 'default': 'http://creativecommons.org/licenses/by-nc/4.0/legalcode', 'description': 'Enter a valid URL to the license informations about the original dataset'})
    metadataArray.append({'id': 'publisher_name', 'default': 'Institute of Data Science at Maastricht University', 'description': 'Enter the name of the institution publishing the data and its affiliation, e.g. Institute of Data Science at Maastricht University'})
    metadataArray.append({'id': 'publisher_url', 'default': 'https://maastrichtuniversity.nl/ids', 'description': 'Enter a valid URL for the publisher homepage.'})
    metadataArray.append({'id': 'created', 'default': date.today(), 'description': 'Enter the date at which the data has been published'})
    metadataArray.append({'id': 'format', 'default': 'application/xml', 'description': 'Enter the format of the source data'})
    metadataArray.append({'id': 'language', 'default': 'http://lexvo.org/id/iso639-3/eng', 'description': 'Enter the lexvo URI for the language of the data'})
    metadataArray.append({'id': 'homepage', 'default': 'http://d2s.semanticscience.org/', 'description': 'Enter the URL of the dataset homepage'})
    # metadataArray.append({'id': 'accessURL', 'default': 'https://www.drugbank.ca/releases/latest', 'description': 'Specify URL of the directory containing the file(s) of interest (not the direct file URL)'})
    metadataArray.append({'id': 'references', 'default': 'https://www.ncbi.nlm.nih.gov/pubmed/29126136', 'description': 'Enter the URL of a publication supporting the dataset'})
    metadataArray.append({'id': 'keyword', 'default': 'drug', 'description': 'Enter a keyword to describe the dataset'})
    # metadataArray.append({'id': 'sparqlEndpoint', 'description': 'Enter the URL of the final SPARQL endpoint to access the integrated dataset',
    #     'default': 'https://graphdb.dumontierlab.com/repositories/test-vincent'})
    # metadataArray.append({'id': 'theme', 'default': 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C54708', 'description': 'Enter the URL to an ontology concept describing the dataset theme'})

    metadata_answers = {}
    for metadataObject in metadataArray:
        if 'default' in metadataObject:
            metadata_answers[metadataObject['id']] = click.prompt(click.style('[?]', bold=True) 
            + ' ' + metadataObject['description'] + ' e.g.',
            default=metadataObject['default'])
        else:
            metadata_answers[metadataObject['id']] = click.prompt(click.style('[?]', bold=True) 
            + ' ' + metadataObject['description'])

    g = create_dataset(metadata_answers, sparql_endpoint, distribution_uri, g)

    if output_file:
        g.serialize(destination=output_file, format='turtle')
        print("Metadata stored to " + output_file + ' 📝')
    # else:
    #     print(g.serialize(format='turtle'))

    return g, metadata_answers


def create_dataset(metadata, sparql_endpoint, distribution_uri, g):
    """Create a new dataset from provided metadata JSON object"""
    g.bind("foaf", FOAF)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("skos", SKOS)
    g.bind("schema", SCHEMA)
    g.bind("dcat", DCAT)
    g.bind("prov", PROV)
    g.bind("dc", DC)
    g.bind("dctypes", DCTYPES)
    g.bind("dct", DCTERMS)
    g.bind("pav", PAV)
    g.bind("idot", IDOT)
    g.bind("void", VOID)
    g.bind("d2s", D2S)
    # g.bind("owl", OWL)

    distribution_uri_slash = distribution_uri + '/' if not distribution_uri.endswith('/') else distribution_uri
    created_date = Literal(metadata['created'], datatype=XSD.date)
    lang = 'en'
    # created_date = Literal(date.today(),datatype=XSD.date)

    # Summary
    summary_uri = URIRef(f"{distribution_uri_slash}summary")
    g.add((summary_uri, RDF.type, DCTYPES['Dataset']))
    # g.add((summary_uri, RDFS['label'], Literal(metadata['name'] + ' dataset summary')))
    # g.add((summary_uri, DC.identifier, Literal(metadata['dataset_id'])))
    # g.add((summary_uri, IDOT['preferredPrefix'], Literal(metadata['dataset_id'])))
    g.add((summary_uri, DCTERMS.description, Literal(metadata['description'], lang=lang)))
    g.add((summary_uri, DCTERMS.title, Literal(metadata['name'], lang=lang)))
    g.add((summary_uri, FOAF['page'], URIRef(metadata['homepage'])))
    # g.add((summary_uri, DCAT['accessURL'], URIRef(metadata['accessURL'])))
    g.add((summary_uri, DCTERMS.references, URIRef(metadata['references'])))
    g.add((summary_uri, DCAT['keyword'], Literal(metadata['keyword'])))
    g.add((summary_uri, VOID.sparqlEndpoint, URIRef(sparql_endpoint)))

    # Publisher
    publisher_uri = URIRef(f"{distribution_uri_slash}agent/{urllib.parse.quote(metadata['publisher_name'])}")
    g.add((publisher_uri, RDF.type, DCTERMS.Agent))
    g.add((publisher_uri, FOAF['name'], Literal(metadata['publisher_name'])))
    g.add((publisher_uri, FOAF['page'], Literal(metadata['publisher_url'])))
    g.add((summary_uri, DCTERMS.publisher, publisher_uri))

    # Version
    version = '1'
    version_uri = URIRef(f"{distribution_uri_slash}version/{version}")
    g.add((version_uri, RDF.type, DCTYPES['Dataset']))
    g.add((version_uri, DCTERMS.title, Literal(f"{metadata['name']} dataset version", lang=lang)))
    g.add((version_uri, DCTERMS.description, Literal(f"{metadata['name']} dataset version", lang=lang)))
    g.add((version_uri, DCTERMS.isVersionOf, summary_uri))
    g.add((version_uri, PAV['version'], Literal(version)))
    g.add((version_uri, DCTERMS.creator, publisher_uri))
    g.add((version_uri, DCTERMS.publisher, publisher_uri))
    g.add((version_uri, DCTERMS.license, URIRef(metadata['license'])))
    g.add((version_uri, DCTERMS.language, URIRef(metadata['language'])))
    # g.add((version_uri, DCTERMS.created, created_date))

    # TODO: Add language?? With lexvo URI
    # Source distribution
    source_uri = URIRef(f"{distribution_uri_slash}version/{version}/source")
    g.add((source_uri, RDF.type, DCAT['Distribution']))
    g.add((source_uri, DCTERMS.title, Literal(f"{metadata['name']} source distribution", lang=lang)))
    g.add((source_uri, DCTERMS.description, Literal(f"{metadata['name']} source distribution", lang=lang)))
    g.add((source_uri, DCTERMS['format'], Literal(metadata['format'])))
    g.add((source_uri, DCAT['downloadURL'], URIRef(metadata['downloadURL'])))
    g.add((source_uri, DCTERMS.creator, publisher_uri))
    g.add((source_uri, DCTERMS.publisher, publisher_uri))
    g.add((source_uri, DCTERMS.license, URIRef(metadata['license'])))
    g.add((source_uri, DCTERMS.language, URIRef(metadata['language'])))
    g.add((source_uri, DCTERMS.created, created_date))
    g.add((source_uri, DCTERMS.issued, created_date))

    # RDF Distribution description
    rdf_uri = URIRef(distribution_uri)
    # rdf_uri_string = dataset_namespace + metadata['dataset_id'] + '/version/' + version + '/distribution/rdf'
    # rdf_uri = URIRef(rdf_uri_string)
    g.add((rdf_uri, RDF.type, DCAT['Distribution']))
    g.add((rdf_uri, RDF.type, VOID.Dataset))
    g.add((rdf_uri, DCTERMS.title, Literal(metadata['name'], lang=lang)))
    g.add((rdf_uri, DCTERMS.description, Literal(f"{metadata['name']} RDF distribution", lang=lang)))
    g.add((rdf_uri, DCTERMS.source, source_uri))
    g.add((rdf_uri, DCTERMS.creator, publisher_uri))
    g.add((rdf_uri, DCTERMS.publisher, publisher_uri))
    g.add((rdf_uri, DCTERMS.license, URIRef(metadata['license'])))
    # g.add((rdf_uri, DCTERMS.format, Literal('application/sparql-results+json')))
    g.add((rdf_uri, DCTERMS.format, URIRef('http://www.w3.org/ns/formats/Turtle')))
    g.add((rdf_uri, DCTERMS.language, URIRef(metadata['language'])))
    g.add((rdf_uri, DCTERMS.created, created_date))
    g.add((rdf_uri, DCTERMS.issued, created_date))

    g.add((version_uri, DCAT['distribution'], source_uri))
    g.add((version_uri, DCAT['distribution'], rdf_uri))

    if sparql_endpoint:
        g.add((rdf_uri, DCAT['accessURL'], URIRef(sparql_endpoint)))
    
    return g

def generate_hcls_from_sparql(sparql_endpoint, rdf_distribution_uri, metadata_type, graph, g=Graph(), create_dataset=False):
    """Query the provided SPARQL endpoint to compute HCLS metadata"""
    sparql = SPARQLWrapper(sparql_endpoint)
    root = pathlib.Path(__file__).parent.resolve()
    with open(root / '../REPORT_FAIL.md', 'w') as f:
        f.write('# Failing HCLS SPARQL queries\n\n\n')
    with open(root / '../REPORT_SUCCESS.md', 'w') as f:
        f.write('# Generated HCLS metadata\n\n\n')

    query_prefixes = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dqv: <http://www.w3.org/ns/dqv#>
PREFIX hcls: <http://www.w3.org/hcls#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dctypes: <http://purl.org/dc/dcmitype/>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX void: <http://rdfs.org/ns/void#>
PREFIX void-ext: <http://ldf.fi/void-ext#>\n"""

    # If no specific graph provided we get graphs from the SPARQL endpoint
    if not graph:
        query_select_all_graphs = 'SELECT DISTINCT ?graph WHERE { GRAPH ?graph {?s ?p ?o} }'
        sparql.setQuery(query_select_all_graphs)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        # print('Get all graphs query Results:')
        # print(results)
        select_all_graphs_results = results["results"]["bindings"]
    else: 
        # Just query the single provided graph
        select_all_graphs_results = [{ 'graph': {'value': str(graph)}}]

    # Compute HCLS metadata per graph
    for graph_row in select_all_graphs_results:
        graph = graph_row['graph']['value']

        if metadata_type == 'bio2rdf' and not graph.startswith('http://bio2rdf.org'):
            # For bio2rdf ignore Virtuoso default graphs
            continue

        print('[' + str(datetime.now()) + '] Computing metadata for graph ' + graph)
        for filename in os.listdir(pkg_resources.resource_filename('d2s', 'queries/' + metadata_type)):
            with open(pkg_resources.resource_filename('d2s', 'queries/' + metadata_type + '/' + filename), 'r') as f:
                sparql_query = f.read()

                # Define variables to replace for the different metadata type here
                if metadata_type == 'bio2rdf':
                    namespace_search = re.search('http:\/\/bio2rdf\.org\/(.*)_resource:bio2rdf\.dataset\.(.*)\.R[0-9]*', graph, re.IGNORECASE)
                    if namespace_search:
                        graph_namespace = namespace_search.group(1)
                        sparql_query = sparql_query.replace('?_graph_namespace', graph_namespace)
                    # extract namespace from graph URI

                if metadata_type == 'hcls':
                    if (graph):
                        sparql_query = sparql_query.replace('?_graph_uri', graph)
                        sparql_query = sparql_query.replace('<?_graph_start>', 'GRAPH <' + graph + '> {')
                        sparql_query = sparql_query.replace('<?_graph_end>', '}')
                    else:
                        sparql_query = sparql_query.replace('?_graph_uri', rdf_distribution_uri)
                        sparql_query = sparql_query.replace('<?_graph_start>', '')
                        sparql_query = sparql_query.replace('<?_graph_end>', '')

                complete_query = query_prefixes + sparql_query 
                # print(complete_query)

                try:
                    sparql.setQuery(complete_query)
                    sparql.setReturnFormat(TURTLE)
                    # sparql.setReturnFormat(JSONLD)
                    results = sparql.query().convert()
                    # g.parse(data=results, format="turtle")
                    # g.parse(data=results, format="json-ld")

                    g.parse(data=results, format="turtle")
                    with open(root / '../REPORT_SUCCESS.md', 'a') as f:
                        # f.write('## Returned RDF \n\n```turtle\n' + results.decode('utf-8') + "\n```\n\n"
                        f.write('## Successfull query \n\n'
                            + '```sparql\n' + complete_query + "\n```\n\n"
                            + 'In SPARQL endpoint: ' + sparql_endpoint + "\n\n---\n")
                except Exception as e:
                    print('SPARQL query failed:')
                    print(complete_query)
                    print(e)
                    with open(root / '../REPORT_FAIL.md', 'a') as f:
                        f.write('## Query failed \n\n```sparql\n' + complete_query + "\n```\n\n"
                            + 'In SPARQL endpoint: ' + sparql_endpoint + "\n> " 
                            + str(e) + "\n\n---\n")

        if create_dataset:
            g, metadata_answers = create_dataset_prompt(sparql_endpoint, graph, g)
            # dataset_uri = f"{graph}/dataset"
            # g, metadata_answers = create_dataset_prompt(dataset_uri, g)

    # print(g.serialize(format='json-ld', indent=4))
    # print(g.serialize(format='turtle', indent=4))
    return g


# {
#   "@context": "/contexts/GraphMap",
#   "@id": "/graph_maps",
#   "@type": "hydra:Collection",
#   "hydra:member": [
#     {
#       "@id": "/graph_maps/3",
#       "@type": "http://example.org/GraphMap",
#       "subjectType": "http://www.w3.org/2000/01/rdf-schema#Resource",
#       "predicate": "http://semanticscience.org/resource/has-participant",
#       "objectType": "http://www.w3.org/2000/01/rdf-schema#Resource",
#       "dataset": "/datasets/3",
#       "id": 3
#     },
#     {
#       "@id": "/graph_maps/4",
#       "@type": "http://example.org/GraphMap",
#       "subjectType": "http://www.w3.org/2000/01/rdf-schema#Resource",
#       "predicate": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
#       "objectType": "http://www.ebi.ac.uk/efo/EFO_0001067",
#       "dataset": "/datasets/3",
#       "id": 4
#     }
#   ],
#   "hydra:totalItems": 2
# }

# {
#   "@context": "/contexts/Dataset",
#   "@id": "/datasets",
#   "@type": "hydra:Collection",
#   "hydra:member": [
#     {
#       "@id": "/datasets/3",
#       "@type": "http://www.w3.org/ns/dcat#Dataset",
#       "identifier": "mw1",
#       "title": "Infections",
#       "description": "A dataset of infections",
#       "publisher": "http://fairdata.systems",
#       "license": "http://fairdata.systems/dataset/infections/license",
#       "publicationDate": "2020-11-12T11:25:00+00:00",
#       "publisher_name": "Mark Wilkinson",
#       "graphmaps": [
#         "/graph_maps/3",
#         "/graph_maps/4"
#       ],
#       "dataservices": [
#         "/data_services/1"
#       ],
#       "id": 3
#     }
#   ],
#   "hydra:totalItems": 1
# }

# {
#   "@context": "/contexts/DataService",
#   "@id": "/data_services",
#   "@type": "hydra:Collection",
#   "hydra:member": [
#     {
#       "@id": "/data_services/1",
#       "@type": "http://www.w3.org/ns/dcat#DataService",
#       "name": "Infections endpoint",
#       "description": "A SPARQL endpoint with infection data",
#       "url": "http://fairdata.systems:8990/sparql",
#       "serviceType": "SPARQL",
#       "conformsTo": "https://www.w3.org/TR/sparql11-overview/",
#       "publisher": "http://fairdata.systems",
#       "dataset": "/datasets/3",
#       "id": 1
#     }
#   ],
#   "hydra:totalItems": 1
# }