import os
import glob
from rdflib import Graph, Literal, RDF, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID, DCAT
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD
import requests
from dateutil.parser import parse as parsedate
import shutil
import stat
from urllib.parse import urlparse
import pandas as pd 
# import datetime
from datetime import datetime, timezone
# import pathlib
import re

from d2s.utils import init_d2s_java, get_base_dir, get_parse_format, get_yaml_config
from d2s.sparql_operations import insert_graph_in_sparql_endpoint, java_upload_files
from d2s.generate_metadata import generate_hcls_from_sparql

D2S = Namespace("https://w3id.org/d2s/vocab/")

def execute_script(script):
    """Small function to run bash scripts with python"""
    print('📇 Running the script: ' + script)
    if script.startswith('https://') or script.startswith('http://'):
        # Download script from URL
        script_filename = os.path.basename(urlparse(script).path)
        os.system('wget -qN ' + script)
        # os.system('chmod +x *.sh ')
        import stat
        st = os.stat(script_filename)
        os.chmod(script_filename, st.st_mode | stat.S_IEXEC)
        script_cmd = './' + script_filename
    elif script.endswith('.sh'):
        # Local shell script, first copy to data folder, then run
        shutil.copy('../' + script, script)
        # os.system('cp -f ../' + script + ' ' + script)
        # os.chmod(script, stat.S_IEXEC)
        script_cmd = './' + script
    else:
        # Directly provided a bash command
        script_cmd = script
    os.system(script_cmd)


def load_rdf_to_ldp(upload_file, upload_mimetype, ldp_url, ldp_slug, endpoint_user, endpoint_password):
    print('📤 Loading the RDF file ' + upload_file + ' to the graph ' + ldp_url + '/' + ldp_slug)
    load_cmd = 'curl -u ' + endpoint_user + ':' + endpoint_password + ' --data-binary @' + upload_file + ' -H "Accept: ' + upload_mimetype + '" -H "Content-type: ' + upload_mimetype + '" -H "Slug: ' + ldp_slug + '" ' + ldp_url
    print(load_cmd)
    os.system(load_cmd)


# TODO: unfinished example of a workflow to build entities and associations
# following SIO reificatedgraph patterns (hasAttribute)
def sio_builder_csv(filename, row):
    ## For large files:
    chunksize = 10000
    with pd.read_csv(filename, chunksize=chunksize) as reader:
        for chunk in reader:
            print(chunk)
            # TODO: create SioBuilder
            sioBuilder = {}
            # sioBuilder = SioBuilder(row['hgnc_id'])
            sioBuilder.subject(row['hgnc_id'])
            sioBuilder.addAttribute(
                value=row['symbol'], 
                type='sio:Symbol'
            )
            sioBuilder.addAssociation(
                subject=row['hgnc_id'],
                object=row['associated with'],
                predicate='sio:isAssociatedWith',
                supportedBy=row['pmid']
            )
            sioBuilder.to_rdf()


