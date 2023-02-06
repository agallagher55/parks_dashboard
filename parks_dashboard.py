"""
- Approximate run time: 20 minutes.

"""

# TODO: Add email notifications
# TODO: Add as chron job

import arcpy
import os
import configparser

from datetime import datetime

from logger import function_logger as loggy

arcpy.env.overwriteOutput = True
arcpy.SetLogHistory(False)

loggy.setLevel("INFO")

config = configparser.ConfigParser()
config.read("config.ini")

SDE = config.get("options", "SDE")

OutputFGDB = config.get("options", "OutputFGDB")
SHP_DIR = config.get("options", "SHP_DIR")
Excel_Output_Location = config.get("options", "Excel_Output_Location")
REFERENCE_GDB = config.get("options", "REFERENCE_GDB")

rural_rec_commuter_areas = os.path.join(REFERENCE_GDB, "rural_rec_commuter_areas")

object_id_table = os.path.join(REFERENCE_GDB, "Object_ID")  # TODO: Create better name
index_table_csv = os.path.join(REFERENCE_GDB, "index_table_csv")  # TODO: Create better name
population_index_table_csv = os.path.join(REFERENCE_GDB, "population_index_table_csv")
material_codes = os.path.join(REFERENCE_GDB, "material_codes")

SDEADM_AST_boat_facility = os.path.join(SDE, "SDEADM.AST_boat_facility")
SDEADM_LND_outdoor_rec_poly = os.path.join(SDE, "SDEADM.LND_outdoor_rec_poly")
SDEADM_LND_outdoor_rec_use = os.path.join(SDE, "SDEADM.LND_outdoor_rec_use")
SDEADM_ADM_polling_district = os.path.join(SDE, "SDEADM.ADM_electoral_boundaries", "SDEADM.ADM_polling_district")
SDEADM_ADM_gsa_polygon = os.path.join(SDE, "SDEADM.ADM_gsa_boundaries", "SDEADM.ADM_gsa_polygon")
SDEADM_LND_hrm_park = os.path.join(SDE, "SDEADM.LND_hrm_parcel_parks", "SDEADM.LND_hrm_park")

final_asset_point_output_xlsx = fr"{Excel_Output_Location}\park_assets.xlsx"


