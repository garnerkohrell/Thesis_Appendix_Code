from prep_wepp_inputs.CMIP5_to_CLI.download_ftp import extract_netcdf
from prep_wepp_inputs.CMIP5_to_CLI.netcdf_to_GDS import netcdf_to_GDS
from prep_wepp_inputs.CMIP5_to_CLI.Generate_calibrated_cli_files import gen_cli_file
from prep_wepp_inputs.Prep_sol_slp_man_files import prep_input_files
from prep_wepp_inputs.Assign_Cli_Files import assign_cli_files

def run_prep(HUC12_path, ftp_lst, HUC12_name, proj_num, obs_cli_xlsx,\
                 wshed_ID, LOCA_labs, BCCA_labs, man_labs, periods):
    '''
    Combines functions from scripts in CMIP5_to_CLI folder to produce fully calibrated 
    .cli files from the raw netCDF inputs.

    HUC12_path = path to main HUC12 directory (watershed name/ID)

    ftp_ID = ID of ftp download from  The first ID in the list is always for 
    the BCCA downscaling method and the second is for the LOCA method.

    HUC12_name = name of HUC12 watershed or area that is being modeled as well as the name
    of the directory that holds all subsequent sub-directories and files for the WEPP runs

    var_cols = column names of variables (bcca and loca have different names)

    proj_names = path to text file with climate projection names

    num_locs = number of modeled areas in netcdf

    proj_num = number of projections/models in netcdf

    obs_cli_xlsx = excel spreadsheet with observed climate data. See read_me for formatting

    man,LOCA,BCCA + _labs = list of management and climate scenario labels as strings

    periods = list of time periods as integers 
    '''

    def netcdf_calcli(dwnsc_type, ftp_num, var_cols, num_locs):
        '''
        Runs functions that extract netcdf files from ftp ID and produce a fully
        calibrated .cli file

        Separated by downscaling method
        '''
        #Set paths to netcdf, GDS, PAR, uncalibrated, observed directories as well a
        #define column labels, and climate model IDss 
        netcdf_path = str(HUC12_path + '/netCDF/{}/'.format(dwnsc_type))
        GDS_path = str(HUC12_path + '/GDS/{}/'.format(dwnsc_type))
        uncal_path = str(HUC12_path + '/Uncalibrated/{}/'.format(dwnsc_type))
        obs_path = str(HUC12_path + '/obs_data/{}'.format(obs_cli_xlsx))
        par_path = str(HUC12_path + '/PAR/{}/'.format(dwnsc_type))
        model_IDs = str(HUC12_path + 'netcdf/{}_projections_Short.txt'.format(dwnsc_type))

        #Run functions to extract netcdf, convert to GDS format, and then generate fully
        #calibrated climate files
        extract_netcdf(ftp_lst[ftp_num], netcdf_path, HUC12_name)
        netcdf_to_GDS(netcdf_path, var_cols, model_IDs, num_locs, proj_num, dwnsc_type, GDS_path)
        gen_cli_file(GDS_path, HUC12_name, uncal_path, obs_path, '19', '59', par_path, True)
    
    LOCA_cols = ['lat', 'lon', 'projection', 'time']
    BCCA_cols = ['latitude', 'longitude', 'projection', 'time']

    #netCDF extractions come with different column labels for LOCA and BCCA,
    #so they must be defined beforehand
    netcdf_calcli('LOCA', 1, LOCA_cols, 9)
    netcdf_calcli('BCCA', 0, BCCA_cols,5)

    #Set up paths to the base runs directory (includes soil, slope, and management 
    #files), the parent directory for all model runs (Run_dir), and the excel file
    #that contains the coordinate points for each hillslope
    base_runs_dir = str(HUC12_path + 'Runs/wepp/runs/')
    Run_dir = str(HUC12_path + 'Runs/')
    hill_coords = str(HUC12_path + 'hillslope_coords.xlsx')

    #Combine LOCA and BCCA model labs into one list for prep_input_files
    model_labs = []
    for mod in LOCA_labs:
        model_labs.append(mod)

    for mod in BCCA_labs:
        model_labs.append(mod)


    #Run prep_input_files - no need to separate by downscaling method because climate 
    prep_input_files(base_runs_dir, wshed_ID, HUC12_name, Run_dir, model_labs, man_labs, periods)

    #Set path to LOCA and BCCA .cli files
    LOCA_cli_path = str(HUC12_path + '/PAR/LOCA/')
    BCCA_cli_path = str(HUC12_path + '/PAR/BCCA/')

    #Run assign_cli_files for each downscaling method
    assign_cli_files(hill_coords, LOCA_cli_path, Run_dir, LOCA_labs, 'Base/', man_labs, periods, HUC12_name, None)
    assign_cli_files(hill_coords, BCCA_cli_path, Run_dir, BCCA_labs, 'Base/', man_labs, periods, HUC12_name, None)



############# SET UP INPUTS FOR "netCDF_to_calcli" FUNCTION ###################

#Define ftp IDs. First ID in each list is BCCA and second is LOCA
BE1_ftp_lst = ['202112031343Nr5d_n_1ybge3', '202112011141Nr5l_n_PB_INf']
DO1_ftp_lst = ['202112011149Nr5d_n_DLYep4', '202112011154Nr5l_n_EMRSgN']
GO1_ftp_lst = ['202112210935Nr5d_n_KFSh8l', '202112210934Nr5l_n_H2xfJA']
RO1_ftp_lst = ['202112011146Nr5d_n_PDkd1q', '202112011146Nr5l_n_SLtbnG']
ST1_ftp_lst = ['202112011100Nr5d_n_DtgiWu', '202112011054Nr5l_n_FMUb4i']

#Define HUC12 IDs from DEP project 
BE1_ID = '070200110305_'
DO1_ID = '070400040109_'
GO1_ID = '070400010601_'
RO1_ID = '101702031504_'
ST1_ID = '070102020303_'

#Define labels for each climate model, time period, and management scenario
LOCA_model_labs = ['L1','L2','L3','L4','L5','L6']
BCCA_model_labs = ['B1','B2','B3','B4','B5','B6']
man_labs = ['CC', 'CT', 'Comb', 'Per', 'NC']
periods = ['19', '59', '99']

#Define path to HUC12 watershed directory
HUC12_path = 'E:/Soil_Erosion_Project/WEPP_PRWs/GO1/'

############# RUN netCDF_to_calcli ##################
run_prep(HUC12_path, GO1_ftp_lst, 'GO1', 6,'GO1_MnDNR_Obs.xlsx',\
             GO1_ID, LOCA_model_labs, BCCA_model_labs, man_labs, periods)



