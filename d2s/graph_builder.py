from rdflib import ConjunctiveGraph, URIRef, RDF, RDFS


class GraphBuilder(ConjunctiveGraph):
    # identifier is the default graph URI

    def __init__(self,
            *args,
            default_graph: URIRef = None,
            dataset_uri : str = 'https://w3id.org/d2s/dataset',
            dataset_title: str, 
            dataset_description: str,
            dataset_version: str ="0.1.0",
            dataset_keywords=[],
            dataset_page=None,
            dataset_references=[],
            **kwargs
        ) -> None:
        """
        Constructor of the Graph builder
        """
        if not dataset_title: raise Exception("Provide the title of the dataset")
        if not dataset_description: raise Exception("Provide the description of the dataset")
        self.dataset_title=dataset_title
        self.dataset_description=dataset_description
        self.dataset_version=dataset_version
        self.dataset_keywords=dataset_keywords
        self.dataset_page=dataset_page
        self.dataset_references=dataset_references
        if default_graph: 
            self.identifier = default_graph
        
        # super().__init__(*args, **kwargs)
        super(self).__init__(*args, **kwargs)


    def getMetadata(self):
        g = ConjunctiveGraph(identifier=URIRef(''))
        metadata_graph = URIRef(f"{self.dataset_uri}/metadata")
        subj = URIRef(f"{self.dataset_uri}")
        g.add((subj, RDF.type, URIRef('http://purl.org/dc/dcmitype/Dataset'), metadata_graph))
