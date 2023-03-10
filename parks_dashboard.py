import os
import arcpy
import configparser
import sys

from datetime import datetime

from HRMutils_py3 import setupLog, send_error

# TODO: Have send_error script reference config file at root of scripts directory
#  for email recipients

arcpy.env.overwriteOutput = True
arcpy.SetLogHistory(False)

TODAY = datetime.today().date().strftime('%m%d%Y')
LOG_FILE = "logs/logs_{}.log".format(TODAY)

loggy = setupLog(LOG_FILE)

TOOLBOX = r"R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\scripts\New Toolbox.atbx"

TOOLBOX_NAME = "NewToolbox"
MODEL = "Dashboard_model_20230301"

TOOL_NAME = f'{MODEL.lower()}_{TOOLBOX_NAME}'  # 'dashboard_model_20230301_NewToolbox'

arcpy.ImportToolbox(TOOLBOX)
config = configparser.ConfigParser()
config.read("config.ini")

# MODEL VARIABLES - Get from model properties

SDE = config.get("options", "SDE")
REFERENCE_GDB = config.get("options", "REFERENCE_GDB")
OutputFGDB = config.get("options", "OutputFGDB")
Excel_Output_Location = config.get("options", "Excel_Output_Location")
SHP_DIR = config.get("options", "SHP_DIR")

SDEADM_LND_outdoor_rec_poly = os.path.join(SDE, "SDEADM.LND_outdoor_rec_poly")
SDEADM_LND_outdoor_rec_use = os.path.join(SDE, "SDEADM.LND_outdoor_rec_use")
index_table_csv = os.path.join(REFERENCE_GDB, "index_table_csv")  # TODO: Create better name
SDEADM_AST_boat_facility = os.path.join(SDE, "SDEADM.AST_boat_facility")
object_id_table = os.path.join(REFERENCE_GDB, "Object_ID")  # TODO: Create better name

SDEADM_LND_hrm_park = os.path.join(SDE, "SDEADM.LND_hrm_parcel_parks", "SDEADM.LND_hrm_park")

rural_rec_commuter_areas = os.path.join(REFERENCE_GDB, "rural_rec_commuter_areas")

SDEADM_ADM_gsa_polygon = os.path.join(SDE, "SDEADM.ADM_gsa_boundaries", "SDEADM.ADM_gsa_polygon")
material_codes = os.path.join(REFERENCE_GDB, "material_codes")
SDEADM_ADM_polling_district = os.path.join(SDE, "SDEADM.ADM_electoral_boundaries", "SDEADM.ADM_polling_district")
population_index_table_csv = os.path.join(REFERENCE_GDB, "population_index_table_csv")

excel_file = os.path.join(Excel_Output_Location, "park_assets.xls")
final_feature = os.path.join(OutputFGDB, "final_phase_1_assets")


def run_model():

    print(f"\tCall model as function like: 'arcpy.{MODEL.lower()}_{TOOLBOX_NAME}()', adding in model parameters in function call.")

    # HAD TO CREATE MODEL PARAMETERS
    arcpy.dashboard_model_20230301_NewToolbox(
        OutputFGDB,
        Excel_Output_Location,
        SHP_DIR,
        SDEADM_LND_outdoor_rec_poly,
        SDEADM_LND_outdoor_rec_use,
        index_table_csv,
        SDEADM_AST_boat_facility,
        object_id_table,

        # R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\scripts\intermediate_data.gdb\group_by_prox

        SDEADM_LND_hrm_park,
        rural_rec_commuter_areas,
        SDEADM_ADM_gsa_polygon,
        material_codes,
        SDEADM_ADM_polling_district,
        population_index_table_csv,
    )


if __name__ == "__main__":
    import traceback

    server_name = os.environ.get("COMPUTERNAME")
    script_name = os.path.basename(sys.argv[0])
    email_error_msg = f"ERROR - Parks dashboard script failed. {server_name} / {script_name}"

    print(f"START Time: {datetime.now()}")
    loggy.info(f"\nSTART Time: {datetime.now()}")

    try:

        if arcpy.Exists(OutputFGDB):
            loggy.info(f"Deleting exists workspace, {OutputFGDB}...")
            arcpy.Delete_management(OutputFGDB)

        gdb_dir = os.path.dirname(OutputFGDB)
        gdb_name = os.path.basename(OutputFGDB)
        arcpy.CreateFileGDB_management(gdb_dir, gdb_name).getOutput(0)
        
        run_model()

        final_table_row_count = int(arcpy.GetCount_management(final_feature)[0])
        loggy.info(f"Final table row count: {final_table_row_count}.")

        if final_table_row_count < 1000:
            raise ValueError(f"Final table row count: {final_table_row_count}.\t(This should be >1000.)")

        asset_types = [row[0] for row in arcpy.da.SearchCursor(final_feature, "Subcategory_1", sql_clause=(
            "DISTINCT Subcategory_1", "ORDER BY Subcategory_1"))]
        loggy.info(f"Assets included in final feature:\n\t{', '.join(asset_types)}")

        if "Playground" not in asset_types:
            raise IndexError(f"Did NOT find PLAYGROUNDS in the final report. Assets found: {', '.join(asset_types)}")

    except arcpy.ExecuteError:
        arcpy_msgs = arcpy.GetMessages(2)
        loggy.error(f"ARCPY ERROR: {arcpy_msgs}")

        # send_error("ERROR - Parks dashboard failed", email_error_msg)

    except Exception as e:
        loggy.error(f"ERROR: {e}")

        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]

        pymsg = f"PYTHON ERRORS:\n" \
                f"Traceback Info:\n" \
                f"{tbinfo}\nError Info:\n" \
                f"\t{sys.exc_info()[0]}: {sys.exc_info()[1]}"

        loggy.error(pymsg)

        # send_error("ERROR - Parks dashboard failed", email_error_msg)

    loggy.info(f"END Time: {datetime.now()}")
    loggy.info("\n")
