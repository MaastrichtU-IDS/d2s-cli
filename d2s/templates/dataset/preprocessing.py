import os
import glob
import pandas as pd 
import os

os.chdir('output')

# This is an example to edit a CSV file, and perform text processing
# To use the right types before RML conversion
# Change it as you please
# Note: could be done more efficiently using pandas

# Add a column based on another column value
# Here we replace spaces with - and lowercase the string to use it as ID
def add_column_with_pandas():
    df = pd.read_csv("my-file.csv")
    # Create the "id" column based on "column1" value
    df["id"] = df["column1"].apply (lambda row: row.replace(' ','-').lower())

    df.to_csv("my-file-processed.csv", index=False)


def convert_tsv_to_csv(tsv_file):
    csv_table=pd.read_table(tsv_file,sep='\t')
    csv_table.to_csv(tsv_file[:-4] + '.csv',index=False)


def rename_txt_to_tsv():
    # os.chdir('data')
    listing = glob.glob('*.txt')
    for filename in listing:
        os.rename(filename, filename[:-4] + '.tsv')
