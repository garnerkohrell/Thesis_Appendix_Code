
import os,shutil
import pandas as pd

def find_rotations(per_dir):
    '''
    Finds all crops in each hillslope .man file. The crops are appended to a separate list
    for each hillslope which can be interpreted as a crop rotation. Specific years are 
    not known but also not necessary to know for downstream analysis
    
    Returns dataframe with two columns for IDs and rotations in string format
    '''
    
    # Create lists for appending rotations and IDs from all hillslopes
    ID_lst = []
    OFE_lst = []
    
    # Loop through all management files in runs_dir
    for file in os.listdir(per_dir):
        if file.endswith('.man') and file.startswith('p'):

            #open file for reading
            with open(str(per_dir + file)) as f:

                #read lines 
                lines = f.readlines()

                OFE_line = lines[6]

                OFE_lst.append(OFE_line[0])
            
            #Append IDs to a list 
            ID_lst.append(file[:-4])

    #create dataframe of hillslope IDs and the respective rotations
    HS_OFEs = pd.DataFrame({'ID':ID_lst,'OFE':OFE_lst})
    
    return HS_OFEs


##### Example for Goodhue watershed ######

#Hillslopes with only corn in rotation, perennial integration must
#only use alfalfa-corn in these hillslopes
corn_lst = ['p8','p66','p142','p181','p250','p266']

#hillslopes selected for IWG implementation in GO1 watershed
kernza_lst = ['p27','p118']

#define watershed
wshed = 'GO1'

#source directory for manually created p20 perennial scenarios.
per_dir = 'C:/Users/Garner/Soil_Erosion_Project/WEPP_PRWs/{}/Management_Edits/Perennial/'.format(wshed)
HS_info = find_rotations(per_dir)


#loop through columns in HS_info
for ID, OFE in zip(HS_info['ID'], HS_info['OFE']):

    #check if hillslope ID is in corn list
    if ID in corn_lst:

        #define path to source corn soy OFE file
        source_path = str(per_dir + 'corn_alf_{}ofe.man'.format(OFE))

        #define destination path 
        dest_path = str(per_dir + ID + '.man')

        #replace DEP row crop file with alfalfa-corn file
        shutil.copy(source_path, dest_path)

    #check if hillslope ID is in IWG list
    elif ID in kernza_lst:
        #define path to source corn soy OFE file
        source_path = str(per_dir + 'IWG_{}ofe.man'.format(OFE))

        #define destination path 
        dest_path = str(per_dir + ID + '.man')

        #replace DEP row crop file with IWG file
        shutil.copy(source_path, dest_path)

    else:

        # "else:" does not refer to all other hillslopes in the
        # WEPP project directories. The aflafla-corn-soy files
        # in the p20 scenarios were created manually for the 
        # pre-selected hillslopes, so "else:" is selecting from
        # these files, which are in a separate directory along with
        # the IWG files.
        
        #define path to source corn soy OFE file
        source_path = str(per_dir + 'corn_soy_alf_{}ofe.man'.format(OFE))

        #define destination path 
        dest_path = str(per_dir + ID + '.man')

        #replace DEP row crop file with alfalfa-corn-soy file
        shutil.copy(source_path, dest_path)

