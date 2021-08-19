import os
import glob
from rdflib import Graph, plugin, Literal, RDF, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID, DCAT
from rdflib.serializer import Serializer
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD
import requests
from dateutil.parser import parse as parsedate
import shutil
import stat
import pandas as pd 
import datetime
import pathlib

from d2s.utils import init_d2s_java, get_base_dir, get_parse_format, get_yaml_config
from d2s.sparql_operations import insert_graph_in_sparql_endpoint, java_upload_files
from d2s.generate_metadata import generate_hcls_from_sparql

D2S = Namespace("https://w3id.org/d2s/vocab/")

def process_datasets_metadata(input_file=None, sample=False, dryrun=True):
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
    
    if (dataset_uri, DC.identifier, None) in g:
        dataset_id = str(g.value(dataset_uri, DC.identifier))
    else:
        raise Exception("Could not find the dc:identifier property for the dataset in the metadata file") 

    if (dataset_uri, D2S.processor, None) in g:
        processor = str(g.value(dataset_uri, D2S.processor))
    else:
        processor = 'rmlmapper-java'
    if (dataset_uri, D2S.rdfSyntax, None) in g:
        rdfSyntax = str(g.value(dataset_uri, D2S.rdfSyntax))
    else:
        rdfSyntax = 'turtle'

    if rdfSyntax == 'ntriples':
        output_file_extension = '.nt'
        output_file_mimetype = 'application/n-triples'
    else:
        output_file_extension = '.ttl'
        output_file_mimetype = 'text/turtle'

    # TODO: Get data from the SPARQL endpoint, retrieve versions infos and last updated time
    prod_endpoint = get_yaml_config('production')['sparql-endpoint']
    prod_ldp = get_yaml_config('production')['virtuoso-ldp-url']
    staging_endpoint = get_yaml_config('staging')['sparql-endpoint']
    staging_ldp = get_yaml_config('staging')['virtuoso-ldp-url']
    endpoint_user = os.getenv('DBA_USER', 'dba')
    endpoint_password = os.getenv('DBA_PASSWORD')

    if prod_endpoint:
        print('Querying the SPARQL endpoint ' + prod_endpoint + ' to retrieve version infos for the dataset ' + dataset_uri)
        query = """PREFIX d2s: <https://w3id.org/d2s/vocab/>
        PREFIX pav: <http://purl.org/pav/>
        SELECT ?lastUpdated WHERE {
            <""" + str(dataset_uri) + """> pav:lastUpdateOn ?lastUpdated .
        }
        """
        # query = """SELECT * WHERE {
        #     ?s ?p ?o .
        # } LIMIT 10
        # """
        sparql = SPARQLWrapper(prod_endpoint)
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)
        results = sparql.query().convert()
        print('SPARQLWrapper Results:')
        print(results["results"]["bindings"])
        last_updated = results["results"]["bindings"]["lastUpdated"]["value"]
        date_last_updated = parsedate(last_updated)
        print(results["results"]["bindings"]["lastUpdated"]["value"])

    # else:
    #     print('No SPARQL endpoint associated, running the download without checking if the graphs need to be updated')

    date_last_updated = None

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
    # file_time = datetime.datetime.fromtimestamp(os.path.getmtime(dstFile))
    # if url_date > file_time:
    #     download it !
    if not date_last_modified or not date_last_updated or date_last_modified > date_last_updated:
        # Download file in data subfolder
        os.chdir('data')
        for ddl_file in download_file_list:
            if 'downloadScript' in ddl_file:
                print('📥 Running the download script: ' + ddl_file['downloadScript'])
                os.system(ddl_file['downloadScript'])

            if 'postProcessScript' in ddl_file:
                script = ddl_file['postProcessScript']
                print('⛏️ Running the post processing script to prepare the downloaded file')
                if script.startswith('https://') or script.startswith('http://'):
                    # Download script from URL
                    os.system('wget -N ' + script)
                    os.chmod(script, stat.S_IEXEC)
                    script_cmd = './' + script
                elif script.endswith('.sh'):
                    # Local shell script
                    shutil.copyfile('../' + script, script)
                    os.chmod(script, stat.S_IEXEC)
                    script_cmd = './' + script
                else:
                    # Directly provided a bash command
                    script_cmd = script
                os.system(script_cmd)

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

        # Go back to dataset folder to convert YARRML files
        os.chdir('..')

        # For each YARRRML mappings: convert to RML and run mapper
        for file in glob.glob('*.yarrr.yml'):
            yarrrml_filename = os.fsdecode(file)
            rml_filename = yarrrml_filename.replace('.yarrr.yml', '.rml.ttl')
            print('🦜 Converting YARRRML mapping '+ yarrrml_filename + ' to RML ' + rml_filename)
            output_filepath = '../output/' + yarrrml_filename.replace('.yarrr.yml', output_file_extension)
            os.system('yarrrml-parser -i ' + yarrrml_filename + ' -o data/' + rml_filename)

            # Run RML mapper depending on processor given in the metadata file
            if processor.lower() == 'rmlmapper-java':
                print('🗜️ Running the RML mapper with java to generate the RDF to ' + output_filepath)
                init_d2s_java('rmlmapper')
                # Change dir to fix issue with rmlmapper requiring to load a .dtd locally when reading DrugBank RML
                os.chdir('data')
                # Copy functions jar file in the same folder where we run the rmlmapper to fix issues with finding the functions
                shutil.copyfile('../../IdsRmlFunctions.jar', 'IdsRmlFunctions.jar')
                rml_cmd = 'java -jar ' + get_base_dir('rmlmapper.jar') + ' -s ' + rdfSyntax + ' -f ../../functions_ids.ttl -m ' + rml_filename + ' -o ' + output_filepath
                os.system(rml_cmd)
                os.chdir('..')

            if processor.lower() == 'rmlstreamer':
                print('RMLStreamer not implemented yet')

            if processor.lower() == 'rocketrml':
                print('🚀 Running RocketRML with NodeJS to generate the RDF to ' + output_filepath)
                os.chdir('data')
                os.system('node ../../rocketrml.js -m ' + rml_filename + ' -o ' + output_filepath)
                os.chdir('..')

        # TO CHECK: concatenate produced nt files in 1 file f multiple
        os.system('cat output/*.nt > ' + dataset_id +'.nt')
        os.system('ls *.nt | grep -v ' + dataset_id + '.nt' + ' | xargs ls')
        if len(glob.glob('output/*.ttl')) > 1:
            raise Exception("More than 1 turtle output file found. If you produce multiple files as output, use the rdfSyntax ntriples, so the output can be concatenated in one graph per dataset") 

        if dryrun:
            update_endpoint = staging_endpoint
            update_ldp = staging_ldp
        else:
            update_endpoint = prod_endpoint
            update_ldp = prod_ldp
            
        dataset_graph = update_ldp + '/' + dataset_id
        metadata_graph = update_ldp + '/metadata-' + dataset_id
        metadata_slug = 'metadata-' + dataset_id

        # TODO: once RDF ouput files generated, if new version and not dry run: load to production Virtuoso
        # Otherwise load to staging Virtuoso and generate metadata
        # TODO: do we want 1 graph per dataset or 1 graph per file? I would say 1 per dataset to improve metadata generation per graph

        # Iterates the output file to upload them, should be only one turtle or ntriples file
        for output_file in glob.glob('output/*'):
            # Clear graph SPARQL query
            sparql = SPARQLWrapper(update_endpoint)
            sparql.setMethod(POST)
            # sparql.setHTTPAuth(BASIC) or DIGEST
            sparql.setCredentials(endpoint_user, endpoint_password)
            query = 'CLEAR GRAPH <' + dataset_graph + '>'
            print('🗑️ Clearing previous graph')
            sparql.setQuery(query)
            query_results = sparql.query()
            print(query_results.response.read())

            # TODO: also delete file from the DAV? It's overwritten automatically

            # Load the RDF output file after deleting previous graph
            print('📤 Loading the RDF ouput file ' + output_file)
            load_cmd = 'curl -u ' + endpoint_user + ':' + endpoint_password + ' --data-binary @' + output_file + ' -H "Accept: ' + output_file_mimetype + '" -H "Content-type: ' + output_file_mimetype + '" -H "Slug: ' + dataset_id + '" ' + dataset_graph
            os.system(load_cmd)

            # TODO: then run d2s metadata to get HCLS metadata and upload it in the dataset metadata graph
            # And compare new version metadata to the current version in production
            # generate_hcls_from_sparql(sparql_endpoint, rdf_distribution_uri, metadata_type, graph)
            g_metadata = generate_hcls_from_sparql(update_endpoint, dataset_graph, 'hcls', dataset_graph)
            output_metadata_file = 'output/metadata.ttl'
            g_metadata.serialize(destination=output_metadata_file, format='turtle', indent=4)

            print('📤 Loading the metadata file ' + output_file)
            load_metadata_cmd = 'curl -u ' + endpoint_user + ':' + endpoint_password + ' --data-binary @' + output_metadata_file + ' -H "Accept: text/turtle" -H "Content-type: text/turtle" -H "Slug: ' + metadata_slug + '" ' + metadata_graph
            os.system(load_metadata_cmd)
            


        # try:
        #     insert_results = insert_file_in_sparql_endpoint(file_path, sparql_endpoint, username, password, graph_uri, chunks_size)
        # except Exception as e:
        #     print('Error with INSERT of file: ' + file_path)
        #         print(e)
