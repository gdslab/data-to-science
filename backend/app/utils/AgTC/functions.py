import yaml
import os
import errno
import pandas as pd


def get_yml_item_value(file, item_input):
    
    '''
    Function that opens the yaml file and returns the value that the item has.
    '''

    # transform the argument values into lowcase or uppercase
    file = file.lower()
    item_input = item_input.upper()

    with open(file, 'r') as file:

        configuration = yaml.full_load(file)

        for item, value in configuration.items():

            if item == item_input:
                value_output = value

                return value_output


def csv_file_to_df(file, item_input):
    
    '''
    Function that reads a csv file using config file that it name and path location is declared in a YAML config file.
    '''
    
    # get the path of the template folder from the YAML config file
    values_template_input = get_yml_item_value(file, item_input).values()

    if any(s.startswith('./') and s.endswith('/') for s in values_template_input):

        if any(s.endswith('.csv') for s in values_template_input):
            
            if any(os.path.isdir(s) for s in values_template_input):

                for value in values_template_input:

                    if os.path.isdir(value):

                        folder_path = value

                    else:

                        file_name = value

                name_file_read = folder_path + file_name

                # read the base template
                base_template = pd.read_csv(name_file_read)

                # transform column names into lowcase to make them case insensitive
                base_template.columns = base_template.columns.str.lower()

                return base_template
            
            else:
                
                path_value = [s for s in values_template_input if './' in s]
                
                print('ERROR! = The directory' , path_value, 'does not exists!')

        else:
            
            print('ERROR! = File name does not have .CSV extension!')

    else:

        print('ERROR! = Path should be like: ./folder/')


def matching_elements_two_lists(first_list, second_list):
    
    '''
    Function that compares two lists and returns the elements that exist in both of them.
    '''

    # compare the template colums vs subset columns from config file and return NOT matches
    not_matching_elements = list(set(first_list).difference(second_list))

    if len(not_matching_elements) > 0:

        print('ATTENTION! The following columns do not exist in the data frame:', not_matching_elements)

    # Remove 'columns' form the list that does no exist in the template
    return [element for element in first_list if element not in not_matching_elements]


def create_new_template(config_file_name, item_TEMPLATE_INPUT, item_COLUMNS_TEMPLATE, item_NEW_COLUMNS,
                  item_SAMPLES_PER_PLOT, item_SAMPLE_IDENTIFIER, item_TEMPLATE_OUTPUT):
    
    '''
    Function that creates a template file using information from the config.yml file.
    '''

    ## get base template using the csv_file_to_df() function
    base_template = csv_file_to_df(config_file_name, item_TEMPLATE_INPUT)

    # get the columns to select from template
    template_columns = get_yml_item_value(config_file_name, item_COLUMNS_TEMPLATE)
    template_columns_lower = [s.lower().replace(' ', '') for s in template_columns]

    first_list = template_columns_lower

    # names of columns from the template into a list
    second_list = base_template.columns.tolist()

    # get a list of columns that exists in bot the list of config file and the template
    columns_in_template = matching_elements_two_lists(first_list, second_list)

    # subset of the columns that are indicated in the config file
    base_template_subset = base_template[columns_in_template]

    # new colmns to add to the template
    new_columns = get_yml_item_value(config_file_name, item_NEW_COLUMNS)

    # add the new columns and rows to the template dataframe
    number = len(base_template_subset.columns)  # it will be used to get the dataframe position of new columns
    for key_column in new_columns:
        base_template_subset.insert(number, key_column.lower(), new_columns.get(key_column))

        number += 1

    # create the rows for the number of measurements that are going to be taken from each row
    times_repeat_row = len([value for value in get_yml_item_value(config_file_name, item_SAMPLES_PER_PLOT).values()][0])
    base_template_subset_rep = base_template_subset.loc[base_template_subset.index.repeat(times_repeat_row)]

    # get the rows to select from template
    sample_name = [value for value in get_yml_item_value(config_file_name, item_SAMPLES_PER_PLOT).values()][0]

    # columns_row = int(config.get('NEW_FILE_CONFIG', 'columnsPerRow'))
    name_column_sample_name = [value for value in get_yml_item_value(config_file_name, item_SAMPLES_PER_PLOT).keys()][
        0].lower()
    base_template_subset_rep[name_column_sample_name] = sample_name * int(
        len(base_template_subset_rep) / len(sample_name))

    # move the'Sample_ID' column to the second position of the data frame
    col = base_template_subset_rep.pop(name_column_sample_name)
    base_template_subset_rep.insert(1, col.name, col)

    # get the column names from the config file and make them lower case to create the id sample
    list_columns_id = [x.lower() for x in
                       [value for value in get_yml_item_value(config_file_name, item_SAMPLE_IDENTIFIER).values()][0]]

    first_list = list_columns_id

    # names of columns from the database into a list
    second_list = base_template_subset_rep.columns.tolist()

    # review if the columns to create the id exist in the data frame
    list_columns_id_select = matching_elements_two_lists(first_list, second_list)

    # get the name of the new column to create from the config file
    name_column_id = [value for value in get_yml_item_value(config_file_name, item_SAMPLE_IDENTIFIER).keys()][0].lower()

    # create the new column as id identifier for the sample and insert the id values
    ##base_template_subset_rep[name_column_id] = base_template_subset_rep[list_columns_id_select].astype(str).add('_').sum(axis = 1)
    base_template_subset_rep[name_column_id] = base_template_subset_rep[list_columns_id_select].astype(str).agg(
        '_'.join, axis=1)

    # move the'id_plot' column to the fist position of the data frame
    col = base_template_subset_rep.pop(name_column_id)
    base_template_subset_rep.insert(0, col.name, col)

    # reset dataframe index
    base_template_subset_rep = base_template_subset_rep.reset_index(drop=True)

    # get the column names from the config file and make them lower case to create the file name
    list_columns_fileName = get_yml_item_value(config_file_name, item_TEMPLATE_OUTPUT)
    list_columns_fileName_lower = [s.lower().replace(' ', '') for s in list_columns_fileName]

    first_list = list_columns_fileName_lower

    # names of columns from the database into a list
    second_list = base_template_subset_rep.columns.tolist()

    # review if the columns to create the file name exist in the data frame
    list_columns_fileName_select = matching_elements_two_lists(first_list, second_list)

    # create the string for the output file name
    output_file_name = base_template_subset_rep[list_columns_fileName_select].astype(str).add('_').sum(axis=1).unique()[
                           0][:-1]
    final_output_file_name = './output/' + output_file_name + '.csv'
    final_output_file_name = final_output_file_name.replace(' ', '-')
    final_output_file_name

    # create the folder where the output file will be stored
    try:
        os.makedirs('output')

    except OSError as e:

        if e.errno != errno.EEXIST:
            raise

    base_template_subset_rep.to_csv(final_output_file_name, index=False)

    return print('File ' + final_output_file_name + ' created successfully!')