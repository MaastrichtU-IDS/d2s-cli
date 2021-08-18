import os
import glob
from rdflib import Graph, plugin, Literal, RDF, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID, DCAT
from rdflib.serializer import Serializer
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD
import requests
from dateutil.parser import parse as parsedate
import shutil
import pandas as pd 
import datetime
import pathlib

from d2s.utils import init_d2s_java, get_base_dir, get_parse_format, get_yaml_config

D2S = Namespace("https://w3id.org/d2s/vocab/")

def process_datasets_metadata(input_file=None, sample=False):
    """Read a RDF metadata file with infos about datasets, check if the dataset exist in the project SPARQL endpoint
    Download the data if new"""

    # If no metadata file provided, we search for one in the current folder
    if not input_file:
        file_list = glob.glob('*.ttl')
        if len(file_list) > 1:
            raise Exception("More than 1 metadata file have been found in the current folder: " + ', '.join(file_list)) 
        elif len(file_list) < 1:
            raise Exception("No metadata file has been found in the current folder") 
        else:
            input_file = file_list[0]
            print("📂 Loading the metadata file " + input_file)

    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    # Retrieve the files to download infos from the metadata turtle file
    g = Graph()
    g.parse(input_file, format=get_parse_format(input_file))
    download_file_list = []
    datasets_described = set()
    i = 0
    for subject, download_predicate, download_files_uri in g.triples((None, D2S.downloadFiles, None)):
        datasets_described.add(subject)
        download_file_list.append({})
        download_file_list[i]['downloadUrl'] = str(g.value(download_files_uri, DCAT.downloadURL))
        if (download_files_uri, D2S.downloadScript, None) in g:
            download_file_list[i]['downloadScript'] = str(g.value(download_files_uri, D2S.downloadScript))
        if (download_files_uri, D2S.postProcessScript, None) in g:
            download_file_list[i]['postProcessScript'] = str(g.value(download_files_uri, D2S.postProcessScript))
        i += 1

    # Retrieve the dataset URI in the metadata file
    if len(datasets_described) < 1:
        raise Exception("No dataset has been found in the metadata file") 
    elif len(datasets_described) > 1:
        raise Exception("More than 1 dataset has been found in the metadata file") 
    else:
        dataset_uri = datasets_described.pop()
    
    if (dataset_uri, D2S.processor, None) in g:
        processor = str(g.value(dataset_uri, D2S.processor))
    else:
        processor = 'rmlmapper-java'

    # TODO: Get data from the SPARQL endpoint, retrieve versions infos and last updated time
    sparql_endpoint = get_yaml_config('sparql-endpoint')
    # if sparql_endpoint:
    #     print('Querying the SPARQL endpoint ' + sparql_endpoint + ' to retrieve version infos for the dataset ' + dataset_uri)
    #     query = """PREFIX d2s: <https://w3id.org/d2s/vocab/>
    #     PREFIX pav: <http://purl.org/pav/>
    #     SELECT ?lastUpdated WHERE {
    #         <""" + str(dataset_uri) + """> pav:lastUpdateOn ?lastUpdated .
    #     }
    #     """
    #     # query = """SELECT * WHERE {
    #     #     ?s ?p ?o .
    #     # } LIMIT 10
    #     # """
    #     sparql = SPARQLWrapper(sparql_endpoint)
    #     sparql.setReturnFormat(JSON)
    #     sparql.setQuery(query)
    #     results = sparql.query().convert()
    #     print('SPARQLWrapper Results:')
    #     print(results["results"]["bindings"])
    #     last_updated = results["results"]["bindings"]["lastUpdated"]["value"]
    #     date_last_updated = parsedate(last_updated)
    #     print(results["results"]["bindings"]["lastUpdated"]["value"])

    # else:
    #     print('No SPARQL endpoint associated, running the download without checking if the graphs need to be updated')

    date_last_updated = None
    # yaml_config['sparql-endpoint']
    # print('yaml_config')
    # print(yaml_config)
    # remote_endpoint = get_yaml_config()['sparql-endpoint']
    # print(remote_endpoint)


    # For each file to download, check the LastModified date
    for dataset_download in download_file_list:
        url = dataset_download['downloadUrl']
        print('📤 Checking file at ' + url)
        r = requests.head(url)
        if 'last-modified' in r.headers.keys():
            url_last_modified = r.headers['last-modified']
            date_last_modified = parsedate(url_last_modified)
            print('📅 File last modified on ' + url_last_modified)
        else:
            print('Last modified date of the file could not be found')

    # Download if last modified date is later than last updated date (or if modified/updated date could not be fetched)
    if not date_last_modified or not date_last_updated or date_last_modified > date_last_updated:
        # Download file in data subfolder
        os.chdir('data')
        for ddl_file in download_file_list:
            if 'downloadScript' in ddl_file:
                print('📥 Running the download script: ' + ddl_file['downloadScript'])
                os.system(ddl_file['downloadScript'])

            if 'postProcessScript' in ddl_file:
                print('⛏️ Running the post processing script to prepare the downloaded file')
                os.system(ddl_file['postProcessScript'])

        # Check for .tsv .txt and .tab then convert to CSV (required for most RML engines)
        tab_files = glob.glob('*.tsv') + glob.glob('*.txt') + glob.glob('*.tab')
        for tsv_file in tab_files:
            csv_file = tsv_file[:-4] + '.csv'
            print('📄 Converting TSV file '+ tsv_file + ' to CSV ' + csv_file)
            try:
                tsv_to_csv_cmd = """sed -e 's/"//g' -e 's/\\t/","/g' -e 's/^/"/' -e 's/$/"/' -e 's/\\r//' """ + tsv_file + """ > """ + csv_file
                os.system(tsv_to_csv_cmd)
                # csv_table=pd.read_table(tsv_file,sep='\t')
                # csv_table.to_csv(csv_file, index=False)
            except Exception as e:
                print('Could not convert the file ' + tsv_file + ' to CSV')

        if sample:
            for csv_file in glob.glob('*.csv'):
                print('Creating a sample file with 100 lines for ' + csv_file)
                # if not os.path.exists(filename):
                full_csv_file = csv_file + '.full'
                shutil.copyfile(csv_file, full_csv_file)
                sample_cmd = """tail -n 100 """ + full_csv_file + """ > """ + csv_file
                os.system(sample_cmd)

        os.chdir('..')

        # For each YARRRML mappings: convert to RML and run mapper
        for file in glob.glob('*.yarrr.yml'):
            yarrrml_filename = os.fsdecode(file)
            rml_filepath = yarrrml_filename.replace('.yarrr.yml', '.rml.ttl')
            print('🦜 Converting YARRRML mapping '+ yarrrml_filename + ' to RML ' + rml_filepath)
            output_filepath = '../output/' + yarrrml_filename.replace('.yarrr.yml', '.ttl')
            os.system('yarrrml-parser -i ' + yarrrml_filename + ' -o ' + rml_filepath)

            # Run RML mapper depending on processor given in the metadata file
            if processor.lower() == 'rmlmapper-java':
                print('🗜️ Running the RML mapper with java to generate the RDF to ' + output_filepath)
                init_d2s_java('rmlmapper')
                # Change dir to fix issue with rmlmapper requiring to load a .dtd locally when reading DrugBank RML
                os.chdir('data')
                # Copy functions jar file in the same folder where we run the rmlmapper to fix issues with finding the functions
                shutil.copyfile('../../IdsRmlFunctions.jar', 'IdsRmlFunctions.jar')
                rml_cmd = 'java -jar ' + get_base_dir('rmlmapper.jar') + ' -s turtle -f ../../functions_ids.ttl -m ' + rml_filepath + ' -o ' + output_filepath
                os.system(rml_cmd)
                os.chdir('..')

            if processor.lower() == 'rmlstreamer':
                print('RMLStreamer not implemented yet')

            if processor.lower() == 'rocketrml':
                print('🚀 Running RocketRML with NodeJS to generate the RDF to ' + output_filepath)
                os.chdir('data')
                os.system('node ../../rocketrml.js -m ' + rml_filepath + ' -o ' + output_filepath)
                os.chdir('..')

        # file_time = datetime.datetime.fromtimestamp(os.path.getmtime(dstFile))
        # if url_date > file_time:
        #     # download it !









        # try:
        #     insert_results = insert_file_in_sparql_endpoint(file_path, sparql_endpoint, username, password, graph_uri, chunks_size)
        # except Exception as e:
        #     print('Error with INSERT of file: ' + file_path)
        #         print(e)





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
    g.parse(file_path, format=get_parse_format(file_path))
    insert_results = insert_graph_in_sparql_endpoint(g, sparql_endpoint, username, password, graph_uri, chunks_size)
    return insert_results

