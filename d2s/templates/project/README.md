# Mappings to build a knowledge graph


The [`d2s` CLI](https://github.com/MaastrichtU-IDS/d2s-cli) allows you to easily generate new dataset mappings in your repository, with sample mappings and prefilled metadata (you will be asked some questions)

## Install `d2s`

Install the `d2s` python command line interface:

```bash
pip3 install git+https://github.com/MaastrichtU-IDS/d2s-cli.git@develop
```

## Initialize a project

To initialize a project with `d2s`, go to the project 

```bash
mkdir my-project
cd my-project
```

Initialize the folder, and provide this git repository URL, this will clone the repository in the initialized folder, and create all necessary files:

```bash
d2s init
```

## Datasets mappings

All files required to map and convert a dataset to a RDF knowledge graph

[RML mappings](https://rml.io), bash download scripts, python preprocessing scripts and a `README.md` are stored for each dataset in a different folder in the `datasets` folder.

### Create new dataset mappings

Generate a new dataset in the `datasets` folder:

```bash
d2s new dataset
```

You will be prompted a few questions to fill metadata about the dataset (description, download URL, license, publication, etc...)

> See **[d2s.semanticscience.org](https://d2s.semanticscience.org/)** for a more detailed documentation on how to use the `d2s` client to quickly create new RDF knowledge graphs from structured data, and deploy services.
>
> `d2s` is a work in progress, feel free to [provide feedback](https://github.com/MaastrichtU-IDS/d2s-cli/issues) to improve it.

---

## Publish the generated RDF

The generated RDF can easily be publicly published at the Institute of Data Science at Maastricht University.

See the [`d2s` documentation](https://d2s.semanticscience.org/docs/store-rdf) for more instructions to publicly publish a RDF knowledge graph.

2 popular options are:

* IDS [Ontotext GraphDB](https://graphdb.ontotext.com/) triplestore at https://graphdb.dumontierlab.com
  * See [graphdb-docker](https://github.com/Ontotext-AD/graphdb-docker) to deploy GraphDB with docker
* [OpenLink Virtuoso](https://virtuoso.openlinksw.com/) triplestore
  * See below to deploy a Virtuoso triplestore locally or on IDS servers.

### Deploy a Virtuoso triplestore

The [Virtuoso triplestore](https://hub.docker.com/r/tenforce/virtuoso) deployment is defined in the `docker-compose.yml`. 

We use [nginx-proxy](https://github.com/nginx-proxy/nginx-proxy) with [nip.io](https://nip.io) to route the Virtuoso triplestore to a publicly available URL on IDS servers.

1. Change the `dba` user password in the `.env` file (default to `VIRTUOSO_PASSWORD=dba`)
2. Run a Virtuoso triplestore container:

```bash
docker-compose up -d
```

> Database files stored in `/data/bio2rdf5/virtuoso` on your machine. The path can be changed in the `docker-compose.yml`

3. Manage the triplestore data:

**Bulk load** `.nq` files in `/data/bio2rdf5/virtuoso/dumps` (on the server):

```bash
docker exec -it bio2rdf5-virtuoso isql-v -U dba -P dba exec="ld_dir('/data/dumps', '*.nq', 'http://bio2rdf.org'); rdf_loader_run();"
```

**Check** bulk load in process:

```bash
docker exec -it bio2rdf5-virtuoso isql-v -U dba -P dba exec="select * from DB.DBA.load_list;"
```

**Reset** the triplestore:

```bash
docker exec -it bio2rdf5-virtuoso isql-v -U dba -P dba exec="RDF_GLOBAL_RESET ();"
```

**Configure Virtuoso**:

* Instructions to **enable CORS** for the SPARQL endpoint via the admin UI: http://vos.openlinksw.com/owiki/wiki/VOS/VirtTipsAndTricksCORsEnableSPARQLURLs

* Instructions to enable the **faceted browser** and **full text search** via the admin UI: http://vos.openlinksw.com/owiki/wiki/VOS/VirtFacetBrowserInstallConfig