def create_report():

    # Check that Excel output location exists
    if not os.path.exists(Excel_Output_Location):
        raise FileNotFoundError(f"Excel output folder is invalid: {Excel_Output_Location}")

    boat_facilitiesd_2_ = arcpy.conversion.FeatureClassToFeatureClass(
        in_features=SDEADM_AST_boat_facility,
        out_path=OutputFGDB,
        out_name="boat_facilitiesd",
        where_clause="OWNER = 'HRM'"
    )[0]

    recreation_locations_2_ = arcpy.conversion.FeatureClassToFeatureClass(
        in_features=SDEADM_LND_outdoor_rec_poly,
        out_path=OutputFGDB,
        out_name="recreation_locations"
    )[0]

    rec_use_table_20230111 = arcpy.conversion.TableToTable(
        in_rows=SDEADM_LND_outdoor_rec_use,
        out_path=OutputFGDB,
        out_name="rec_use_table_20230111"
    )[0]

    recreation_locations_JoinFeatures_shp = fr"{SHP_DIR}\recreation_locations_JoinFeatures.shp"

    arcpy.gapro.JoinFeatures(target_layer=recreation_locations_2_, join_layer=rec_use_table_20230111,
                             output=recreation_locations_JoinFeatures_shp, join_operation="JOIN_ONE_TO_MANY",
                             spatial_relationship="", spatial_near_distance="", temporal_relationship="",
                             temporal_near_distance="", attribute_relationship=[["ASSETID", "ASSETID"]],
                             summary_fields=[], join_condition="", keep_all_target_features="")

    asset_name_join_together = arcpy.conversion.FeatureClassToFeatureClass(
        in_features=recreation_locations_JoinFeatures_shp,
        out_path=OutputFGDB,
        out_name="asset_name_join_together"
    )[0]

    asset_name_join2_6_ = arcpy.management.JoinField(
        in_data=asset_name_join_together, in_field="REC_USE", join_table=index_table_csv,
        join_field="MPFU", fields=["New_NAME"]
    )[0]

    asset_name_join2_4_ = arcpy.management.AddFields(in_table=asset_name_join2_6_, field_description=[
        ["Ownership_Filter", "TEXT", "Ownership_Filter", "255", "", ""],
        ["Maintenance_Filter", "TEXT", "Maintenance_Filter", "255", "", ""],
        ["Primary_Use_Filter", "TEXT", "Primary_Use_Filter", "255", "", ""]])[0]

    output_1_3_ = arcpy.management.CalculateField(in_table=asset_name_join2_4_, field="Ownership_Filter",
                                                      expression="cf(!OWNER!)", expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return 'NO DATA'
    else:
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    output_1_6_ = arcpy.management.CalculateField(in_table=output_1_3_, field="Maintenance_Filter", expression="cf(!MAINTBY!)",
                                        expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return 'NO DATA'
    else:
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    asset_name_join2_3_ = arcpy.management.CalculateField(in_table=output_1_6_, field="Primary_Use_Filter", expression="cf(!PRIMARY!)",
                                        expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return 'No'
    elif a == 'N':
        return 'No'
    else:
        return 'Yes'""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    asset_name_join2_2_asset_name_join2_2_ = arcpy.management.AddField(in_table=asset_name_join2_3_, field_name="diss_sum", field_type="LONG",
                                  field_precision=None, field_scale=None, field_length=None, field_alias="diss_sum",
                                  field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED")[0]

    asset_name_join2_2_asset_name_join2_3_ = arcpy.management.CalculateField(in_table=asset_name_join2_2_asset_name_join2_2_, field="diss_sum",
                                        expression="1", expression_type="PYTHON3", code_block="", field_type="TEXT",
                                        enforce_domains="NO_ENFORCE_DOMAINS")[0]

    dissed = fr"{OutputFGDB}\dissed"
    arcpy.management.Dissolve(in_features=asset_name_join2_2_asset_name_join2_3_, out_feature_class=dissed,
                                  dissolve_field=["ASSETCODE", "ASSETID"], statistics_fields=[["diss_sum", "SUM"]],
                                  multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    asset_name_join22asset_name_ = arcpy.management.AddField(in_table=dissed, field_name="ID_CODE_CONCAT", field_type="TEXT", field_precision=None,
                                  field_scale=None, field_length=None, field_alias="ID_CODE_CONCAT",
                                  field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")[0]

    dissed_3_ = arcpy.management.CalculateField(in_table=asset_name_join22asset_name_, field="ID_CODE_CONCAT",
                                                    expression="cf(!SUM_diss_sum!,!ASSETCODE!)",
                                                    expression_type="PYTHON3", code_block="""def cf(a,b):
    if a == 1:
        return 'NO'
    else:
        if b is None:
            return 'NO'
        elif 'SPC' in b:
            return 'Multi-Use Court'
        elif 'SPF' in b:
            return 'Multi-Use Field'
        else:
            return 'NO'""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_NonMPtoSP_Merge_2_ = arcpy.management.AddField(in_table=asset_name_join2_3_, field_name="Repeat_IDs", field_type="TEXT",
                                      field_precision=None, field_scale=None, field_length=None,
                                      field_alias="Repeat_IDs", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED")[0]

    if dissed_3_:
        NonMPtoSP_Merge_NonMPtoSP_Merge_4_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_NonMPtoSP_Merge_2_, field="Repeat_IDs",
                                            expression="cf(!ASSETID!)", expression_type="PYTHON3", code_block="""uniqueList = []
def cf(b):
    if b not in uniqueList:
        uniqueList.append(b)
        return ''
    else:
        return 'repeat id'
""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_NonMPtoSP_Merge_6_ = arcpy.management.JoinField(in_data=NonMPtoSP_Merge_NonMPtoSP_Merge_4_, in_field="ASSETID",
                                       join_table=dissed_3_, join_field="ASSETID", fields=["ID_CODE_CONCAT"])[0]

    if dissed_3_:
        asset_name_join2_5_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_NonMPtoSP_Merge_6_, field="New_NAME",
                                            expression="cf(!ID_CODE_CONCAT!,!New_NAME!)", expression_type="PYTHON3",
                                            code_block="""def cf(a,b):
    if a is None and b is None:
        return a
    elif a is None and b is not None:
        return b
    elif 'NO'.lower() in a.lower():
        return b
    else:
        return a
    """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_NonMPtoSP_Merge_3_, Count = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=asset_name_join2_5_, selection_type="NEW_SELECTION",
                where_clause="Repeat_IDs = 'repeat id'")

    if dissed_3_:
        Updated_Input_With_Rows_Removed = arcpy.management.DeleteRows(in_rows=NonMPtoSP_Merge_NonMPtoSP_Merge_3_)[0]

    if dissed_3_:
        filtered_for_ownership_and_m_2_ = arcpy.management.CalculateGeometryAttributes(in_features=Updated_Input_With_Rows_Removed,
                                                         geometry_property=[["X", "CENTROID_X"], ["Y", "CENTROID_Y"]],
                                                         length_unit="", area_unit="",
                                                         coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
                                                         coordinate_format="SAME_AS_INPUT")[0]

    if dissed_3_:
        centroid = arcpy.conversion.TableToTable(
                in_rows=filtered_for_ownership_and_m_2_,
                out_path=OutputFGDB,
                out_name="centroid",
                where_clause="(Ownership_Filter = 'HRM' Or Maintenance_Filter = 'HRM') And ASSETSTAT = 'INS'"
        )[0]

    NonMPtoSP = fr"{OutputFGDB}\NonMPtoSP"
    if dissed_3_:
        arcpy.management.XYTableToPoint(
                in_table=centroid,
                out_feature_class=NonMPtoSP,
                x_field="X",
                y_field="Y",
                coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]];19877400 -10001100 10000;0 1;0 1;0.001;2;0.001;IsHighPrecision"
            )

    if dissed_3_:
        non_boat_facilities = arcpy.conversion.FeatureClassToFeatureClass(in_features=NonMPtoSP, out_path=OutputFGDB,
                                                        out_name="non_boat_facilities")[0]

    boat_facilitiesd_Merge = fr"{OutputFGDB}\boat_facilitiesd_Merge"
    if dissed_3_:
        arcpy.management.Merge(inputs=[boat_facilitiesd_2_, non_boat_facilities], output=boat_facilitiesd_Merge,
                                   field_mappings="ASSETID \"AssetID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETID,0,50;BOATID \"Boat Facility ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,BOATID,0,50;ASSETCODE \"Asset Code\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETCODE,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETCODE,0,6;OWNER \"Owner\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,OWNER,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,OWNER,0,5;BOATNAME \"Boat Facility Name\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,BOATNAME,0,50;EMERGSERV \"Emergency Services\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,EMERGSERV,0,1;INSTYR \"Install Year\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,INSTYR,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,INSTYR,-1,-1;INSTYRCONF \"Install Year Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,INSTYRCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,INSTYRCONF,-1,-1;MAT \"Material\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,MAT,0,8,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MAT,0,8;MATCONF \"Material Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,MATCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MATCONF,-1,-1;LOCGEN \"General Location\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,LOCGEN,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,LOCGEN,0,6;HRMINTRST \"HRM Interest\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,HRMINTRST,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,HRMINTRST,0,1;LENGTHM \"Length\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,LENGTHM,-1,-1;SIZE1UNIT \"Length Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE1UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SIZE1UNIT,0,4;SIZE1CONF \"Length confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE1CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SIZE1CONF,-1,-1;HEIGHTM \"Height\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,HEIGHTM,-1,-1;SIZE2UNIT \"Height Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE2UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SIZE2UNIT,0,4;SIZE2CONF \"Height confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE2CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SIZE2CONF,-1,-1;AREASQM \"Area\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,AREASQM,-1,-1;SIZE3UNIT \"Area Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE3UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SIZE3UNIT,0,4;SIZE3CONF \"Area confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE3CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SIZE3CONF,-1,-1;WIDTHM \"Width\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,WIDTHM,-1,-1;SIZE4UNIT \"Width Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE4UNIT,0,4;SIZE4CONF \"Width confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SIZE4CONF,-1,-1;ASSETRAW \"AssetRaw\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETRAW,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETRAW,0,50;ASSETGRP \"Asset Group\" true true false 2 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETGRP,0,2,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETGRP,0,2;ASSETSBGRP \"Asset SubGroup\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETSBGRP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETSBGRP,0,6;ASSETTYP \"Asset Type\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETTYP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETTYP,0,6;ASSETSBTYP \"Asset SubType\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETSBTYP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETSBTYP,0,6;ASSETSBTCP \"Asset SubType Component\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETSBTCP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETSBTCP,0,6;ASSETDESC \"Asset Description\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETDESC,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETDESC,0,50;ROLLUPID \"Roll Up ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ROLLUPID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ROLLUPID,0,50;PARTNER \"Partner\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,PARTNER,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PARTNER,0,5;ASSETSTAT \"Asset Status\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ASSETSTAT,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETSTAT,0,5;CRIT \"Criticality\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,CRIT,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CRIT,-1,-1;CRITCONF \"Criticality Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,CRITCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CRITCONF,-1,-1;INSTDATE \"Install Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,INSTDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,INSTDATE,-1,-1;INSTCS \"Install Cost\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,INSTCS,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,INSTCS,-1,-1;BASELIFE \"Base life\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,BASELIFE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BASELIFE,-1,-1;RMLIFE \"Remaining Life\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,RMLIFE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,RMLIFE,-1,-1;RMLIFECONF \"Remaining Life Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,RMLIFECONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,RMLIFECONF,-1,-1;INSTCSCONF \"Install Cost Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,INSTCSCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,INSTCSCONF,-1,-1;REPLCSRA \"Replacement Cost Rate\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,REPLCSRA,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,REPLCSRA,-1,-1;REPLRACONF \"Replacement Rate Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,REPLRACONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,REPLRACONF,-1,-1;REPLCSTOTL \"Replacement Cost Total\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,REPLCSTOTL,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,REPLCSTOTL,-1,-1;REPLCSCONF \"Replacement Cost Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,REPLCSCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,REPLCSCONF,-1,-1;TCACAT \"TCA Category\" true true false 10 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,TCACAT,0,10,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,TCACAT,0,10;PERFRMRA \"Performance Rate\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,PERFRMRA,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PERFRMRA,-1,-1;PERFRMCONF \"Performance Rate Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,PERFRMCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PERFRMCONF,-1,-1;WARNTYLAB \"Labour Warranty Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,WARNTYLAB,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,WARNTYLAB,-1,-1;WARRANTYDATE \"Manufacturer Warranty Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,WARRANTYDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,WARRANTYDATE,-1,-1;LOCATION \"Location\" true true false 250 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,LOCATION,0,250,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,LOCATION,0,250;CONDIT \"Condition\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,CONDIT,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CONDIT,-1,-1;CONDITDTE \"Condition Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,CONDITDTE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CONDITDTE,-1,-1;CONDICONF \"Condition Rating Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,CONDICONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CONDICONF,-1,-1;MAINTBY \"Maintained By\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,MAINTBY,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MAINTBY,0,5;LEGACYID \"Legacy ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,LEGACYID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,LEGACYID,0,50;PROFCNCAT \"Profile Key Concatenation\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,PROFCNCAT,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PROFCNCAT,0,50;FCODE \"Feature Code\" true true false 12 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,FCODE,0,12,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,FCODE,0,12;ADDBY \"Add by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ADDBY,0,32,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ADDBY,0,32;MODBY \"Modified by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,MODBY,0,32,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MODBY,0,32;ADDDATE \"Add Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,ADDDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ADDDATE,-1,-1;MODDATE \"Modified Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,MODDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MODDATE,-1,-1;SDATE \"Source Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SDATE,-1,-1;SOURCE \"Data Source\" true true false 20 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SOURCE,0,20,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SOURCE,0,20;SACC \"Source Accuracy\" true true false 2 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,SACC,0,2,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SACC,0,2;GLOBALID \"GLOBALID\" false false true 38 GlobalID 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,GLOBALID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,GLOBALID,-1,-1;LANDID \"LandID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,LANDID,-1,-1;PARK_ID \"Park ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,PARK_ID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PARK_ID,-1,-1;CIV_ID \"Civic ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\boat_facilitiesd,CIV_ID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CIV_ID,-1,-1;RECPOLYID \"Recreation Poly ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,RECPOLYID,0,50;LAND_ID \"Land ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,LAND_ID,-1,-1;LENGTH \"Length\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,LENGTH,-1,-1;WIDTH \"Width\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,WIDTH,-1,-1;ACCESSIBLE \"Accessible\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ACCESSIBLE,0,1;CLASS \"Classification\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,CLASS,0,5;POLY_AREA \"Polygon Area\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,POLY_AREA,-1,-1;REC_ID \"Park Rec Feature ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,REC_ID,-1,-1;MEASURE_NOTES \"Measurement Notes\" true true false 500 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MEASURE_NOTES,0,500;PLAYLEVEL_NOTES \"Play Level Notes\" true true false 100 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PLAYLEVEL_NOTES,0,100;OBJECTID_1 \"OBJECTID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,OBJECTID_1,-1,-1;RECUSEID \"Recreation Use ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,RECUSEID,0,50;ASSETID_1 \"Asset ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ASSETID_1,0,50;GENRECTYPE \"General Recreation Type\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,GENRECTYPE,-1,-1;REC_USE \"Recreation Use\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,REC_USE,0,8;PRIMARY \"Primary Use\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,PRIMARY,0,1;NUMCOURTS \"Number of Courts\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,NUMCOURTS,-1,-1;COMMENTS \"Comments\" true true false 150 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,COMMENTS,0,150;FENCE \"Fence\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,FENCE,0,1;LIGHTING \"Lighting\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,LIGHTING,0,1;SEATING \"Seating\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SEATING,0,1;SEATCAPCTY \"Seating Capacity\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SEATCAPCTY,-1,-1;WSHRMS \"Washrooms Available\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,WSHRMS,0,1;SCOREBOARD \"Scoreboard\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SCOREBOARD,0,1;BDCLASS \"Ball Diamond Classification\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDCLASS,0,8;BDMATINF \"Ball Diamond Infield Material\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDMATINF,0,8;BDMOUND \"Ball Diamond Mound\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDMOUND,0,1;BDDUGOUTS \"Ball Diamond Covered Dugouts\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDDUGOUTS,0,1;BDBACKSTP \"Ball Diamond Backstop\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDBACKSTP,0,1;BDBNCHPLYR \"Ball Diamond Player Benches\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDBNCHPLYR,0,1;BDFENOUTF \"Ball Diamond Outfield Fence\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,BDFENOUTF,0,1;NONSPORTUSE \"Non-Sport Use Permitted\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,NONSPORTUSE,0,1;UNSCHEDUSE \"Unscheduled Use Permitted\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,UNSCHEDUSE,0,1;GLOBALID_1 \"GLOBALID\" true true false 38 Guid 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,GLOBALID_1,-1,-1;ADDBY_1 \"Add by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ADDBY_1,0,32;MODBY_1 \"Modified by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MODBY_1,0,32;ADDDATE_1 \"Add Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,ADDDATE_1,-1,-1;MODDATE_1 \"Modified Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MODDATE_1,-1,-1;SDATE_1 \"Source Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SDATE_1,-1,-1;SOURCE_1 \"Data Source\" true true false 20 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SOURCE_1,0,20;SACC_1 \"Source Accuracy\" true true false 2 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,SACC_1,0,2;OBJECTID_12 \"OBJECTID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,OBJECTID_12,-1,-1;MPFU \"MPFU\" true true false 8000 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,MPFU,0,8000;New_NAME \"New_NAME\" true true false 8000 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,New_NAME,0,8000;Ownership_Filter \"Ownership_Filter\" true true false 255 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,Ownership_Filter,0,255;Maintenance_Filter \"Maintenance_Filter\" true true false 255 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,Maintenance_Filter,0,255;X \"X\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,X,-1,-1;Y \"Y\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230113\\TestMap_20230113\\Tmap2\\Tmap2.gdb\\non_boat_facilities,Y,-1,-1",
                                   add_source="NO_SOURCE_INFO")

    if dissed_3_:
        playgrounds = arcpy.conversion.FeatureClassToFeatureClass(
            in_features=boat_facilitiesd_Merge, out_path=OutputFGDB,
            out_name="playgrounds", where_clause="New_NAME = 'Playground'"
        )[0]

    if dissed_3_:
        PLAYG_3_ = arcpy.management.CalculateField(in_table=playgrounds, field="PARK_ID",
                                                       expression="SequentialNumber(!PARK_ID!)",
                                                       expression_type="PYTHON3", code_block="""# Calculates a sequential number
rec= 10000
def SequentialNumber(a):
    if a is None:
        global rec
        pStart = 1
        pInterval = 1
        if (rec == 0):
            rec = pStart
        else:
            rec = rec + pInterval
        return rec
    else: 
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        playg2_2_ = arcpy.management.CalculateField(in_table=PLAYG_3_, field="LAND_ID",
                                                        expression="SequentialNumber(!LAND_ID!)",
                                                        expression_type="PYTHON3", code_block="""# Calculates a sequential number
# More calculator examples at esriurl.com/CalculatorExamples
rec= 10000
def SequentialNumber(a):
    if a is None:
        global rec
        pStart = 1
        pInterval = 1
        if (rec == 0):
            rec = pStart
        else:
            rec = rec + pInterval
        return rec
    else: 
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    Summary_Statistics_Dissolve_LID_PID = fr"{OutputFGDB}\Summary_Statistics_Dissolve_LID_PID"
    if dissed_3_:
        arcpy.management.Dissolve(in_features=playg2_2_, out_feature_class=Summary_Statistics_Dissolve_LID_PID,
                                      dissolve_field=["PARK_ID", "LAND_ID"], statistics_fields=[],
                                      multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    SummaryStatistics_PID = fr"{OutputFGDB}\SummaryStatistics_PID"
    if dissed_3_:
        arcpy.analysis.Statistics(in_table=playgrounds, out_table=SummaryStatistics_PID,
                                      statistics_fields=[["PARK_ID", "COUNT"]], case_field=["PARK_ID"])

    if dissed_3_:
        pg_Dissolve1_2_ = arcpy.management.JoinField(in_data=Summary_Statistics_Dissolve_LID_PID, in_field="PARK_ID",
                                       join_table=SummaryStatistics_PID, join_field="PARK_ID", fields=["FREQUENCY"])[0]

    if dissed_3_:
        pg_Dissolve1_3_ = arcpy.management.AlterField(in_table=pg_Dissolve1_2_, field="FREQUENCY", new_field_name="park_id_frequency",
                                        new_field_alias="park_id_frequency", field_type="", field_length=4,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    Summary_Statistics_LID = fr"{OutputFGDB}\Summary_Statistics_LID"
    if dissed_3_:
        arcpy.analysis.Statistics(in_table=playg2_2_, out_table=Summary_Statistics_LID,
                                      statistics_fields=[["LAND_ID", "COUNT"]], case_field=["LAND_ID"])

    if dissed_3_:
        pg_Dissolve1_4_ = arcpy.management.JoinField(in_data=pg_Dissolve1_3_, in_field="LAND_ID", join_table=Summary_Statistics_LID,
                                       join_field="LAND_ID", fields=["FREQUENCY"])[0]

    if dissed_3_:
        pg_Dissolve1_5_ = arcpy.management.AlterField(in_table=pg_Dissolve1_4_, field="FREQUENCY", new_field_name="land_id_frequency",
                                        new_field_alias="land_id_frequency", field_type="", field_length=4,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    if dissed_3_:
        filtered_pgs = arcpy.conversion.FeatureClassToFeatureClass(
            in_features=pg_Dissolve1_5_, out_path=OutputFGDB,
            out_name="filtered_pgs", where_clause="land_id_frequency = 1"
        )[0]

    if dissed_3_:
        playgrounds_with_same_lid_pid = arcpy.conversion.FeatureClassToFeatureClass(in_features=pg_Dissolve1_5_, out_path=OutputFGDB,
                                                        out_name="playgrounds_with_same_lid_pid",
                                                        where_clause="land_id_frequency > 1",
                                                        config_keyword="")[0]

    if dissed_3_:
        playgrounds_with_same_lid_pid_3_ = arcpy.management.AddFields(in_table=playgrounds_with_same_lid_pid,
                                                                          field_description=[
                                                                              ["X", "DOUBLE", "X", "", "", ""],
                                                                              ["Y", "DOUBLE", "Y", "", "", ""]])[0]

    if dissed_3_:
        playgrounds_with_same_lid_pid_4_ = arcpy.management.CalculateGeometryAttributes(in_features=playgrounds_with_same_lid_pid_3_,
                                                         geometry_property=[["X", "CENTROID_X"], ["Y", "CENTROID_Y"]],
                                                         coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
                                                         coordinate_format="SAME_AS_INPUT")[0]

    playgrounds_with_same_lid_pid_XYTableToPoint = fr"{OutputFGDB}\playgrounds_with_same_lid_pid_XYTableToPoint"
    if dissed_3_:
        arcpy.management.XYTableToPoint(in_table=playgrounds_with_same_lid_pid_4_,
                                            out_feature_class=playgrounds_with_same_lid_pid_XYTableToPoint, x_field="X",
                                            y_field="Y", z_field="",
                                            coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]];19877400 -10001100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision")

    Dissolve2 = fr"{OutputFGDB}\Dissolve2"
    if dissed_3_:
        arcpy.management.Dissolve(in_features=playgrounds_with_same_lid_pid_XYTableToPoint,
                                      out_feature_class=Dissolve2,
                                      dissolve_field=["Y", "PARK_ID", "LAND_ID", "park_id_frequency",
                                                      "land_id_frequency"], statistics_fields=[],
                                      multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    if dissed_3_:
        Dissolve2_2_ = arcpy.management.AlterField(in_table=Dissolve2, field="PARK_ID", new_field_name="Park ID 2",
                                                       new_field_alias="Park ID 2",
                                                       field_type="",
                                                       field_length=4,
                                                       clear_field_alias="DO_NOT_CLEAR")[0]

    if dissed_3_:
        Dissolve2_4_ = arcpy.management.AlterField(in_table=Dissolve2_2_, field="LAND_ID", new_field_name="Land ID 2",
                                        new_field_alias="Land ID 2", field_type="", field_length=4,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    Merge_4_ = fr"{OutputFGDB}\Merge"
    if dissed_3_:
        arcpy.management.Merge(inputs=[filtered_pgs, Dissolve2_4_], output=Merge_4_,
                                   field_mappings=fr"PARK_ID \"Park ID\" true true false 4 Long 0 0,First,#,C:\Users\an24517\Desktop\Test Maps\TestMap_20230109\TestMap_20230109\TestMap_20230109.gdb\filtered_pgs,PARK_ID,-1,-1;LAND_ID \"Land ID\" true true false 4 Long 0 0,First,#,C:\Users\an24517\Desktop\Test Maps\TestMap_20230109\TestMap_20230109\TestMap_20230109.gdb\filtered_pgs,LAND_ID,-1,-1;park_id_frequency \"park_id_frequency\" true true false 0 Long 0 0,First,#,C:\Users\an24517\Desktop\Test Maps\TestMap_20230109\TestMap_20230109\TestMap_20230109.gdb\filtered_pgs,park_id_frequency,-1,-1,{OutputFGDB}\Dissolve2,park_id_frequency,-1,-1;land_id_frequency \"land_id_frequency\" true true false 0 Long 0 0,First,#,C:\Users\an24517\Desktop\Test Maps\TestMap_20230109\TestMap_20230109\TestMap_20230109.gdb\filtered_pgs,land_id_frequency,-1,-1,{OutputFGDB}\Dissolve2,land_id_frequency,-1,-1;ParkID2 \"ParkID2\" true true false 255 Text 0 0,First,#,C:\Users\an24517\Desktop\Test Maps\TestMap_20230109\TestMap_20230109\TestMap_20230109.gdb\Dissolve2,Park_ID_2,0,255;Y \"Y\" true true false 0 Double 0 0,First,#,{OutputFGDB}\Dissolve2,Y,-1,-1;LandID2 \"LandID2\" true true false 255 Text 0 0,First,#,C:\Users\an24517\Desktop\Test Maps\TestMap_20230109\TestMap_20230109\TestMap_20230109.gdb\Dissolve2,Land_ID_2,0,255",
                                   add_source="NO_SOURCE_INFO")

    if dissed_3_:
        playgrounds_with_same_lid_pid_5_ = arcpy.management.CalculateGeometryAttributes(
                in_features=Merge_4_,
                geometry_property=[
                    ["X", "CENTROID_X"],
                    ["Y", "CENTROID_Y"]],
                coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
                coordinate_format="SAME_AS_INPUT"
            )[0]

    if dissed_3_:
        Merge_5_ = arcpy.management.CalculateField(in_table=playgrounds_with_same_lid_pid_5_, field="PARK_ID",
                                                       expression="cf(!PARK_ID!,!ParkID2!)", expression_type="PYTHON3",
                                                       code_block="""def cf(a,b):
    if a is None:
        return b
    if b is None:
        return a
       """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        Merge_6_ = arcpy.management.CalculateField(in_table=Merge_5_, field="LAND_ID", expression="cf(!LAND_ID!,!LandID2!)",
                                            expression_type="PYTHON3", code_block="""def cf(a,b):
    if a is None:
        return b
    if b is None:
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    GroupByProximity_shp = fr"{SHP_DIR}\GroupByProximity.shp"
    if dissed_3_:
        arcpy.gapro.GroupByProximity(input_layer=Merge_6_, output=GroupByProximity_shp,
                                         spatial_relationship="NEAR_PLANAR", spatial_near_distance="100 Meters",
                                         temporal_relationship="NONE")

    Dissolve3 = fr"{OutputFGDB}\Dissolve3"
    if dissed_3_:
        arcpy.management.Dissolve(in_features=GroupByProximity_shp, out_feature_class=Dissolve3,
                                      dissolve_field=["PARK_ID", "GROUP_ID"],
                                      statistics_fields=[["X", "MEAN"], ["Y", "MEAN"], ["PARK_ID", "FIRST"],
                                                         ["LAND_ID", "FIRST"]], multi_part="MULTI_PART",
                                      unsplit_lines="DISSOLVE_LINES")

    Dissolve3_XYTableToPvbnvbnoint = fr"{OutputFGDB}\Dissolve3_XYTableToPvbnvbnoint"
    if dissed_3_:
        arcpy.management.XYTableToPoint(in_table=Dissolve3, out_feature_class=Dissolve3_XYTableToPvbnvbnoint,
                                            x_field="MEAN_X", y_field="MEAN_Y",
                                            coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]];19877400 -10001100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision")

    Dissolve3_XYTableToPvbnvbnoi = fr"{OutputFGDB}\Dissolve3_XYTableToPvbnvbnoi"
    if dissed_3_:
        arcpy.management.Dissolve(in_features=Dissolve3_XYTableToPvbnvbnoint,
                                      out_feature_class=Dissolve3_XYTableToPvbnvbnoi,
                                      dissolve_field=["MEAN_X", "MEAN_Y"],
                                      statistics_fields=[["FIRST_PARK_ID", "FIRST"], ["FIRST_LAND_ID", "FIRST"]],
                                      multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    if dissed_3_:
        playgrounds_with_same_lid_pid_6_ = arcpy.management.AddFields(in_table=Dissolve3_XYTableToPvbnvbnoi,
                                                                          field_description=[
                                                                              ["X", "DOUBLE", "X", "", "", ""],
                                                                              ["Y", "DOUBLE", "Y", "", "", ""]])[0]

    if dissed_3_:
        playgrounds_with_same_lid_pid_7_ = arcpy.management.CalculateGeometryAttributes(in_features=playgrounds_with_same_lid_pid_6_,
                                                         geometry_property=[["X", "CENTROID_X"], ["Y", "CENTROID_Y"]],
                                                         coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
                                                         coordinate_format="SAME_AS_INPUT")[0]

    if dissed_3_:
        a = arcpy.conversion.FeatureClassToFeatureClass(in_features=playgrounds_with_same_lid_pid_7_,
                                                            out_path=OutputFGDB, out_name="a",
                                                            config_keyword="")[0]

    if dissed_3_:
        s_3_ = arcpy.management.AddField(in_table=a, field_name="coord_sum", field_type="DOUBLE", field_precision=None,
                                      field_scale=None, field_length=None, field_alias="coord_sum",
                                      field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain=""
                                             )[0]

    if dissed_3_:
        a_4_ = arcpy.management.CalculateField(in_table=s_3_, field="coord_sum", expression="!X! + !Y!",
                                                   expression_type="PYTHON3", code_block="", field_type="TEXT",
                                                   enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        playg2_4_ = arcpy.management.AddFields(in_table=a_4_, field_description=[
                ["Park_Land_ID", "TEXT", "Park_Land_ID", "255", "", ""]])[0]

    if dissed_3_:
        a_3_ = arcpy.management.CalculateField(in_table=playg2_4_, field="Park_Land_ID",
                                                   expression="cf(!FIRST_FIRST_PARK_ID!,!FIRST_FIRST_LAND_ID!)",
                                                   expression_type="PYTHON3", code_block="""def cf(a,b):
    return str(round(a))+' - '+str(round(b))""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        new_geom_points = arcpy.conversion.FeatureClassToFeatureClass(in_features=a_3_, out_path=OutputFGDB,
                                                                          out_name="new_geom_points",
                                                                          config_keyword="")[0]

    if dissed_3_:
        playg2_3_ = arcpy.management.AddFields(in_table=playg2_2_, field_description=[
                ["Park_Land_ID", "TEXT", "Park_Land_ID", "255", "", ""]])[0]

    if dissed_3_:
        playg2_5_ = arcpy.management.CalculateField(in_table=playg2_3_, field="Park_Land_ID",
                                                        expression="cf(!PARK_ID!,!LAND_ID!)", expression_type="PYTHON3",
                                                        code_block="""def cf(a,b):
    return str(a) + ' - ' + str(b)""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        c = arcpy.conversion.FeatureClassToFeatureClass(in_features=playg2_5_, out_path=OutputFGDB, out_name="c",
                                                            config_keyword="")[0]

    if dissed_3_:
        new_geom_points_2_ = arcpy.management.JoinField(in_data=new_geom_points, in_field="Park_Land_ID", join_table=c,
                                       join_field="Park_Land_ID",
                                       fields=["ACCESSIBLE", "ADDBY", "ADDBY_1", "ADDDATE", "ADDDATE_1", "AREASQM",
                                               "SIZE3CONF", "SIZE3UNIT", "ASSETCODE", "ASSETDESC", "ASSETGRP",
                                               "ASSETID", "ASSETID_1", "ASSETSTAT", "ASSETSBGRP", "ASSETSBTYP",
                                               "ASSETSBTCP", "ASSETTYP", "ASSETRAW", "BDBACKSTP", "BDCLASS",
                                               "BDDUGOUTS", "BDMATINF", "BDMOUND", "BDFENOUTF", "BDBNCHPLYR",
                                               "BASELIFE", "BOATID", "BOATNAME", "CIV_ID", "CLASS", "COMMENTS",
                                               "CONDIT", "CONDITDTE", "CONDICONF", "CRIT", "CRITCONF", "SOURCE",
                                               "SOURCE_1", "EMERGSERV", "FCODE", "FENCE", "LOCGEN", "GENRECTYPE",
                                               "GLOBALID_1", "HEIGHTM", "HRMINTRST", "INSTCS", "INSTCSCONF", "INSTDATE",
                                               "INSTYR", "INSTYRCONF", "WARNTYLAB", "LAND_ID", "LANDID", "LEGACYID",
                                               "LENGTH", "LENGTHM", "SIZE1CONF", "SIZE1UNIT", "LIGHTING", "LOCATION",
                                               "MAINTBY", "WARRANTYDATE", "MAT", "MATCONF", "MEASURE_NOTES", "MODBY",
                                               "MODBY_1", "MODDATE", "MODDATE_1", "MPFU", "New_NAME", "NONSPORTUSE",
                                               "NUMCOURTS", "OBJECTID_1", "OBJECTID_12", "OWNER",
                                               "Ownership_Maintenance_Primary_Asset_Filter",
                                               "Ownership_Maintenance_Priority_Filter", "PARK_ID", "REC_ID",
                                               "Park_Land_ID", "PARTNER", "PERFRMRA", "PERFRMCONF", "PLAYLEVEL_NOTES",
                                               "POLY_AREA", "PRIMARY", "PROFCNCAT", "RECPOLYID", "REC_USE", "RECUSEID",
                                               "RMLIFE", "RMLIFECONF", "REPLCSCONF", "REPLCSRA", "REPLCSTOTL",
                                               "REPLRACONF", "ROLLUPID", "SCOREBOARD", "SEATING", "SEATCAPCTY", "SACC",
                                               "SACC_1", "SDATE", "SDATE_1", "TCACAT", "UNSCHEDUSE", "WSHRMS", "WIDTH",
                                               "WIDTHM", "SIZE2CONF", "SIZE4CONF", "SIZE2UNIT", "SIZE4UNIT", "X", "Y"]
                                                            )[0]

    if dissed_3_:
        sdfsdfsf = arcpy.conversion.FeatureClassToFeatureClass(in_features=new_geom_points_2_, out_path=OutputFGDB,
                                                                   out_name="sdfsdfsf",
                                                                   config_keyword="")[0]

    if dissed_3_:
        non_playgrounds = arcpy.conversion.FeatureClassToFeatureClass(
            in_features=boat_facilitiesd_Merge, out_path=OutputFGDB,
            out_name="non_playgrounds", where_clause="New_NAME <> 'Playground' Or New_NAME IS NULL"
        )[0]

    if dissed_3_:
        non_playgrounds_2_ = arcpy.management.AddField(in_table=non_playgrounds, field_name="UNIQUE_ID", field_type="LONG",
                                      field_precision=None, field_scale=None, field_length=None,
                                      field_alias="UNIQUE_ID", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED", field_domain="")[0]

    if dissed_3_:
        non_playgrounds_3_ = arcpy.management.CalculateField(in_table=non_playgrounds_2_, field="UNIQUE_ID", expression="!OBJECTID!",
                                            expression_type="PYTHON3", code_block="", field_type="TEXT",
                                            enforce_domains="NO_ENFORCE_DOMAINS")[0]

    non_playgrounds_Dissolve = fr"{OutputFGDB}\non_playgrounds_Dissolve"
    if dissed_3_:
        arcpy.management.Dissolve(in_features=non_playgrounds_3_, out_feature_class=non_playgrounds_Dissolve,
                                      dissolve_field=["UNIQUE_ID"], statistics_fields=[], multi_part="MULTI_PART",
                                      unsplit_lines="DISSOLVE_LINES")

    if dissed_3_:
        non_playgrounds_Dissolve1 = arcpy.management.JoinField(in_data=non_playgrounds_Dissolve, in_field="UNIQUE_ID",
                                       join_table=non_playgrounds_3_, join_field="UNIQUE_ID",
                                       fields=["ACCESSIBLE", "ADDBY", "ADDBY_1", "ADDDATE", "ADDDATE_1", "AREASQM",
                                               "SIZE3CONF", "SIZE3UNIT", "ASSETCODE", "ASSETDESC", "ASSETGRP",
                                               "ASSETID", "ASSETID_1", "ASSETSTAT", "ASSETSBGRP", "ASSETSBTYP",
                                               "ASSETSBTCP", "ASSETTYP", "ASSETRAW", "BDBACKSTP", "BDCLASS",
                                               "BDDUGOUTS", "BDMATINF", "BDMOUND", "BDFENOUTF", "BDBNCHPLYR",
                                               "BASELIFE", "BOATID", "BOATNAME", "CIV_ID", "CLASS", "COMMENTS",
                                               "CONDIT", "CONDITDTE", "CONDICONF", "CRIT", "CRITCONF", "SOURCE",
                                               "SOURCE_1", "EMERGSERV", "FCODE", "FENCE", "LOCGEN", "GENRECTYPE",
                                               "GLOBALID_1", "HEIGHTM", "HRMINTRST", "INSTCS", "INSTCSCONF", "INSTDATE",
                                               "INSTYR", "INSTYRCONF", "WARNTYLAB", "LAND_ID", "LANDID", "LEGACYID",
                                               "LENGTH", "LENGTHM", "SIZE1CONF", "SIZE1UNIT", "LIGHTING", "LOCATION",
                                               "MAINTBY", "Maintenance_Filter", "WARRANTYDATE", "MAT", "MATCONF",
                                               "MEASURE_NOTES", "MODBY", "MODBY_1", "MODDATE", "MODDATE_1", "MPFU",
                                               "New_NAME", "NONSPORTUSE", "NUMCOURTS", "OBJECTID_1", "OBJECTID_12",
                                               "OWNER", "Ownership_Filter", "PARK_ID", "REC_ID", "PARTNER", "PERFRMRA",
                                               "PERFRMCONF", "PLAYLEVEL_NOTES", "POLY_AREA", "PRIMARY", "PROFCNCAT",
                                               "RECPOLYID", "REC_USE", "RECUSEID", "RMLIFE", "RMLIFECONF", "REPLCSCONF",
                                               "REPLCSRA", "REPLCSTOTL", "REPLRACONF", "ROLLUPID", "SCOREBOARD",
                                               "SEATING", "SEATCAPCTY", "SACC", "SACC_1", "SDATE", "SDATE_1", "TCACAT",
                                               "UNIQUE_ID", "UNSCHEDUSE", "WSHRMS", "WIDTH", "WIDTHM", "SIZE2CONF",
                                               "SIZE4CONF", "SIZE2UNIT", "SIZE4UNIT", "X", "Y"])[0]

    sdfsdfsf_Merge = fr"{OutputFGDB}\sdfsdfsf_Merge"
    if dissed_3_:
        arcpy.management.Merge(inputs=[sdfsdfsf, non_playgrounds_Dissolve1], output=sdfsdfsf_Merge,
                                   field_mappings="MEAN_X \"MEAN_X\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MEAN_X,-1,-1;MEAN_Y \"MEAN_Y\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MEAN_Y,-1,-1;FIRST_FIRST_PARK_ID \"FIRST_FIRST_PARK_ID\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,FIRST_FIRST_PARK_ID,-1,-1;FIRST_FIRST_LAND_ID \"FIRST_FIRST_LAND_ID\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,FIRST_FIRST_LAND_ID,-1,-1;X \"X\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,X,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,X,-1,-1;Y \"Y\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,Y,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,Y,-1,-1;coord_sum \"coord_sum\" true true false 0 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,coord_sum,-1,-1;Park_Land_ID \"Park_Land_ID\" true true false 255 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,Park_Land_ID,0,255;ACCESSIBLE \"Accessible\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ACCESSIBLE,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ACCESSIBLE,0,1;ADDBY \"Add by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ADDBY,0,32,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ADDBY,0,32;ADDBY_1 \"Add by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ADDBY_1,0,32,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ADDBY_1,0,32;ADDDATE \"Add Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ADDDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ADDDATE,-1,-1;ADDDATE_1 \"Add Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ADDDATE_1,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ADDDATE_1,-1,-1;AREASQM \"Area\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,AREASQM,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,AREASQM,-1,-1;SIZE3CONF \"Area confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE3CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE3CONF,-1,-1;SIZE3UNIT \"Area Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE3UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE3UNIT,0,4;ASSETCODE \"Asset Code\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETCODE,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETCODE,0,6;ASSETDESC \"Asset Description\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETDESC,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETDESC,0,50;ASSETGRP \"Asset Group\" true true false 2 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETGRP,0,2,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETGRP,0,2;ASSETID \"Asset ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETID,0,50;ASSETID_1 \"Asset ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETID_1,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETID_1,0,50;ASSETSTAT \"Asset Status\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETSTAT,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETSTAT,0,5;ASSETSBGRP \"Asset SubGroup\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETSBGRP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETSBGRP,0,6;ASSETSBTYP \"Asset SubType\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETSBTYP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETSBTYP,0,6;ASSETSBTCP \"Asset SubType Component\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETSBTCP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETSBTCP,0,6;ASSETTYP \"Asset Type\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETTYP,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETTYP,0,6;ASSETRAW \"AssetRaw\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ASSETRAW,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ASSETRAW,0,50;BDBACKSTP \"Ball Diamond Backstop\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDBACKSTP,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDBACKSTP,0,1;BDCLASS \"Ball Diamond Classification\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDCLASS,0,8,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDCLASS,0,8;BDDUGOUTS \"Ball Diamond Covered Dugouts\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDDUGOUTS,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDDUGOUTS,0,1;BDMATINF \"Ball Diamond Infield Material\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDMATINF,0,8,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDMATINF,0,8;BDMOUND \"Ball Diamond Mound\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDMOUND,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDMOUND,0,1;BDFENOUTF \"Ball Diamond Outfield Fence\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDFENOUTF,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDFENOUTF,0,1;BDBNCHPLYR \"Ball Diamond Player Benches\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BDBNCHPLYR,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BDBNCHPLYR,0,1;BASELIFE \"Base life\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BASELIFE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BASELIFE,-1,-1;BOATID \"Boat Facility ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BOATID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BOATID,0,50;BOATNAME \"Boat Facility Name\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,BOATNAME,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,BOATNAME,0,50;CIV_ID \"Civic ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CIV_ID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CIV_ID,-1,-1;CLASS \"Classification\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CLASS,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CLASS,0,5;COMMENTS \"Comments\" true true false 150 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,COMMENTS,0,150,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,COMMENTS,0,150;CONDIT \"Condition\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CONDIT,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CONDIT,-1,-1;CONDITDTE \"Condition Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CONDITDTE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CONDITDTE,-1,-1;CONDICONF \"Condition Rating Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CONDICONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CONDICONF,-1,-1;CRIT \"Criticality\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CRIT,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CRIT,-1,-1;CRITCONF \"Criticality Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,CRITCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,CRITCONF,-1,-1;SOURCE \"Data Source\" true true false 20 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SOURCE,0,20,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SOURCE,0,20;SOURCE_1 \"Data Source\" true true false 20 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SOURCE_1,0,20,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SOURCE_1,0,20;EMERGSERV \"Emergency Services\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,EMERGSERV,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,EMERGSERV,0,1;FCODE \"Feature Code\" true true false 12 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,FCODE,0,12,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,FCODE,0,12;FENCE \"Fence\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,FENCE,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,FENCE,0,1;LOCGEN \"General Location\" true true false 6 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LOCGEN,0,6,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LOCGEN,0,6;GENRECTYPE \"General Recreation Type\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,GENRECTYPE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,GENRECTYPE,-1,-1;GLOBALID_1 \"GLOBALID\" true true false 38 Guid 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,GLOBALID_1,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,GLOBALID_1,-1,-1;HEIGHTM \"Height\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,HEIGHTM,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,HEIGHTM,-1,-1;HRMINTRST \"HRM Interest\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,HRMINTRST,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,HRMINTRST,0,1;INSTCS \"Install Cost\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,INSTCS,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,INSTCS,-1,-1;INSTCSCONF \"Install Cost Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,INSTCSCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,INSTCSCONF,-1,-1;INSTDATE \"Install Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,INSTDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,INSTDATE,-1,-1;INSTYR \"Install Year\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,INSTYR,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,INSTYR,-1,-1;INSTYRCONF \"Install Year Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,INSTYRCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,INSTYRCONF,-1,-1;WARNTYLAB \"Labour Warranty Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,WARNTYLAB,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,WARNTYLAB,-1,-1;LAND_ID \"Land ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LAND_ID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LAND_ID,-1,-1;LANDID \"LandID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LANDID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LANDID,-1,-1;LEGACYID \"Legacy ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LEGACYID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LEGACYID,0,50;LENGTH \"Length\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LENGTH,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LENGTH,-1,-1;LENGTHM \"Length\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LENGTHM,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LENGTHM,-1,-1;SIZE1CONF \"Length confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE1CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE1CONF,-1,-1;SIZE1UNIT \"Length Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE1UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE1UNIT,0,4;LIGHTING \"Lighting\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LIGHTING,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LIGHTING,0,1;LOCATION \"Location\" true true false 250 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,LOCATION,0,250,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,LOCATION,0,250;MAINTBY \"Maintained By\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MAINTBY,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MAINTBY,0,5;WARRANTYDATE \"Manufacturer Warranty Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,WARRANTYDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,WARRANTYDATE,-1,-1;MAT \"Material\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MAT,0,8,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MAT,0,8;MATCONF \"Material Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MATCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MATCONF,-1,-1;MEASURE_NOTES \"Measurement Notes\" true true false 500 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MEASURE_NOTES,0,500,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MEASURE_NOTES,0,500;MODBY \"Modified by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MODBY,0,32,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MODBY,0,32;MODBY_1 \"Modified by\" true true false 32 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MODBY_1,0,32,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MODBY_1,0,32;MODDATE \"Modified Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MODDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MODDATE,-1,-1;MODDATE_1 \"Modified Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MODDATE_1,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MODDATE_1,-1,-1;MPFU \"MPFU\" true true false 8000 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,MPFU,0,8000,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,MPFU,0,8000;New_NAME \"New_NAME\" true true false 8000 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,New_NAME,0,8000,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,New_NAME,0,8000;NONSPORTUSE \"Non-Sport Use Permitted\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,NONSPORTUSE,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,NONSPORTUSE,0,1;NUMCOURTS \"Number of Courts\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,NUMCOURTS,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,NUMCOURTS,-1,-1;OBJECTID_1 \"OBJECTID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,OBJECTID_1,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,OBJECTID_1,-1,-1;OBJECTID_12 \"OBJECTID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,OBJECTID_12,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,OBJECTID_12,-1,-1;OWNER \"Owner\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,OWNER,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,OWNER,0,5;Ownership_Maintenance_Primary_Asset_Filter \"Ownership_Maintenance_Primary_Asset_Filter\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,Ownership_Maintenance_Primary_Asset_Filter,-1,-1;Ownership_Maintenance_Priority_Filter \"Ownership_Maintenance_Priority_Filter\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,Ownership_Maintenance_Priority_Filter,-1,-1;PARK_ID \"Park ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PARK_ID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PARK_ID,-1,-1;REC_ID \"Park Rec Feature ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,REC_ID,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,REC_ID,-1,-1;PARTNER \"Partner\" true true false 5 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PARTNER,0,5,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PARTNER,0,5;PERFRMRA \"Performance Rate\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PERFRMRA,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PERFRMRA,-1,-1;PERFRMCONF \"Performance Rate Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PERFRMCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PERFRMCONF,-1,-1;PLAYLEVEL_NOTES \"Play Level Notes\" true true false 100 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PLAYLEVEL_NOTES,0,100,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PLAYLEVEL_NOTES,0,100;POLY_AREA \"Polygon Area\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,POLY_AREA,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,POLY_AREA,-1,-1;PRIMARY \"Primary Use\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PRIMARY,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PRIMARY,0,1;PROFCNCAT \"Profile Key Concatenation\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,PROFCNCAT,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,PROFCNCAT,0,50;RECPOLYID \"Recreation Poly ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,RECPOLYID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,RECPOLYID,0,50;REC_USE \"Recreation Use\" true true false 8 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,REC_USE,0,8,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,REC_USE,0,8;RECUSEID \"Recreation Use ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,RECUSEID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,RECUSEID,0,50;RMLIFE \"Remaining Life\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,RMLIFE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,RMLIFE,-1,-1;RMLIFECONF \"Remaining Life Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,RMLIFECONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,RMLIFECONF,-1,-1;REPLCSCONF \"Replacement Cost Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,REPLCSCONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,REPLCSCONF,-1,-1;REPLCSRA \"Replacement Cost Rate\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,REPLCSRA,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,REPLCSRA,-1,-1;REPLCSTOTL \"Replacement Cost Total\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,REPLCSTOTL,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,REPLCSTOTL,-1,-1;REPLRACONF \"Replacement Rate Confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,REPLRACONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,REPLRACONF,-1,-1;ROLLUPID \"Roll Up ID\" true true false 50 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,ROLLUPID,0,50,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,ROLLUPID,0,50;SCOREBOARD \"Scoreboard\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SCOREBOARD,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SCOREBOARD,0,1;SEATING \"Seating\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SEATING,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SEATING,0,1;SEATCAPCTY \"Seating Capacity\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SEATCAPCTY,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SEATCAPCTY,-1,-1;SACC \"Source Accuracy\" true true false 2 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SACC,0,2,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SACC,0,2;SACC_1 \"Source Accuracy\" true true false 2 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SACC_1,0,2,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SACC_1,0,2;SDATE \"Source Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SDATE,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SDATE,-1,-1;SDATE_1 \"Source Date\" true true false 8 Date 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SDATE_1,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SDATE_1,-1,-1;TCACAT \"TCA Category\" true true false 10 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,TCACAT,0,10,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,TCACAT,0,10;UNSCHEDUSE \"Unscheduled Use Permitted\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,UNSCHEDUSE,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,UNSCHEDUSE,0,1;WSHRMS \"Washrooms Available\" true true false 1 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,WSHRMS,0,1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,WSHRMS,0,1;WIDTH \"Width\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,WIDTH,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,WIDTH,-1,-1;WIDTHM \"Width\" true true false 8 Double 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,WIDTHM,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,WIDTHM,-1,-1;SIZE2CONF \"Width confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE2CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE2CONF,-1,-1;SIZE4CONF \"Width confidence\" true true false 2 Short 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE4CONF,-1,-1,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE4CONF,-1,-1;SIZE2UNIT \"Width Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE2UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE2UNIT,0,4;SIZE4UNIT \"Width Unit of measure\" true true false 4 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\sdfsdfsf,SIZE4UNIT,0,4,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,SIZE4UNIT,0,4;UNIQUE_ID \"UNIQUE_ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,UNIQUE_ID,-1,-1;Ownership_Filter \"Ownership_Filter\" true true false 255 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,Ownership_Filter,0,255;Maintenance_Filter \"Maintenance_Filter\" true true false 255 Text 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,Maintenance_Filter,0,255;UNIQUE_ID_1 \"UNIQUE_ID\" true true false 4 Long 0 0,First,#,C:\\Users\\an24517\\Desktop\\Test Maps\\TestMap_20230109\\TestMap_20230109\\TestMap_20230109.gdb\\non_playgrounds_Dissolve1,UNIQUE_ID_1,-1,-1",
                                   add_source="ADD_SOURCE_INFO")

    if dissed_3_:
        sdfsdfsf_Merge_2_ = arcpy.management.DeleteField(in_table=sdfsdfsf_Merge,
                                                             drop_field=["MEAN_X", "MEAN_Y", "FIRST_FIRST_PARK_ID",
                                                                         "FIRST_FIRST_LAND_ID", "X", "Y", "coord_sum",
                                                                         "Park_Land_ID", "ACCESSIBLE", "ADDBY",
                                                                         "ADDBY_1", "ADDDATE", "ADDDATE_1", "AREASQM",
                                                                         "SIZE3CONF", "SIZE3UNIT", "ASSETDESC",
                                                                         "ASSETGRP", "ASSETID_1", "ASSETSBGRP",
                                                                         "ASSETSBTYP", "ASSETSBTCP", "ASSETTYP",
                                                                         "ASSETRAW", "BDBACKSTP", "BDCLASS",
                                                                         "BDDUGOUTS", "BDMATINF", "BDMOUND",
                                                                         "BDFENOUTF", "BDBNCHPLYR", "BASELIFE",
                                                                         "BOATID", "CIV_ID", "COMMENTS", "SOURCE",
                                                                         "SOURCE_1", "EMERGSERV", "FCODE", "FENCE",
                                                                         "LOCGEN", "GENRECTYPE", "HEIGHTM", "HRMINTRST",
                                                                         "LAND_ID", "LANDID", "LEGACYID", "LENGTH",
                                                                         "LENGTHM", "SIZE1CONF", "SIZE1UNIT",
                                                                         "LIGHTING", "MAINTBY", "MEASURE_NOTES",
                                                                         "MODBY", "MODBY_1", "MODDATE", "MODDATE_1",
                                                                         "MPFU", "NONSPORTUSE", "OBJECTID_1",
                                                                         "OBJECTID_12",
                                                                         "Ownership_Maintenance_Primary_Asset_Filter",
                                                                         "Ownership_Maintenance_Priority_Filter",
                                                                         "PARK_ID", "REC_ID", "PARTNER", "PERFRMRA",
                                                                         "PERFRMCONF", "PLAYLEVEL_NOTES", "POLY_AREA",
                                                                         "PRIMARY", "PROFCNCAT", "RECPOLYID", "REC_USE",
                                                                         "RECUSEID", "ROLLUPID", "SCOREBOARD",
                                                                         "SEATING", "SEATCAPCTY", "SACC", "SACC_1",
                                                                         "SDATE", "SDATE_1", "TCACAT", "UNSCHEDUSE",
                                                                         "WSHRMS", "WIDTH", "WIDTHM", "SIZE2CONF",
                                                                         "SIZE4CONF", "SIZE2UNIT", "SIZE4UNIT",
                                                                         "UNIQUE_ID", "Ownership_Filter",
                                                                         "Maintenance_Filter", "UNIQUE_ID_1",
                                                                         "MERGE_SRC"], method="DELETE_FIELDS")[0]

    NonMPtoSP_Merge_SpatialJoin = fr"{OutputFGDB}\NonMPtoSP_Merge_SpatialJoin"
    if dissed_3_:
        arcpy.analysis.SpatialJoin(target_features=sdfsdfsf_Merge_2_, join_features=SDEADM_ADM_polling_district,
                                       out_feature_class=NonMPtoSP_Merge_SpatialJoin, join_operation="JOIN_ONE_TO_ONE",
                                       join_type="KEEP_ALL",
                                       match_option="INTERSECT", search_radius="", distance_field_name="")

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_2_ = arcpy.management.JoinField(in_data=NonMPtoSP_Merge_SpatialJoin, in_field="DISTNAME",
                                       join_table=population_index_table_csv, join_field="Column1",
                                       fields=["Population"])[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_8_ = arcpy.management.AddFields(in_table=NonMPtoSP_Merge_SpatialJoin_2_,
                                                                        field_description=[
                                                                            ["Lat", "DOUBLE", "Lat", "", "", ""],
                                                                            ["Long", "DOUBLE", "Long", "", "", ""],
                                                                            ["School_in_name", "TEXT", "School in Name",
                                                                             "255", "", ""], ["Ownership_final", "TEXT",
                                                                                              "Ownership Final", "255",
                                                                                              "", ""],
                                                                            ["Subcategory_1", "TEXT", "Subcategory 1",
                                                                             "255", "", ""],
                                                                            ["Subcategory_2", "TEXT", "Subcategory 2",
                                                                             "255", "", ""],
                                                                            ["Number_of_courts_final", "DOUBLE",
                                                                             "Number of Courts Final", "", "", ""],
                                                                            ["Asset_Name", "TEXT", "Asset Name", "255",
                                                                             "", ""],
                                                                            ["Condition", "TEXT", "Condition", "255",
                                                                             "", ""],
                                                                            ["DISTNAME_ID", "TEXT", "DISTNAME_ID",
                                                                             "255", "", ""]])[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_11_ = arcpy.management.CalculateGeometryAttributes(in_features=NonMPtoSP_Merge_SpatialJoin_8_,
                                                         geometry_property=[["Lat", "CENTROID_Y"]], length_unit="",
                                                         area_unit="",
                                                         coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
                                                         coordinate_format="DD")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_5_ = arcpy.management.CalculateGeometryAttributes(in_features=NonMPtoSP_Merge_SpatialJoin_11_,
                                                         geometry_property=[["Long", "CENTROID_X"]], length_unit="",
                                                         area_unit="",
                                                         coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
                                                         coordinate_format="DD")[0]

    if dissed_3_:
        merge2_2_ = arcpy.management.JoinField(in_data=NonMPtoSP_Merge_SpatialJoin_5_, in_field="MAT",
                                                   join_table=material_codes, join_field="Label", fields=["Name"])[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_4_ = arcpy.management.CalculateField(in_table=merge2_2_, field="Condition", expression="cf(!CONDIT!)",
                                            expression_type="PYTHON3", code_block="""def cf(a):
    if a == 0:
        return 'Very Good'
    elif a ==25:
        return 'Good'
    elif a == 50:
        return 'Fair'
    elif a == 75:
        return 'Poor'
    elif a == 100:
        return 'Critical'
        """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_6_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_4_, field="Number_of_courts_final",
                                            expression="cf(!New_NAME!,!NUMCOURTS!)", expression_type="PYTHON3",
                                            code_block="""def cf(a,b):
    if a is None:
        return 1
    elif 'Half' in a:
        return 0.5
    elif 'Standard' in a:
        return 0.5
    elif b is None or b == 0:
        return 1
    else:
        return b""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_3_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_6_, field="School_in_name",
                                            expression="cf(!LOCATION!)", expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return 'No'
    elif 'school' in a.lower():
        return 'Yes'
    else:
        return 'No'""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_9_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_3_, field="Ownership_final",
                                            expression="cf(!OWNER!)", expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return 'Halifax Regional Municipality'
    a = a.lower()
    if a == 'fed':
        return 'Federal Government'
    elif a == 'hrm':
        return 'Halifax Regional Municipality'
    elif a == 'hrsb':
        return 'Halifax Regional School Board'
    elif a =='hw':
        return 'Halifax Water'
    elif a =='nspi':
        return 'Nova Scotia Power'
    elif a =='priv':
        return 'Privately Owned'
    elif a =='prov':
        return 'Province'
    elif a=='un':
        return 'Unknown'
    else:
        return 'Halifax Regional Municipality'
    """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_12_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_9_, field="Subcategory_1",
                                            expression="cf(!New_NAME!,!BOATNAME!)", expression_type="PYTHON3",
                                            code_block="""def cf(a,b):
    if b is None:
        if a is None:
            return 'NOT PHASE 1'
        elif 'Half'.lower() in a.lower() or 'Standard'.lower() in a.lower():
            return 'Basketball Court'.title()
        else:
            return a.title()
    elif 'DOCK'.lower() in b.lower():
        return 'Boat Dock'
    elif 'LAUNCH'.lower() in b.lower():
        return 'Boat Launch'""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_12_, field="Subcategory_1",
                                            expression="cf(!LOCATION!,!Subcategory_1!)", expression_type="PYTHON3",
                                            code_block="""def cf(a,b):
    if a is None and b is None:
        return 'NOT PHASE 1'
    elif a is None and b is not None:
        return b
    if 'SKATEPARK' in a:
        return 'Skatepark'
    if 'ALL-WEATHER' in a:
        return 'All-Weather Sports Field'
    if 'ALL-WEATHER' not in a and 'SKATEPARK' not in a:
        return b
""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    NonMPtoSP_Merge_SpatialJoin_GroupByProximity = "\\\\msfs202\\Common\\hrmshare\\ICT\\ICT BIDS\\ETL Data Exchange\\Parks and Rec Assets\\GIS and Python Scripts\\Dashboard Upates_20230119\\output.gdb\\NonMPtoSP_Merge_SpatialJoin_GroupByProximity"
    if dissed_3_:
        arcpy.gapro.GroupByProximity(input_layer=NonMPtoSP_Merge_SpatialJoin_7_,
                                         output=NonMPtoSP_Merge_SpatialJoin_GroupByProximity,
                                         spatial_relationship="NEAR_PLANAR", spatial_near_distance="10 Meters",
                                         temporal_relationship="NONE", temporal_near_distance="")

    if dissed_3_:
        Updated_Input_Features = arcpy.management.AddXY(in_features=NonMPtoSP_Merge_SpatialJoin_GroupByProximity)[0]

    final_asset_point_outputfina = fr"{OutputFGDB}\final_asset_point_outputfina"
    if dissed_3_:
        arcpy.management.Dissolve(in_features=Updated_Input_Features,
                                      out_feature_class=final_asset_point_outputfina,
                                      dissolve_field=["GROUP_ID", "Subcategory_1"],
                                      statistics_fields=[["POINT_X", "MEAN"], ["POINT_Y", "MEAN"]],
                                      multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    final_asset_point_outputfina_XYTableToPoint = fr"{OutputFGDB}\final_asset_point_outputfina_XYTableToPoint"
    if dissed_3_:
        arcpy.management.XYTableToPoint(in_table=final_asset_point_outputfina,
                                            out_feature_class=final_asset_point_outputfina_XYTableToPoint,
                                            x_field="MEAN_POINT_X", y_field="MEAN_POINT_Y", z_field="",
                                            coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]];19877400 -10001100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision")

    if dissed_3_:
        final_asset_point_outputfinal_asset_point_output_GroupByProximity_3_ = arcpy.management.AddField(in_table=final_asset_point_outputfina_XYTableToPoint, field_name="Join_Field",
                                      field_type="TEXT", field_precision=None, field_scale=None, field_length=None,
                                      field_alias="Join_Field", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED", field_domain="")[0]

    if dissed_3_:
        final_asset_point_outputfinal_asset_point_output_GroupByProximity_5_ = arcpy.management.CalculateField(
                in_table=final_asset_point_outputfinal_asset_point_output_GroupByProximity_3_, field="Join_Field",
                expression="cf(!GROUP_ID!,!Subcategory_1!)", expression_type="PYTHON3", code_block="""def cf(a,b):
    return str(a)+' - '+str(b)""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        final_asset_point_outputfinal_asset_point_output_GroupByProximity_2_ = arcpy.management.AddField(in_table=Updated_Input_Features, field_name="Join_Field", field_type="TEXT",
                                      field_precision=None, field_scale=None, field_length=None,
                                      field_alias="Join_Field", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED", field_domain="")[0]

    if dissed_3_:
        final_asset_point_outputfinal_asset_point_output_GroupByProximity_4_ = arcpy.management.CalculateField(
                in_table=final_asset_point_outputfinal_asset_point_output_GroupByProximity_2_, field="Join_Field",
                expression="cf(!GROUP_ID!,!Subcategory_1!)", expression_type="PYTHON3", code_block="""def cf(a,b):
    return str(a)+' - '+str(b)""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        final_asset_point_outputfina_XYTableToPoint_2_ = arcpy.management.JoinField(
            in_data=final_asset_point_outputfinal_asset_point_output_GroupByProximity_5_,
            in_field="Join_Field",
            join_table=final_asset_point_outputfinal_asset_point_output_GroupByProximity_4_,
            join_field="Join_Field",
            fields=[
                    "Asset_Name", "ASSETCODE", "ASSETID", "ASSETSTAT", "BOATNAME", "CLASS",
                   "CONDICONF", "CONDIT", "CONDITDTE", "Condition", "CRIT", "CRITCONF",
                   "DIST_ID", "DISTNAME", "DISTNAME_ID", "GLOBALID_1", "GROUP_ID", "INSTCS",
                   "INSTCSCONF", "INSTDATE", "INSTYR", "INSTYRCONF", "Join_Count",
                   "Join_Field", "Lat", "LOCATION", "Long", "MAT", "MATCONF", "Name",
                   "New_NAME", "Number_of_courts_final", "NUMCOURTS", "OBJECTID", "OWNER",
                   "Ownership_final", "POINT_X", "POINT_Y", "Population", "REPLCSCONF",
                   "REPLCSRA", "REPLCSTOTL", "REPLRACONF", "RMLIFE", "RMLIFECONF",
                   "School_in_name", "Subcategory_1", "Subcategory_2", "TARGET_FID",
                   "WARNTYLAB", "WARRANTYDATE"
            ]
        )[0]

    if dissed_3_:
        final_asset_point_outputfina_XYTableToPoint_4_ = arcpy.management.CalculateGeometryAttributes(
            in_features=final_asset_point_outputfina_XYTableToPoint_2_,
            geometry_property=[["Lat", "POINT_X"]],
            length_unit="",
            area_unit="",
            coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
            coordinate_format="DD"
        )[0]

    if dissed_3_:
        final_asset_point_outputfina_XYTableToPoint_5_ = arcpy.management.CalculateGeometryAttributes(
            in_features=final_asset_point_outputfina_XYTableToPoint_4_,
            geometry_property=[["Long", "POINT_Y"]],
            length_unit="",
            area_unit="",
            coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
            coordinate_format="DD"
        )[0]

    if dissed_3_:
        Final_Output = arcpy.management.CalculateField(in_table=final_asset_point_outputfina_XYTableToPoint_5_,
                                                           field="Subcategory_2", expression="cf(!Subcategory_1!)",
                                                           expression_type="PYTHON3", code_block="""def cf(a):
    if a == 'Rugby Field':
        return 'Sports Field'
    elif a == 'Soccer Field':
        return 'Sports Field'
    elif a == 'Lacrosse Field':
        return 'Sports Field'
    elif a == 'Football Field':
        return 'Sports Field'
    elif a == 'All-Weather Sports Field':
        return 'Sports Field'
    else:
        return ''""",
                                                       field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_13, Count_4_ = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=Final_Output, selection_type="NEW_SELECTION",
                where_clause="(Subcategory_1 IS NULL And Subcategory_2 = '') Or Subcategory_1 = 'NOT PHASE 1'",
                invert_where_clause="")

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_, Count_5_ = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=NonMPtoSP_Merge_SpatialJoin_13, selection_type="ADD_TO_SELECTION",
                where_clause="Subcategory_1 IS NULL And Subcategory_2 IS NULL", invert_where_clause="")

    if dissed_3_:
        Updated_Input_With_Rows_Removed_4_ = arcpy.management.DeleteRows(in_rows=NonMPtoSP_Merge_SpatialJoin_)[0]

    if dissed_3_:
        final_asset_point_fina = arcpy.conversion.FeatureClassToFeatureClass(
                in_features=Updated_Input_With_Rows_Removed_4_,
                out_path=OutputFGDB,
                out_name="final_asset_point_fina",
            )[0]

    if dissed_3_:
        final_asset_point_fina_2_ = arcpy.management.CalculateField(in_table=final_asset_point_fina, field="DISTNAME_ID",
                                            expression="cf(!DIST_ID!,!DISTNAME!)", expression_type="PYTHON3",
                                            code_block="""def cf(a, b):
    return str(a) + ' - ' + str(b)
""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        final_asset_point_fina_3_ = arcpy.management.CalculateField(in_table=final_asset_point_fina_2_, field="Asset_Name",
                                            expression="cf(!LOCATION!,!BOATNAME!)", expression_type="PYTHON3",
                                            code_block="""def cf(a,b):
    if b is None:
        return str(a)
    else:
        return str(b)""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        final_asset_point_outputfina1 = arcpy.management.AddFields(in_table=final_asset_point_fina_3_,
                                                                       field_description=[["Asset_Name_Final_2", "TEXT",
                                                                                           "Asset_Name_Final_2", "255",
                                                                                           "", ""],
                                                                                          ["AssetName_FIN", "TEXT",
                                                                                           "AssetName_FIN", "255", "",
                                                                                           ""]])[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_14 = arcpy.management.CalculateField(in_table=final_asset_point_outputfina1, field="Asset_Name_Final_2",
                                            expression="cf(!Asset_Name!)", expression_type="PYTHON3", code_block="""def cf(a):
    z = a.lower()
    if 'rply' in z:
        re=z.split('rply')
        res=str(re[0])
        output=res[:-3]
        return output.upper() +' Playground'.upper()
    else:
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_12_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_14, field="Asset_Name_Final_2",
                                            expression="isDuplicate(!Asset_Name_Final_2!)", expression_type="PYTHON3",
                                            code_block="""uniqueList = []
def isDuplicate(a):
    b = a.upper()
    if b not in uniqueList:
        uniqueList.append(b)
        return b
    else:
        return check(a,'2')
        
def check(a,b):
    x = a+' '+b
    if x.upper() not in uniqueList:
        uniqueList.append(x.upper())
        return x.upper()
    else:
        z = int(b)+1
        return check(a,str(z))""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        final_asset_point_outputfina1_2_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_7_12_, field="AssetName_FIN",
                                            expression="!Asset_Name_Final_2!", expression_type="PYTHON3", code_block="",
                                            field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        asset_name_joined = arcpy.conversion.FeatureClassToFeatureClass(in_features=final_asset_point_outputfina1_2_,
                                                        out_path=OutputFGDB, out_name="asset_name_joined")[0]

    NonMPtoSP_Merge_SpatialJoin_2s = fr"{OutputFGDB}\NonMPtoSP_Merge_SpatialJoin_2s"
    if dissed_3_:
        arcpy.analysis.SpatialJoin(target_features=asset_name_joined, join_features=SDEADM_ADM_gsa_polygon,
                                       out_feature_class=NonMPtoSP_Merge_SpatialJoin_2s,
                                       join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL",
                                       match_option="INTERSECT")

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_2_7_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_2s, field="GSA_NAME",
                                            expression="!GSA_NAME!.title()", expression_type="PYTHON3", code_block="",
                                            field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_2__201 = arcpy.management.AlterField(in_table=NonMPtoSP_Merge_SpatialJoin_2_7_, field="Name",
                                        new_field_name="Material_Name", new_field_alias="Material_Name", field_type="",
                                        field_length=10485758,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    NonMPtoSP_Merge_SpatialJoin_6 = fr"{OutputFGDB}\NonMPtoSP_Merge_SpatialJoin_6"
    if dissed_3_:
        arcpy.analysis.SpatialJoin(target_features=NonMPtoSP_Merge_SpatialJoin_2__201,
                                       join_features=rural_rec_commuter_areas,
                                       out_feature_class=NonMPtoSP_Merge_SpatialJoin_6,
                                       join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL",
                                       match_option="INTERSECT")

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_6_3_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_6, field="Rural_Rec_Commuter_Area",
                                            expression="cf(!Rural_Rec_Commuter_Area!)", expression_type="PYTHON3",
                                            code_block="""def cf(a):
    if a == 'EAST':
        return 'Commuter East'
    elif a == 'WEST':
        return 'Commuter West'
    elif a == 'EASTERN SHORE':
        return 'Eastern Shore'
    elif a == 'MUSQUODOBIIT VALLEY':
        return 'Musquodobit Valley'
    else:
        return 'Regional Centre'
   """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    NonMPtoSP_Merge_SpatialJoin_7_7_ = fr"{OutputFGDB}\NonMPtoSP_Merge_SpatialJoin_7"
    if dissed_3_:
        arcpy.analysis.SpatialJoin(target_features=NonMPtoSP_Merge_SpatialJoin_6_3_,
                                       join_features=SDEADM_LND_hrm_park,
                                       out_feature_class=NonMPtoSP_Merge_SpatialJoin_7_7_,
                                       join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL",
                                       match_option="INTERSECT")

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_8_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_7_7_, field="PARK_NAME",
                                            expression="cf(!PARK_NAME!)", expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return ''
    else:
        return a.title()""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_6_ = arcpy.management.JoinField(in_data=NonMPtoSP_Merge_SpatialJoin_7_8_, in_field="Asset_Name_Final_2",
                                       join_table=object_id_table, join_field="Asset_Name", fields=["OBJECTID"])[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_13_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_7_6_, field="Asset_Name_Final_2",
                                            expression="!Asset_Name_Final_2!.title()", expression_type="PYTHON3",
                                            code_block="", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7 = arcpy.management.AddField(in_table=NonMPtoSP_Merge_SpatialJoin_7_13_, field_name="Final_OID",
                                      field_type="LONG", field_precision=None, field_scale=None, field_length=None,
                                      field_alias="Final Object ID", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED")[0]

    if dissed_3_:
        merge2_SpatialJoin3_Layer5_S1_3_merge2_SpatialJoin3_Layer5_S1_3_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_7, field="Final_OID",
                                            expression="SequentialNumber(!OBJECTID_1!)", expression_type="PYTHON3",
                                            code_block="""# Calculates a sequential number
rec= 10000
def SequentialNumber(a):
    if a is None:
        global rec
        pStart = 1
        pInterval = 1
        if (rec == 0):
            rec = pStart
        else:
            rec = rec + pInterval
        return rec
    else: 
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_2_ = arcpy.management.AddField(
            in_table=merge2_SpatialJoin3_Layer5_S1_3_merge2_SpatialJoin3_Layer5_S1_3_,
                                      field_name="asset_location", field_type="TEXT", field_precision=None,
                                      field_scale=None, field_length=None, field_alias="asset_location",
                                      field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")[
                0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_15_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_7_2_, field="asset_location",
                                            expression="cf(!Asset_Name_Final_2!,!PARK_NAME!) ",
                                            expression_type="PYTHON3", code_block="""import re
def cf(a,b):
    if b is None or b == '':
        return 'Not located in a Municipal Park'
    else:
        return b.title()
    """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_14_ = arcpy.management.AddField(in_table=NonMPtoSP_Merge_SpatialJoin_7_15_, field_name="Install_Year",
                                      field_type="TEXT", field_precision=None, field_scale=None, field_length=None,
                                      field_alias="Install_Year", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED", field_domain="")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_16_ = arcpy.management.CalculateField(in_table=NonMPtoSP_Merge_SpatialJoin_7_14_, field="Install_Year",
                                            expression="cf(!INSTYR!)", expression_type="PYTHON3", code_block="""def cf(a):
    if a is None:
        return ''
    elif str(a) == '0':
        return ''
    else:
        return a""", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_11_ = arcpy.management.DeleteField(
                in_table=NonMPtoSP_Merge_SpatialJoin_7_16_,
                drop_field=["Join_Count", "TARGET_FID", "Join_Count_1", "TARGET_FID_1", "Join_Count_12",
                            "TARGET_FID_12", "GROUP_ID",
                            "MEAN_POINT_X", "MEAN_POINT_Y", "Join_Field", "Asset_Name", "ASSETCODE", "BASELIFE",
                            "BOATNAME", "CONDIT",
                            "coord_sum", "CRIT", "CRITCONF", "FIRST_FIRST_LAND_ID", "FIRST_FIRST_PARK_ID",
                            "GLOBALID_1", "GROUP_ID_1",
                            "INSTCS", "INSTCSCONF", "INSTYR", "Join_Count_12_13", "Join_Field_1", "LAND_ID",
                            "LANDID", "LOCATION",
                            "Maintenance_Filter", "MAT", "MEAN_X", "MEAN_Y", "MERGE_SRC", "New_NAME", "NUMCOURTS",
                            # "OBJECTID",
                            "Ownership_Filter", "Park_Land_ID", "PERFRMCONF", "PERFRMRA", "POINT_X", "POINT_Y",
                            "REPLCSCONF",
                            "REPLCSRA", "REPLCSTOTL", "REPLRACONF", "TARGET_FID_12_13", "TCACAT", "UNIQUE_ID",
                            "UNIQUE_ID_1",
                            "AssetName_FIN", "GSA_KEY", "FCODE", "MUN_CODE", "GSA_REM", "SOURCE", "DATE_ACT",
                            "SYS_DATE", "TECH_MOD",
                            "TECH_ACT", "Shape_Length_1", "Shape_Area_1", "PARK_ID_1", "OWNER_1", "HRMINTRST",
                            "HECTARES",
                            "NAMESTATUS", "NAMEAPRDTE", "PARK_MAINT", "GROUP_ID_12", "ADDBY", "MODBY", "ADDDATE",
                            "MODDATE", "SDATE",
                            "SOURCE_1", "SACC", "PARK_TYPE", "DEVELOPED", "CIVIC_ID", "Shape_Length_12",
                            "Shape_Area_12"],
                method="DELETE_FIELDS")[0]

    if dissed_3_:
        final_output_final_output_4_ = arcpy.management.AlterField(in_table=NonMPtoSP_Merge_SpatialJoin_7_11_, field="Material_Name",
                                        new_field_name="Material", new_field_alias="Material", field_type="",
                                        field_length=10485758,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    if dissed_3_:
        Updated_Input_Table_2_ = arcpy.management.AddField(in_table=final_output_final_output_4_, field_name="MAINRECUSE", field_type="TEXT",
                                      field_precision=None, field_scale=None, field_length=None,
                                      field_alias="Main Park Facility Use", field_is_nullable="NULLABLE",
                                      field_is_required="NON_REQUIRED")[0]

    if dissed_3_:
        final_output_final_output_5_ = arcpy.management.CalculateField(in_table=Updated_Input_Table_2_, field="MAINRECUSE",
                                            expression="!Subcategory_1!", expression_type="PYTHON3", code_block="",
                                            field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_5_ = arcpy.management.AlterField(in_table=final_output_final_output_5_, field="GSA_NAME",
                                        new_field_name="Community_Name", new_field_alias="Community Name",
                                        field_type="", field_length=40,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    if dissed_3_:
        NonMPtoSP_Merge_SpatialJoin_7_4_ = arcpy.management.AlterField(in_table=NonMPtoSP_Merge_SpatialJoin_7_5_, field="Asset_Name_Final_2",
                                        new_field_name="Asset_name", new_field_alias="Asset_name", field_type="",
                                        field_length=255,
                                        clear_field_alias="DO_NOT_CLEAR")[0]

    if dissed_3_:
        final_phase_1_assets = arcpy.conversion.FeatureClassToFeatureClass(
                in_features=NonMPtoSP_Merge_SpatialJoin_7_4_,
                out_path=OutputFGDB,
                out_name="final_phase_1_assets",
            )[0]

    if dissed_3_:
        final_phase_1_assets_Spatial_3_ = arcpy.management.CalculateField(in_table=final_phase_1_assets, field="OWNER", expression="cf(!OWNER!)",
                                            expression_type="PYTHON3", code_block="""def cf(a):
    if 'HRM' in a: 
        return 'Halifax'
    elif 'PROV' in a:
        return 'Province'
    elif 'HRSB' in a:
        return 'Halifax Regional School Board'
    elif 'PRIV' in a:
        return 'Private'
    else:
        return 'No Data'
    """, field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    final_phase_1_assets_3_ = arcpy.management.DeleteField(
        in_table=final_phase_1_assets_Spatial_3_,
        drop_field=["Join_Count", "TARGET_FID", "Subcategory_12", "PARK_NAME", "OBJECTID_12", "Final_OID"],
        method="DELETE_FIELDS"
    )[0]

    arcpy.conversion.TableToExcel(
        Input_Table=final_phase_1_assets_3_,
        Output_Excel_File=final_asset_point_output_xlsx,
        Use_field_alias_as_column_header="NAME",
        Use_domain_and_subtype_description="DESCRIPTION"
    )

    final_table_row_count = int(arcpy.GetCount_management(final_phase_1_assets_3_)[0])
    loggy.info(f"Final table row count: {final_table_row_count}.")

    if final_table_row_count < 1000:
        raise ValueError(f"Final table row count: {final_table_row_count}.\t(This should be >1000.)")

    asset_types = [row[0] for row in arcpy.da.SearchCursor(final_phase_1_assets_3_, "Subcategory_1", sql_clause=(
        "DISTINCT Subcategory_1", "ORDER BY Subcategory_1"))]
    loggy.info(f"Assets included in final feature:\n\t{', '.join(asset_types)}")

    if "Playground" not in asset_types:
        raise IndexError(f"Did NOT find PLAYGROUNDS in the final report. Assets found: {', '.join(asset_types)}")


if __name__ == '__main__':
    import traceback
    import sys

    print(f"START Time: {datetime.now()}")
    loggy.info(f"\nSTART Time: {datetime.now()}")

    try:

        if arcpy.Exists(OutputFGDB):
            loggy.info(f"Deleting exists workspace, {OutputFGDB}...")
            arcpy.Delete_management(OutputFGDB)

        gdb_dir = os.path.dirname(OutputFGDB)
        gdb_name = os.path.basename(OutputFGDB)
        arcpy.CreateFileGDB_management(gdb_dir, gdb_name).getOutput(0)

        create_report()

    except arcpy.ExecuteError:
        arcpy_msgs = arcpy.GetMessages(2)
        loggy.error(f"ARCPY ERROR: {arcpy_msgs}")

    except Exception as e:
        loggy.error(f"ERROR: {e}")

        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]

        pymsg = f"PYTHON ERRORS:\nTraceback Info:\n{tbinfo}\nError Info:\n    {sys.exc_info()[0]}: {sys.exc_info()[1]}"

        loggy.error(pymsg)

    loggy.info(f"END Time: {datetime.now()}")
    loggy.info("\n")
