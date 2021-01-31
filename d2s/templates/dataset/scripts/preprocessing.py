import os
import glob
import csv
import pandas as pd 

# This is an example to edit a CSV file, and perform text processing
# To use the right types before RML conversion
# Change it as you please
# Note: could be done more efficiently using pandas

# Define which columns in which files to preprocess
preprocess_files = [{'name': 'domain_pair_concept_counts', 'col': [1,2]},
                { 'name': 'domain_concept_counts', 'col': [1] },
                { 'name': 'concepts', 'col': [2] } ]

for file_to_process in preprocess_files:
    # Set the right BioLink types in col2 domain_id
    with open(file_to_process['name'] + '.csv', 'r') as input_file, open(file_to_process['name'] + '_curated.csv','w',newline='') as output_file:
        reader = csv.reader(input_file, delimiter=',')
        writer = csv.writer(output_file, delimiter=',')
        # Iterate over each row to make the changes
        for row in reader:
            # Only make changes to defined columns
            for col in file_to_process['col']:
                # Do the change on the row columns
                row[col] = row[col].replace('Condition','Disease')
                row[col] = row[col].replace('Observation','ActivityAndBehavior') # Not sure
                row[col] = row[col].replace('Measurement','QuantityValue') # Not sure (has_numeric_value, has_unit)
                row[col] = row[col].replace('Procedure','Procedure')
                row[col] = row[col].replace('Device','Device')
                row[col] = row[col].replace('Gender','PopulationOfIndividualOrganisms') # bl:BiologicalSex is an Attribute
                row[col] = row[col].replace('Race','PopulationOfIndividualOrganisms')
                row[col] = row[col].replace('Ethnicity','PopulationOfIndividualOrganisms')
                row[col] = row[col].replace('Relationship','Phenomenon')

            writer.writerow(row)

# Use Pandas, load file in memory
def convert_tsv_to_csv(tsv_file):
    csv_table=pd.read_table(tsv_file,sep='\t')
    csv_table.to_csv(tsv_file[:-4] + '.csv',index=False)

def rename_txt_to_tsv():
    # os.chdir('data')
    listing = glob.glob('*.txt')
    for filename in listing:
        os.rename(filename, filename[:-4] + '.tsv')