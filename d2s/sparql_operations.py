import os
import pathlib
import glob
from rdflib import Graph, plugin, Literal, RDF, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID
from rdflib.serializer import Serializer
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD

# DATASET_NAMESPACE = 'https://w3id.org/d2s/dataset/'

# RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
# RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
# OWL = Namespace("http://www.w3.org/2002/07/owl#")
# SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
# SCHEMA = Namespace("http://schema.org/")
# DCAT = Namespace("http://www.w3.org/ns/dcat#")
# PROV = Namespace("http://www.w3.org/ns/prov#")
# DC = Namespace("http://purl.org/dc/elements/1.1/")
# DCTYPES = Namespace("http://purl.org/dc/dcmitype/")
# PAV = Namespace("http://purl.org/pav/")
# IDOT = Namespace("http://identifiers.org/idot/")
# FOAF = Namespace("http://xmlns.com/foaf/0.1/")

def sparql_insert_files(file_pattern, sparql_endpoint, username, password, graph_uri=None, chunks_size=1000):
    for file_path in glob.glob(file_pattern):
        print('INSERT file: ' + file_path)
        try:
            insert_results = insert_file_in_sparql_endpoint(file_path, sparql_endpoint, username, password, graph_uri, chunks_size)
        except Exception as e:
            print('Error with INSERT of file: ' + file_path)
            print(e)


def insert_file_in_sparql_endpoint(file_path, sparql_endpoint, username, password, graph_uri=None, chunks_size=1000):
    # file_path = 'file.ttl'
    filename, file_extension = os.path.splitext(file_path)
    file_format = ''
    # Get file format for rdflib.parse based on file extension
    if file_extension in ['.trig', '.n3']:
        file_format = 'n3'
    elif file_extension in ['.json', '.jsonld', '.json-ld']:
        file_format = 'json-ld'
    elif file_extension in ['.xml', '.rdf']:
        file_format = 'xml'
    elif file_extension in ['.ttl', '.shacl']:
        file_format = 'ttl'
    elif file_extension in ['.nt']:
        file_format = 'nt'
    g = Graph()
    g.parse(file_path, format=file_format)
    insert_results = insert_graph_in_sparql_endpoint(g, sparql_endpoint, username, password, graph_uri, chunks_size)
    return insert_results

def insert_graph_in_sparql_endpoint(g, sparql_endpoint, username, password, graph_uri=None, chunks_size=1000):
    """Insert rdflib graph in a Update SPARQL endpoint using SPARQLWrapper
    :param g: rdflib graph to insert
    :return: SPARQL update query result
    """
    # print(g.serialize(format='nt').decode('utf-8'))
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setMethod(POST)
    # sparql.setHTTPAuth(BASIC)
    sparql.setCredentials(username, password)
    graph_start = ''
    graph_end = ''
    if graph_uri:
        graph_start = 'GRAPH  <' + graph_uri + '> {'
        graph_end = ' } '

    load_triples = g.serialize(format='nt').decode('utf-8')
    print('Insert ' + str(len(load_triples.split("\n"))) + ' statements per chunks of ' + str(chunks_size) + ' statements')
    chunks_size = int(chunks_size)
    if chunks_size < 5:
        # Load all in one shot
        list_of_strings = [load_triples]
    else:
        list_of_strings = ['\n'.join(load_triples.split("\n")[i:i + chunks_size]) for i in range(0, len(load_triples.split("\n")), chunks_size)]

    for rdf_chunk in list_of_strings:
        try:
            query = """INSERT DATA {{ 
            {graph_start}
            {ntriples}
            {graph_end}
            }}
            """.format(ntriples=rdf_chunk, graph_start=graph_start, graph_end=graph_end)
            sparql.setQuery(query)
            query_results = sparql.query()
        except:
            print('INSERT DATA failed, trying INSERT')
            # If blank nodes, we need to do INSERT for Virtuoso
            # TODO: split ntriples in chunk to load less than 10000 lines
            query = """INSERT {{ 
            {graph_start}
            {ntriples}
            {graph_end}
            }}
            """.format(ntriples=rdf_chunk, graph_start=graph_start, graph_end=graph_end)
            sparql.setQuery(query)
            query_results = sparql.query()
        print('Done')
    