def insert_graph_in_sparql_endpoint(g, sparql_endpoint, username, password, graph_uri=None, chunks_size=1000, operation='INSERT'):
    """Insert rdflib graph in a Update SPARQL endpoint using SPARQLWrapper
    :param g: rdflib graph to insert
    :return: SPARQL update query result
    """
    # print(g.serialize(format='nt').decode('utf-8'))
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setMethod(POST)
    # sparql.setHTTPAuth(BASIC) or DIGEST
    sparql.setCredentials(username, password)
    graph_start = ''
    graph_end = ''
    if graph_uri:
        graph_start = 'GRAPH  <' + graph_uri + '> {'
        graph_end = ' } '

    load_triples = g.serialize(format='nt').decode('utf-8')
    print(load_triples)
    print(operation + ' ' + str(len(load_triples.split("\n"))) + ' statements per chunks of ' + str(chunks_size) + ' statements')
    chunks_size = int(chunks_size)
    if chunks_size < 5:
        # Load all in one shot
        list_of_strings = [load_triples]
    else:
        list_of_strings = ['\n'.join(load_triples.split("\n")[i:i + chunks_size]) for i in range(0, len(load_triples.split("\n")), chunks_size)]

    for rdf_chunk in list_of_strings:
        print(rdf_chunk)
        try:
            query = """{operation} DATA {{ 
            {graph_start}
            {ntriples}
            {graph_end}
            }}
            """.format(ntriples=rdf_chunk, graph_start=graph_start, graph_end=graph_end, operation=operation)
            sparql.setQuery(query)
            query_results = sparql.query()
        except:
            print('INSERT DATA failed, trying INSERT')
            # If blank nodes, we need to do INSERT for Virtuoso
            # TODO: split ntriples in chunk to load less than 10000 lines
            query = """{operation} {{ 
            {graph_start}
            {ntriples}
            {graph_end}
            }}
            """.format(ntriples=rdf_chunk, graph_start=graph_start, graph_end=graph_end)
            sparql.setQuery(query)
            query_results = sparql.query()
        # print('Done')
        print(query_results.response.read())
    
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