def process_datasets_metadata(input_file=None, dryrun=True, staging=True, sample=0, report=False, memory='4g', rmlstreamer_run=False):
    """Read a RDF metadata file with infos about datasets, check if the dataset exist in the project SPARQL endpoint
    Download the data if new"""

    # If no metadata file provided, we search for one in the current folder
    if not input_file:
        # Search for ttl metadata file
        file_list = glob.glob('*.ttl')
        if len(file_list) > 1:
            raise Exception("More than 1 metadata file have been found in the current folder: " + ', '.join(file_list)) 
        elif len(file_list) < 1:
            # Search for jsonld metadata file if no ttl
            jsonld_file_list = glob.glob('*.jsonld')
            if len(jsonld_file_list) > 1:
                raise Exception("More than 1 metadata file have been found in the current folder: " + ', '.join(jsonld_file_list)) 
            elif len(jsonld_file_list) < 1:
                raise Exception("No ttl or jsonld metadata file has been found in the current folder") 
            else:
                input_file = jsonld_file_list[0]
        else:
            input_file = file_list[0]
    print("🔎 Reading the metadata file " + input_file)

    os.makedirs('data/input', exist_ok=True)
    os.makedirs('output', exist_ok=True)


    # Retrieve the infos about files to download from the dataset metadata file
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
        if (download_files_uri, D2S.processedFilename, None) in g:
            download_file_list[i]['processedFilename'] = str(g.value(download_files_uri, D2S.processedFilename))
        i += 1

    # Retrieve the dataset URI and various params in the dataset metadata file
    if len(datasets_described) < 1:
        raise Exception("No dataset has been found in the metadata file") 
    elif len(datasets_described) > 1:
        raise Exception("More than 1 dataset has been found in the metadata file") 
    else:
        dataset_uri = datasets_described.pop()
    
    if (dataset_uri, DC.identifier, None) in g:
        dataset_id_cap = str(g.value(dataset_uri, DC.identifier))
        dataset_id = dataset_id_cap.lower()
    else:
        raise Exception("Could not find the dc:identifier property for the dataset in the metadata file") 

    if (dataset_uri, D2S.processor, None) in g:
        processor = str(g.value(dataset_uri, D2S.processor))
    else:
        processor = 'rmlmapper-java'

    if processor.lower() == 'rmlstreamer':
        if not rmlstreamer_run:
            print('📤 Copying mappings to the RMLStreamer.')
            # Make sure the YARRRML mappings on the DSRI RMLStreamer are up to date
            rmlstreamer_dataset_path = '/mnt/datasets/' + dataset_id_cap + '/'
            oc_cp_cmd = 'oc cp *.yarrr.yml $(oc get pod --selector app=flink --selector component=jobmanager --no-headers -o=custom-columns=NAME:.metadata.name):' + rmlstreamer_dataset_path
            os.system(oc_cp_cmd)
            oc_cp_cmd = 'oc cp *.jsonld $(oc get pod --selector app=flink --selector component=jobmanager --no-headers -o=custom-columns=NAME:.metadata.name):' + rmlstreamer_dataset_path
            os.system(oc_cp_cmd)
            oc_cp_cmd = 'oc cp prepare.sh $(oc get pod --selector app=flink --selector component=jobmanager --no-headers -o=custom-columns=NAME:.metadata.name):' + rmlstreamer_dataset_path
            os.system(oc_cp_cmd)
            # Run this same function directly in the RMLStreamer
            print('☁️  Running the process in the RMLStreamer.')
            run_d2s_cmd = '"cd ' + rmlstreamer_dataset_path + ' && d2s run --rmlstreamer"'
            rmlstreamer_cmd = 'oc exec $(oc get pod --selector app=flink --selector component=jobmanager --no-headers -o=custom-columns=NAME:.metadata.name) -- bash -c ' + run_d2s_cmd
            print(rmlstreamer_cmd)
            os.system(rmlstreamer_cmd)
            # return process_datasets_metadata(input_file, dryrun, sample, report, memory, True)
            return None


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

    if (dataset_uri, D2S.versionRegex, None) in g:
        versionRegex = str(g.value(dataset_uri, D2S.versionRegex))
    else:
        versionRegex = None

    prod_endpoint = get_yaml_config('production')['sparql-endpoint']
    prod_ldp = get_yaml_config('production')['virtuoso-ldp-url']
    staging_endpoint = get_yaml_config('staging')['sparql-endpoint']
    if 'virtuoso-ldp-url' in get_yaml_config('staging').keys():
        staging_ldp = get_yaml_config('staging')['virtuoso-ldp-url']
    endpoint_user = os.getenv('DBA_USER', 'dav')
    endpoint_password = os.getenv('DBA_PASSWORD')


    # TODO: Get lastUpdated date and version infos from the production endpoint
    # date_last_updated = None
    # if prod_endpoint:
    #     print('Querying the SPARQL endpoint ' + prod_endpoint + ' to retrieve version infos for the dataset ' + dataset_uri)
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
    #     sparql = SPARQLWrapper(prod_endpoint)
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

    print('\n🗃️  Checking files to download: \n')

    # Download if last modified date is later than last updated date (or if modified/updated date could not be fetched)
    # file_time = datetime.fromtimestamp(os.path.getmtime(dstFile))
    # if not date_last_modified or not date_last_updated or date_last_modified > date_last_updated:

    # Download file in the data subfolder
    os.chdir('data')
    skip_global_download = True
    # Check last modified date, then download and post process scripts defined for each file
    for ddl_file in download_file_list:
        ddl_url = ddl_file['downloadUrl']
        # # Extract filename from URI:
        # ddl_filename = os.path.basename(urlparse(ddl_url).path)
        processed_filename = ddl_file['processedFilename']
        
        if versionRegex:
            # TODO: Extract version, then increment it 
            # and check if new version available
            version_search = re.search(versionRegex, ddl_url, re.IGNORECASE)
            if version_search:
                file_version = version_search.group(1)
                print(file_version)
                

        skip_download = True

        # Check Last Modified date of the URL to download
        print('🔎 Checking Last Modified date of file at ' + ddl_url)
        r = requests.head(ddl_url)
        if 'last-modified' in r.headers.keys():
            url_last_modified = r.headers['last-modified']
            ddl_file['lastModified'] = parsedate(url_last_modified)
            print('📅 File to download last modified on ' + url_last_modified)

        ## Check if last date updated from SPARQL endpoint is older than the URL Last Modified date
        # if ddl_file['lastModified'] > date_last_updated:
        #     print('📥 According to Last Modified date, the remote file to download is newer than the existing local file (' + str(local_file_time) + '). Downloading it.')
        #     skip_download = False
        #     skip_global_download = False
        # elif os.path.exists(processed_filename):

        # Download only if processed file does not exist, is older than the file to ddl, 
        # or if the file to ddl has no LastModified date
        if os.path.exists(processed_filename):
            # If the file to download is newer than existing local file 
            if 'lastModified' in ddl_file.keys():
                local_file_time = datetime.fromtimestamp(os.path.getmtime(processed_filename), timezone.utc)
                if ddl_file['lastModified'] > local_file_time:
                    print('📥 According to Last Modified date, the remote file to download is newer than the existing local file (' + str(local_file_time) + '). Downloading it.')
                    skip_download = False
                    skip_global_download = False
                else: 
                    print('⏩️ According to Last Modified date, the remote file to download is not newer than the existing local file at data/' + processed_filename + ' (' + str(local_file_time) + '). Skipping download.')
            else:
                print('📥 No Last Modified date for this file. Downloading it.')
                skip_download = False
                skip_global_download = False
        else:
            print('📥 No existing local file for this file. Downloading it.')
            skip_download = False
            skip_global_download = False

        # Run the download and preprocess scripts if download required
        if not skip_download:
            if 'downloadScript' in ddl_file:
                execute_script(ddl_file['downloadScript'])
            elif 'downloadUrl' in ddl_file:
                os.system("wget -qN " + ddl_url)
            if 'postProcessScript' in ddl_file:
                execute_script(ddl_file['postProcessScript'])
        print('')

    # Run download and post process scripts defined for the whole dataset if at least one file has been downloaded
    if not skip_global_download:
        if (dataset_uri, D2S.downloadScript, None) in g:
            execute_script(str(g.value(dataset_uri, D2S.downloadScript)))
        if (dataset_uri, D2S.postProcessScript, None) in g:
            execute_script(str(g.value(dataset_uri, D2S.postProcessScript)))
    else:
        print('⏩️ No dataset has been downloaded, skipping global post processing.')

    print('')

    # TODO: Create a HTML report about input CSV data with Datapane
    # import datapane as dp
    # if report:
    #     print('📋 Produce HTML report for CSV files in data folder with datapane')
    #     for ddl_file in download_file_list:
    #         processed_filename = ddl_file['processedFilename']
    #         if processed_filename.endswith('.csv'):
    #             df = pd.read_csv(processed_filename)
    #             dp.Report(
    #                 dp.Text('## ' + processed_filename),
    #                 dp.DataTable(df)
    #             ).save(path='report-' + processed_filename.replace('.csv', '') + '.html', 
    #                 open=True, formatting=dp.ReportFormatting(width=dp.ReportWidth.FULL))


    ## Automatically unzip files, to be done ad-hoc in prepare.sh?
    # print("""find . -name "*.tar.gz" -exec tar -xzvf {} \;""")
    # if len(glob.glob('*.zip')) > 0:
    #     print('Unzipping .zip files ' + ', '.join(glob.glob('*.zip')))
    #     os.system('unzip -o "*.zip"')
    # if len(glob.glob('*.tar.gz')) > 0:
    #     print('Unzipping .tar.gz files ' + ', '.join(glob.glob('*.tar.gz')))
    #     os.system("""find . -name "*.tar.gz" -exec tar -xzvf {} \;""")
    # if len(glob.glob('*.gz')) > 0:
    #     print('Unzipping .gz files ' + ', '.join(glob.glob('*.gz')))
    #     os.system('gzip -f -d *.gz')

    # Check for .tsv .txt and .tab then convert to CSV (required for most RML engines)
    # tab_files = glob.glob('*.tsv') + glob.glob('*.txt') + glob.glob('*.tab')
    # for tsv_file in tab_files:
    #     csv_file = tsv_file[:-4] + '.csv'
    #     print('📄 Converting TSV file '+ tsv_file + ' to CSV ' + csv_file)
    #     try:
    #         tsv_to_csv_cmd = """sed -e 's/"//g' -e 's/\\t/","/g' -e 's/^/"/' -e 's/$/"/' -e 's/\\r//' """ + tsv_file + """ > """ + csv_file
    #         os.system(tsv_to_csv_cmd)
    #         # csv_table=pd.read_table(tsv_file,sep='\t')
    #         # csv_table.to_csv(csv_file, index=False)
    #     except Exception as e:
    #         print('Could not convert the file ' + tsv_file + ' to CSV')


    # Create sample for CSV files
    if sample > 0:
        for csv_file in glob.glob('*.csv'):
            print('✂️ Creating a sample file with ' + str(sample) + ' lines for ' + csv_file)
            # if not os.path.exists(filename):
            full_csv_file = csv_file + '.full'
            shutil.copy(csv_file, full_csv_file)
            sample_cmd = 'head -n ' + str(sample) + ' ' + full_csv_file + ' > ' + csv_file
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
            print('☕️ Running the RML mapper with java to generate the RDF to ' + output_filepath.replace('../', ''))
            init_d2s_java('rmlmapper')
            # Change dir to fix issue with rmlmapper requiring to load a .dtd locally when reading DrugBank RML
            os.chdir('data')
            # Copy functions jar file in the same folder where we run the rmlmapper to fix issues with finding the functions
            shutil.copy('../../IdsRmlFunctions.jar', 'IdsRmlFunctions.jar')
            if 'memory' in get_yaml_config('resources').keys():
                memory = get_yaml_config('resources')['memory']
            java_opts = "-Xms" + memory + " -Xmx" + memory
            rml_cmd = 'java ' + java_opts + ' -jar ' + get_base_dir('rmlmapper.jar') + ' -s ' + rdfSyntax + ' -f ../../functions_ids.ttl -m ' + rml_filename + ' -o ' + output_filepath
            os.system(rml_cmd)
            os.chdir('..')

        # if processor.lower() == 'rmlstreamer':
        if rmlstreamer_run:
            print('🐿️ Running the RMLStreamer')
            rmlstreamer_dataset_path = os.getcwd()
            parallel_cores = str(get_yaml_config('resources')['flink-cores'])
            os.chdir('data')
            rmlstreamer_cmd = '/opt/flink/bin/flink run -p ' + parallel_cores + ' -c io.rml.framework.Main /opt/flink/lib/RMLStreamer.jar toFile -m ' + rmlstreamer_dataset_path + '/data/' + rml_filename + ' -o ' + rmlstreamer_dataset_path + '/output/output-' + dataset_id + '.nt --job-name "RMLStreamer Bio2KG - ' + dataset_id + '"'
            os.system(rmlstreamer_cmd)
            os.chdir('..')
            

        if processor.lower() == 'rocketrml':
            print('🚀 Running RocketRML with NodeJS to generate the RDF to ' + output_filepath)
            os.chdir('data')
            nodejs_memory='2048'
            if 'nodejs-memory' in get_yaml_config('resources').keys():
                nodejs_memory = str(get_yaml_config('resources')['nodejs-memory'])
            # Try to increase node memory to 2G for large files with --max_old_space_size=2048
            os.system(f'node --max_old_space_size={nodejs_memory} ../../rocketrml.js -m {rml_filename} -o {output_filepath}')
            os.chdir('..')

    # TO CHECK: concatenate produced nt files in 1 file if multiple files
    list_ntriples = glob.glob('output/*.nt')
    if len(list_ntriples) > 1:
        print('🗃️ Concatenate ntriples files: ' + ', '.join(list_ntriples))
        output_filepath = 'output/' + dataset_id +'.nt'
        if os.path.exists(output_filepath):
            os.system('rm ' + output_filepath)
        os.system('cat output/*.nt > ' + output_filepath)
        os.system('ls output/*.nt | grep -v ' + output_filepath + ' | xargs rm')
        # os.system('ls *.nt | grep -v ' + dataset_id + '.nt' + ' | parallel rm')

    if dryrun:
        print('✅ Dry run completed: RDF generated, but not published')
    else:
        if staging:
            print('🧪 Publishing to staging endpoint')
            update_endpoint = staging_endpoint
            update_ldp = staging_ldp
        else:
            print('📰 Publishing the processed file to the production endpoint')
            update_endpoint = prod_endpoint
            update_ldp = prod_ldp
            raise Exception("Publishing not implemented yet") 
            

        if (dataset_uri, D2S.graph, None) in g:
            dataset_graph = str(g.value(dataset_uri, D2S.graph))
        else:
            dataset_graph = update_ldp + '/' + dataset_id
        output_metadata_file = 'output/metadata.ttl'
        metadata_graph = update_ldp + '/metadata-' + dataset_id
        metadata_slug = 'metadata-' + dataset_id

        if os.path.exists(output_metadata_file):
            os.remove(output_metadata_file)
            # os.system('rm ' + output_metadata_file)
        if len(glob.glob('output/*.ttl')) > 1:
            raise Exception("More than 1 turtle output file found. If you produce multiple files as output, use the rdfSyntax ntriples, so the output can be concatenated in one graph per dataset") 

        # TODO: once RDF ouput files generated, if new version and not dry run: load to production Virtuoso
        # Otherwise load to staging Virtuoso and generate metadata
        # TODO: do we want 1 graph per dataset or 1 graph per file? I would say 1 per dataset to improve metadata generation per graph
        
        # print(update_endpoint)
        # print(endpoint_user)
        # print(endpoint_password)


        # Iterates the output file to upload them to the Virtuoso LDP triplestore
        # Should be only one turtle or ntriples file because the LDP create 1 graph per file
        for output_file in glob.glob('output/*'):
            # Load the RDF output file to the Virtuoso LDP DAV
            # Existing file is overwritten automatically at upload
            load_rdf_to_ldp(output_file, output_file_mimetype, update_ldp, dataset_id, endpoint_user, endpoint_password)
            
            # TODO: then run d2s metadata to get HCLS metadata and upload it in the dataset metadata graph
            # And compare new version metadata to the current version in production
            # generate_hcls_from_sparql(sparql_endpoint, rdf_distribution_uri, metadata_type, graph)
            g_metadata = generate_hcls_from_sparql(update_endpoint, dataset_graph, 'hcls', dataset_graph)
            
            g_metadata.serialize(destination=output_metadata_file, format='turtle', indent=4)

            load_rdf_to_ldp(output_metadata_file, "Accept: text/turtle", update_ldp, metadata_slug, endpoint_user, endpoint_password)
            
            # TODO: handle dataset_version
            
            print('✅ Dataset processed and loaded to ' + update_endpoint)


            # Clear graph SPARQL query
            # try:
            #     sparql = SPARQLWrapper(update_endpoint)
            #     sparql.setMethod(POST)
            #     # sparql.setHTTPAuth(BASIC) or DIGEST
            #     sparql.setCredentials(endpoint_user, endpoint_password)
            #     query = 'CLEAR GRAPH <' + dataset_graph + '>'
            #     print('🗑️ Clearing previous graph')
            #     sparql.setQuery(query)
            #     query_results = sparql.query()
            #     print(query_results.response.read())
            # except:
            #     print('Could not delete the graph (probably it does not exist)')

    # try:
    #     insert_results = insert_file_in_sparql_endpoint(file_path, sparql_endpoint, username, password, graph_uri, chunks_size)
    # except Exception as e:
    #     print('Error with INSERT of file: ' + file_path)
    #         print(e)
