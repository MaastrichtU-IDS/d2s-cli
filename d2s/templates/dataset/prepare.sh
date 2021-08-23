#!/bin/bash

## Download file
# wget -N $downloadURL

## Unzip .zip files
unzip -o \*.zip

## Unzip .tar.gz files recursively in current dir
find . -name "*.tar.gz" -exec tar -xzvf {} \;

## Unzip .gz files
gzip -d *.gz

## RENAME EXTENSION (e.g.: txt in tsv)
# rename s/\.txt/.tsv/ *.txt

## Convert TSV to CSV for RMLStreamer
sed -e 's/"/\\"/g' -e 's/\t/","/g' -e 's/^/"/' -e 's/$/"/'  -e 's/\r//' $dataset_id.tsv > $dataset_id.csv

## Add header to the columns if missing
# sed -i '1s/^/column1,column2,column3\n/' $dataset_id.csv

## Convert xlsx to CSV (require python setup)
# pip install xlsx2csv
# xlsx2csv my-file.xlsx my-file.csv