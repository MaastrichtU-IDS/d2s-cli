import os
import re
import click
import pathlib
import urllib.parse
from datetime import date, datetime
import pkg_resources
from rdflib import Graph, Literal, RDF, XSD, URIRef, Namespace
from rdflib.namespace import RDFS, DC, DCTERMS, VOID, SKOS, DCAT, PROV, FOAF
from SPARQLWrapper import SPARQLWrapper, TURTLE, POST, JSON, JSONLD

DATASET_NAMESPACE = 'https://w3id.org/d2s/dataset/'

SCHEMA = Namespace("http://schema.org/")
DCTYPES = Namespace("http://purl.org/dc/dcmitype/")
PAV = Namespace("http://purl.org/pav/")
IDOT = Namespace("http://identifiers.org/idot/")
D2S = Namespace("https://w3id.org/d2s/vocab/")


def generate_shacl(rdf_file):
    """Create a new dataset from provided metadata JSON object"""
    g = Graph()
    g.parse(rdf_file)


    g.bind("foaf", FOAF)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("skos", SKOS)
    g.bind("schema", SCHEMA)
    g.bind("dcat", DCAT)
    g.bind("prov", PROV)
    g.bind("dc", DC)
    g.bind("dctypes", DCTYPES)
    g.bind("dcterms", DCTERMS)
    g.bind("pav", PAV)
    g.bind("idot", IDOT)
    g.bind("void", VOID)
    g.bind("d2s", D2S)
    # g.bind("owl", OWL)


    # # Summary
    # summary_uri = URIRef(DATASET_NAMESPACE + metadata['dataset_id'])
    # g.add((summary_uri, RDF.type, DCTYPES['Dataset']))
    # g.add((summary_uri, RDFS['label'], Literal(metadata['name'] + ' dataset summary')))
    # g.add((summary_uri, DC.identifier, Literal(metadata['dataset_id'])))
    # g.add((summary_uri, DC.description, Literal(metadata['description'])))
    # g.add((summary_uri, DCTERMS.title, Literal(metadata['name'])))
    # g.add((summary_uri, IDOT['preferredPrefix'], Literal(metadata['dataset_id'])))
    # g.add((summary_uri, DCTERMS.license, URIRef(metadata['license'])))
    # g.add((summary_uri, FOAF['page'], URIRef(metadata['homepage'])))
    # # g.add((summary_uri, DCAT['accessURL'], URIRef(metadata['accessURL'])))
    # g.add((summary_uri, DCTERMS.references, URIRef(metadata['references'])))
    # g.add((summary_uri, DCAT['keyword'], Literal(metadata['keyword'])))
    # g.add((summary_uri, VOID.sparqlEndpoint, URIRef(metadata['sparqlEndpoint'])))

    # # Publisher
    # publisher_uri = URIRef(DATASET_NAMESPACE + urllib.parse.quote(metadata['publisher_name']))
    # g.add((publisher_uri, RDF.type, DCTERMS.Agent))
    # g.add((publisher_uri, FOAF['name'], Literal(metadata['publisher_name'])))
    # g.add((publisher_uri, FOAF['page'], Literal(metadata['publisher_url'])))
    # g.add((summary_uri, DCTERMS.publisher, publisher_uri))

    # # Version
    # version = '1'
    # version_uri = URIRef(DATASET_NAMESPACE + metadata['dataset_id'] + '/version/' + version)
    # g.add((version_uri, RDF.type, DCTYPES['Dataset']))
    # g.add((version_uri, RDFS['label'], Literal(metadata['name'] + ' dataset version')))
    # g.add((version_uri, DCTERMS.isVersionOf, summary_uri))
    # g.add((version_uri, PAV['version'], Literal(version)))

    # # Source distribution
    # source_uri = URIRef(DATASET_NAMESPACE + metadata['dataset_id'] + '/version/' + version + '/distribution/source')
    # g.add((source_uri, RDF.type, DCAT['Distribution']))
    # g.add((source_uri, RDFS['label'], Literal(metadata['name'] + ' source distribution')))
    # g.add((source_uri, DCTERMS['format'], Literal(metadata['format'])))
    # g.add((source_uri, DCAT['downloadURL'], Literal(metadata['downloadURL'])))
    # # g.add((source_uri, DCTERMS.issued, Literal(str(date.today()),datatype=XSD.date)))

    # # RDF Distribution description
    # rdf_uri_string = DATASET_NAMESPACE + metadata['dataset_id'] + '/version/' + version + '/distribution/rdf'
    # rdf_uri = URIRef(rdf_uri_string)
    # g.add((rdf_uri, RDF.type, DCAT['Distribution']))
    # g.add((rdf_uri, RDF.type, VOID.Dataset))
    # g.add((rdf_uri, RDFS['label'], Literal(metadata['name'] + ' RDF distribution')))
    # g.add((rdf_uri, DCTERMS.source, source_uri))
    # g.add((rdf_uri, DCTERMS.created, Literal(date.today(),datatype=XSD.date)))

    # g.add((version_uri, DCAT['distribution'], source_uri))
    # g.add((version_uri, DCAT['distribution'], rdf_uri))

    # # print(g.serialize(format='turtle'))

    # if metadata['sparqlEndpoint']:
    #     g.add((rdf_uri, DCAT['accessURL'], Literal(metadata['sparqlEndpoint'])))
    #     # g = generate_hcls_from_sparql(metadata['sparqlEndpoint'], rdf_uri_string, g)
    
    return g

