#!/bin/bash

## Download sample TSV files from GitHub (OMOP CDM mappings, about 15M)
wget -N $downloadURL

## Unzip .zip files
unzip -o \*.zip

## Unzip .tar.gz files recursively in current dir
find . -name "*.tar.gz" -exec tar -xzvf {} \;

## RENAME EXTENSION (e.g.: txt in tsv)
# rename s/\.txt/.tsv/ *.txt

## Convert TSV to CSV for RMLStreamer
# sed -e 's/"/\\"/g' -e 's/\t/","/g' -e 's/^/"/' -e 's/$/"/'  -e 's/\r//' $dataset_id.tsv > $dataset_id.csv
