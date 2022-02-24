import os
import pathlib
import glob
from rdflib import Graph, Literal, RDF, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD
from d2s.utils import init_d2s_java, get_base_dir
import requests

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
    elif file_extension in ['.nq']:
        file_format = 'nquads'
    g = Graph()
    g.parse(file_path, format=file_format)
    insert_results = insert_graph_in_sparql_endpoint(g, sparql_endpoint, username, password, graph_uri, chunks_size)
    return insert_results

def insert_graph_in_sparql_endpoint(g, sparql_endpoint, username, password, graph_uri=None, chunks_size=1000, operation='INSERT'):
    """Insert rdflib graph in a Update SPARQL endpoint using SPARQLWrapper
    :param g: rdflib graph to insert
    :return: SPARQL update query result
    """
    # print(g.serialize(format='nt'))
    # graph_endpoint = f'{sparql_endpoint}/rdf-graphs/{graph_uri}'
    # graph_endpoint = 'https://graphdb.dumontierlab.com/repositories/shapes-registry/rdf-graphs/shapes:github'

    # Post RDF file to SPARQL endpoint using basic auth (works for GraphDB)
    try:
        resp = requests.post(f"{sparql_endpoint}", 
            headers={ 'Content-Type': 'text/turtle' },
            data=str(g.serialize(format='turtle')).encode('utf-8'),
            auth=(username, password),
        )
        print(resp)
    except Exception as e:
        print(e)
    # print(resp.request.body)

    # sparql = SPARQLWrapper(sparql_endpoint)
    # sparql.setMethod(POST)
    # # sparql.setHTTPAuth(BASIC) or DIGEST
    # sparql.setCredentials(username, password)
    # graph_start = ''
    # graph_end = ''
    # if graph_uri:
    #     graph_start = 'GRAPH  <' + graph_uri + '> {'
    #     graph_end = ' } '

    # # load_triples = g.serialize(format='nt').decode('utf-8')
    # load_triples = str(g.serialize(format='nt'))
    # print(operation + ' ' + str(len(load_triples.split("\n"))) + ' statements per chunks of ' + str(chunks_size) + ' statements')
    # chunks_size = int(chunks_size)
    # if chunks_size < 5:
    #     # Load all in one shot
    #     list_of_strings = [load_triples]
    # else:
    #     list_of_strings = ['\n'.join(load_triples.split("\n")[i:i + chunks_size]) for i in range(0, len(load_triples.split("\n")), chunks_size)]

    # for rdf_chunk in list_of_strings:
    #     # print(rdf_chunk)
    #     try:
    #         query = """{operation} DATA {{ 
    #         {graph_start}
    #         {ntriples}
    #         {graph_end}
    #         }}
    #         """.format(ntriples=rdf_chunk, graph_start=graph_start, graph_end=graph_end, operation=operation)
    #         sparql.setQuery(query)
    #         query_results = sparql.query()
    #     except:
    #         print('INSERT DATA failed, trying INSERT')
    #         # If blank nodes, we need to do INSERT for Virtuoso
    #         # TODO: split ntriples in chunk to load less than 10000 lines
    #         query = """{operation} {{ 
    #         {graph_start}
    #         {ntriples}
    #         {graph_end}
    #         }}
    #         """.format(ntriples=rdf_chunk, graph_start=graph_start, graph_end=graph_end)
    #         sparql.setQuery(query)
    #         query_results = sparql.query()
    #     # print('Done')
    #     print(query_results.response.read())
    

def sparql_update_instance(subject_uri, new_graph, sparql_endpoint, username, password, depth=1, graph_uri=None):
    """Run a construct query to get a RDF graph with all triples for the subject_uri
    Use rdflib to compare this graph to the new graph we just generated
    If diff then delete old instance statements and insert new_graph
    """
    # https://rdflib.readthedocs.io/en/4.0/_modules/rdflib/compare.html
    from rdflib.compare import IsomorphicGraph, graph_diff
    print('Starting graph diff for ' + str(subject_uri))
    construct_array = []
    where_array = []
    current_depth = 0
    while current_depth <= depth:
        pattern = '?o' + str(current_depth) + ' ?p' + str(current_depth) + ' ?o' + str(current_depth+1) + ' . '
        construct_array.append(pattern)
        where_array.append('OPTIONAL{' + pattern + '} ')
        current_depth += 1
        
    construct_query = "CONSTRUCT { ?s ?p ?o1 . " + ' '.join(construct_array) + " } WHERE { ?s ?p ?o . " + ' '.join(where_array) + " FILTER(?s = <" + subject_uri + ">) }"
    # CONSTRUCT { ?s ?p ?o1 . ?o1 ?p1 ?o2 . } WHERE { ?s ?p ?o . OPTIONAL{?o1 ?p1 ?o2 .} FILTER... }
    print(sparql_endpoint)
    print(construct_query)
    
    # new_graph.setReturnFormat(TURTLE)
    # results = new_graph.query(construct_query).convert().decode('utf-8')
    results = new_graph.query(construct_query)
    new_g = IsomorphicGraph()
    new_g.parse(data=results.serialize(format='xml'), format=TURTLE)
    print('New G done')
    
    old_g = IsomorphicGraph()
    sparql = SPARQLWrapper(sparql_endpoint)
    # sparql.setQuery(construct_query)
    sparql.setReturnFormat(TURTLE)
    results = sparql.query(construct_query).convert().decode('utf-8')
    old_g.parse(data=results, format="turtle")
    print('Old G done')
    # Write RDF to file
    # with open(self.get_dir(output_file), 'w') as f:
    #     f.write(results)

    if new_g == old_g:
        print('Graph already up to date for file ' + str(subject_uri))
        return 'uptodate'
    else:
        print('Update graph for file ' + str(subject_uri))
        in_both, in_first, in_second = graph_diff(new_g, old_g)
        # Delete old graph and insert new graph
        insert_graph_in_sparql_endpoint(old_g, sparql_endpoint, username, password, graph_uri, 4500, 'DELETE')
        insert_graph_in_sparql_endpoint(new_graph, sparql_endpoint, username, password, graph_uri, 4500, 'INSERT')
        return { 'in_both': in_both, 'in_first': in_first, 'in_second': in_second }

def java_upload_files(file_pattern, sparql_endpoint, username, password, graph=None):
    """Upload RDF files to a SPARQL endpoint using d2s-sparql-operations Java RDF4J
    Java installed required"""
    init_d2s_java('sparql-operations')
    graph_str = ''
    if graph:
        graph_str = ' -g ' + graph
    os.system('java -jar ' + get_base_dir('sparql-operations.jar') 
        + ' -o upload -i "' + file_pattern + '" -e ' + sparql_endpoint
        + ' -u ' + username + ' -p ' + password + graph_str )