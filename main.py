import arcpy
import os
import configparser

import numpy as np
import pandas as pd

from utils import domain_mapping, create_fgdb
from logger import function_logger as loggy
from logger import logger as func_logger

arcpy.SetLogHistory(False)
arcpy.env.overwriteOutput = True

loggy.setLevel("INFO")

config = configparser.ConfigParser()
config.read("config.ini")

EXCEL_OUTPUT = config.get("options", "EXCEL_OUTPUT")

SDE = config.get("options", "SERVER_SDE")
REFERENCE_GDB = config.get("options", "REFERENCE_GDB")

WORKSPACE_GDB = config.get("options", "WORKSPACE_GDB")

BOAT_FACILITIES = os.path.join(SDE, "SDEADM.AST_boat_facility")
REC_POINTS = os.path.join(SDE, "SDEADM.LND_park_recreation_feature")
REC_POLYS = os.path.join(SDE, "SDEADM.LND_outdoor_rec_poly")
POLLING_DISTRICTS = os.path.join(SDE, "SDEADM.ADM_electoral_boundaries", "SDEADM.ADM_polling_district")

PARKS = os.path.join(SDE, "SDEADM.LND_hrm_parcel_parks", "SDEADM.LND_hrm_park")
COMMUNITIES = os.path.join(SDE, "SDEADM.ADM_gsa_boundaries", "SDEADM.ADM_gsa_polygon")
RURAL_COMM_AREAS = os.path.join(REFERENCE_GDB, "rural_rec_commuter_areas")

POPULATION_LOOKUP = os.path.join(REFERENCE_GDB, "population_index_table_csv")


@func_logger
def rec_feature_info(rec_feature, rec_poly, output_workspace):
    # Currently spatial joins rec polys within 1m of a rec feature
    # Join Rec feature to rec poly - need local features for successful one-to-many relationship output

    loggy.info(f"\nJoining rec feature to rec polys...")

    rec_feature_layer = arcpy.MakeFeatureLayer_management(rec_feature, "rec_feature_layer").getOutput(0)

    # Join rec feature to RECPOLY ON RECPOLYID
    arcpy.AddJoin_management(
        in_layer_or_view=rec_feature_layer,
        in_field="RECPOLYID",
        join_table=rec_poly,
        join_field="RECPOLYID",
        join_type="KEEP_COMMON"  # KEEP_COMMON, KEEP_ALL
    )
    loggy.info(f"\tJoin complete.")

    joined_data = arcpy.Select_analysis(
        rec_feature_layer,
        os.path.join(output_workspace, "rec_features_and_polys")
    ).getOutput(0)

    return joined_data


@func_logger
def boat_info(boat_facilities):
    # Get boat facilities owned by HRM
    loggy.info(f"\nGetting HRM boat facilities...")

    hrm_boats = arcpy.Select_analysis(
        boat_facilities,
        os.path.join("memory", "hrm_boat_facilities"),
        "OWNER='HRM'"
    ).getOutput(0)

    return hrm_boats


@func_logger
def merge_features(features: list, merged_feature_name: str, output_workspace):
    loggy.info(f"Merging: {', '.join(features)} to\n\t {os.path.join(output_workspace, merged_feature_name)}")

    # Merge GP tool: adds features as new rows and columns from each feature as new columns
    merged_feature = arcpy.Merge_management(
        inputs=features,
        output=os.path.join(output_workspace, merged_feature_name),
        add_source="NO_SOURCE_INFO"
    ).getOutput(0)
    return merged_feature


@func_logger
def add_location_data(feature, workspace):
    """
    - Add district, community, park info.
    :param feature:
    :param workspace:
    :return:
    """

    final_feature_output = os.path.join(workspace, "features_with_location_data")

    # CIVIC_ID on rec feature, CIV_ID on boat facility --> 4 features don't have a civic/civ id
    loggy.info(f"\nAdding district data to {feature}...")
    district_join = arcpy.SpatialJoin_analysis(
        target_features=feature,
        join_features=POLLING_DISTRICTS,
        out_feature_class=os.path.join("memory", "features_with_district_data"),
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT",
        search_radius="",
        distance_field_name=""
    )[0]

    loggy.info(f"\nAdding community data to {feature}...")
    community_join = arcpy.SpatialJoin_analysis(
        target_features=district_join,
        join_features=COMMUNITIES,
        out_feature_class=os.path.join("memory", "features_with_community_data"),
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT",
        search_radius="",
        distance_field_name=""
    )

    loggy.info(f"\nAdding Rural Recreation Commuter Area data to {feature}...")
    commuter_join = arcpy.SpatialJoin_analysis(
        target_features=community_join,
        join_features=RURAL_COMM_AREAS,
        out_feature_class=os.path.join("memory", "features_with_commuter_data"),
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT",
        search_radius="",
        distance_field_name=""
    )[0]

    loggy.info(f"\nAdding parks data to {feature}...")
    arcpy.SpatialJoin_analysis(
        target_features=commuter_join,
        join_features=PARKS,
        out_feature_class=final_feature_output,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT",
        search_radius="",
        distance_field_name=""
    )

    loggy.info("\nAdding district population info...")
    arcpy.JoinField_management(
        in_data=final_feature_output,
        in_field="DISTNAME",
        join_table=POPULATION_LOOKUP,
        join_field="Column1",
        fields=["Population"]
    )

    return final_feature_output


@func_logger
def add_lat_long(feature):
    # Calculate geometry attributes gp tool
    loggy.info(f"\nAdding Lat and Long values to {feature}...")

    arcpy.CalculateGeometryAttributes_management(
        in_features=feature,
        geometry_property=[["Lat", "POINT_Y"], ["Long", "POINT_X"]],
        length_unit="",
        area_unit="",
        coordinate_system="PROJCS[\"NAD_1983_CSRS_2010_MTM_5_Nova_Scotia\",GEOGCS[\"GCS_North_American_1983_CSRS_2010\",DATUM[\"D_North_American_1983_CSRS\",SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",25500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-64.5],PARAMETER[\"Scale_Factor\",0.9999],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]",
        coordinate_format="DD"
    )


if __name__ == '__main__':

    try:
        # SPATIAL ANALYSIS
        # Get rec feature+poly info
        rec_feature_and_polys = rec_feature_info(REC_POINTS, REC_POLYS, WORKSPACE_GDB)

        # Get HRM boat facilities
        hrm_boat_facilities = boat_info(BOAT_FACILITIES)

        # Merge assets
        merged_assets = merge_features(
            [rec_feature_and_polys, hrm_boat_facilities],
            "merged_feature",
            WORKSPACE_GDB
        )
        # TODO: Model's merge feature contains NO boat features
        # TODO: Could append boat facilities and map the fields

        # Add reference data: District Info. and populations, community, park,
        feature_with_reference_data = add_location_data(merged_assets, WORKSPACE_GDB)

        # Get x,y coordinates
        add_lat_long(feature_with_reference_data)

        # ADD ATTRIBUTE DATA
        location_data_feature = os.path.join(WORKSPACE_GDB, "features_with_location_data")

        # Translate Domain values to codes: condition, material, MAINRECUSE (subtype - check domains),
        # owner_domain_mapping = domain_mapping("AAA_asset_owner", SDE)
        condition_domain_mapping = domain_mapping("AAA_asset_condrat", SDE)
        condition_confidence_mapping = domain_mapping("AAA_asset_conf", SDE)
        material_domain_mapping = domain_mapping("LND_recreation_material", SDE)  # TODO: Doesnt get WDCH?
        boat_facility_mapping = domain_mapping("AST_boatfacility_material", SDE)
        asset_stat_mapping = domain_mapping("AAA_asset_stat", SDE)

        material_domain_mapping.update(boat_facility_mapping)

        owner_domain_mapping = {'HRM': 'Halifax', 'PROV': 'Province of Nova Scotia', 'PRIV': 'Private Person, Business, Organization or Agency', 'HW': 'Halifax Water', 'DND': 'Department of National Defense', 'FED': 'Federal', 'NSPI': 'Nova Scotia Power', 'CN': 'Canadian National', 'HDBC': 'Halifax-Dartmouth Bridge Commission', 'CCGRD': 'Canadian Coast Guard', 'CNDO': 'Condominium Corporation', 'CSAP': 'Conseil scolaire acadien provincial', 'HIAA': 'Halifax International Airport Authority', 'HRSB': 'Halifax Regional School Board', 'UN': 'Unknown', 'NA': 'Not Applicable', 'NTO': 'Not Taken Over', 'TPA': 'Third Party Agreement'}

        feature_rows = [row for row in arcpy.da.SearchCursor(location_data_feature, "*")]
        feature_fields = [x.name for x in arcpy.ListFields(location_data_feature)]

        df = pd.DataFrame(feature_rows, columns=feature_fields)

        loggy.info("Renaming columns...")
        df.rename(
            columns={
                'NAME': 'Rural_Rec_Commuter_Area',
                "GSA_NAME": 'Community_Name',
                'SDEADM_LND_park_recreation_feature_REC_TYPE': "REC_TYPE",

                "SDEADM_LND_outdoor_rec_poly_CLASS": "CLASS",
                'SDEADM_LND_park_recreation_feature_NUM_COURTS': "NUM_COURTS",

                "OWNER": "AST_boat_facility_OWNER",
                "ASSETCODE": "AST_boat_facility_ASSETCODE",

                "SDEADM_LND_park_recreation_feature_REC_NAME": "REC_NAME",
                "SDEADM_LND_park_recreation_feature_MAINRECUSE": "MAINRECUSE",

                "SDEADM_LND_outdoor_rec_poly_OWNER": "OWNER",

            },
            inplace=True
        )

        def courts_count(row):
            if row["MAINRECUSE"]:
                if "HALF" in row["MAINRECUSE"]:
                    return 0.50

                elif "STANDARD" in row["MAINRECUSE"]:
                    return 1

            return row["NUM_COURTS"]

        def subcat_one(row):
            subcat_one_values = [
                "BASEBALL", "BASKETBALL FULL COURT", "BASKETBALL HALF COURT", "CRICKET", "FOOTBALL", "GENERAL PLAYGROUND",
                "LACROSSE", "LAWN BOWLING", "NON STANDARD COURT", "OUTDOOR GYM", "PICKLEBALL", "RUGBY", "RUNNING TRACK",
                "SOCCER", "SPRAY POOL", "TENNIS", "VOLLEYBALL", "SPORTSFIELD"
            ]

            if row["AST_boat_facility_ASSETCODE"]:
                if row["AST_boat_facility_ASSETCODE"] in ("BDK", "BOL"):
                    mapping = {"BDK": "Boat Dock", "BOL": "Boat Launch"}
                    return mapping.get(row["AST_boat_facility_ASSETCODE"])

            elif row["MAINRECUSE"] in subcat_one_values:
                return row["MAINRECUSE"]

            elif row["Asset_name"]:
                if 'SKATEPARK' in row["Asset_name"]:
                    return "Skatepark"

                elif "SOCCER" in row["Asset_name"]:
                    return "Soccer Field"

                elif "Basketball" in row["Asset_name"]:
                    return "Basketball Court"

                elif row["Asset_name"] in ['RUGBY', 'LACROSSE', 'FOOTBALL']:
                    return row["MAINRECUSE"]

            else:
                return ""

        def subcat_two(row):
            if row["Asset_name"]:
                if " FIELD" in row["Asset_name"]:
                    return "Sports Field"

            if row["MAINRECUSE"]:
                if "PLAYFIELD" in row["MAINRECUSE"]:
                    return "Sports Field"

            return ""


        loggy.info("Updating column values...")
        df["OWNER"] = df.apply(lambda row: row["OWNER"] if row["OWNER"] else row["AST_boat_facility_OWNER"], axis=1)
        df["Material"] = df.apply(lambda row: row["MAT"] if row["MAT"] else row['SDEADM_LND_outdoor_rec_poly_MAT'], axis=1)

        df["Condition"] = np.where(df["CONDIT"].notnull(), df["CONDIT"], df['SDEADM_LND_outdoor_rec_poly_CONDIT'])
        df["Install_Year"] = np.where(df['INSTYR'].notnull(), df['INSTYR'], df['SDEADM_LND_outdoor_rec_poly_INSTYR'])
        df['asset_location'] = np.where(df['LOCATION'].notnull(), df['LOCATION'], df['SDEADM_LND_outdoor_rec_poly_LOCATION'])
        df['Ownership_final'] = np.where(df['OWNER'].notnull(), df['OWNER'], df['AST_boat_facility_OWNER'])
        df['AssetID'] = np.where(df['ASSETID'].notnull(), df['ASSETID'], df['SDEADM_LND_park_recreation_feature_ASSETID'])

        df["WARRANTYDATE"] = np.where(df["WARRANTYDATE"].notnull(), df["WARRANTYDATE"], df['SDEADM_LND_outdoor_rec_poly_WARRANTYDATE'])
        df['INSTYRCONF'] = np.where(df['INSTYRCONF'].notnull(), df['INSTYRCONF'], df['SDEADM_LND_outdoor_rec_poly_INSTYRCONF'])
        df['MATCONF'] = np.where(df['MATCONF'].notnull(), df['MATCONF'], df['SDEADM_LND_outdoor_rec_poly_MATCONF'])
        df['ASSETSTAT'] = np.where(df['ASSETSTAT'].notnull(), df['ASSETSTAT'], df['SDEADM_LND_outdoor_rec_poly_ASSETSTAT'])
        df['INSTDATE'] = np.where(df['INSTDATE'].notnull(), df['INSTDATE'], df['SDEADM_LND_outdoor_rec_poly_INSTDATE'])
        df['RMLIFE'] = np.where(df['RMLIFE'].notnull(), df['RMLIFE'], df['SDEADM_LND_outdoor_rec_poly_RMLIFE'])
        df['RMLIFECONF'] = np.where(df['RMLIFECONF'].notnull(), df['RMLIFECONF'], df['SDEADM_LND_outdoor_rec_poly_RMLIFECONF'])
        df['WARNTYLAB'] = np.where(df['WARNTYLAB'].notnull(), df['WARNTYLAB'], df['SDEADM_LND_outdoor_rec_poly_WARNTYLAB'])
        df['CONDITDTE'] = np.where(df['CONDITDTE'].notnull(), df['CONDITDTE'], df['SDEADM_LND_outdoor_rec_poly_CONDITDTE'])
        df['CONDICONF'] = np.where(df['CONDICONF'].notnull(), df['CONDICONF'], df['SDEADM_LND_outdoor_rec_poly_CONDICONF'])

        df["Rural_Rec_Commuter_Area"] = np.where(df["Rural_Rec_Commuter_Area"].notnull(), df["Rural_Rec_Commuter_Area"], "Regional Centre")
        df["Asset_name"] = np.where(df["REC_NAME"].notnull(), df["REC_NAME"].str.upper(), df["BOATNAME"].str.upper())
        df["School_in_name"] = np.where(df["Asset_name"].str.contains("SCHOOL"), "Yes", "No")
        df["DISTNAME_ID"] = df['DIST_ID'].astype(str) + " - " + df["DISTNAME"]
        df["Community_Name"] = df["Community_Name"].str.title()

        df["Number_of_courts_final"] = df.apply(courts_count, axis=1)
        df["Subcategory_1"] = df.apply(subcat_one, axis=1)
        df["Subcategory_2"] = df.apply(subcat_two, axis=1)

        df.replace(
            {
                "Subcategory_1": {
                    "SOCCER": "Soccer Field",
                    "MODULAR RAMPS": 'Skatepark',
                    "PLAYFIELD": 'Soccer Field',
                    "CONCRETE PARK": 'Skatepark',
                }
            },
            inplace=True
        )

        loggy.info(f"\tUpdating material values...")
        df.replace(
            {
                "Material": material_domain_mapping,
                "Condition": condition_domain_mapping,
                'CONDICONF': condition_confidence_mapping,
                'RMLIFECONF': condition_confidence_mapping,
                'INSTYRCONF': condition_confidence_mapping,
                'MATCONF': condition_confidence_mapping,
                'ASSETSTAT': asset_stat_mapping,
                'OWNER': owner_domain_mapping,
                "Rural_Rec_Commuter_Area": {
                    "EAST": "Commuter East", "WEST": "Commuter West", "EASTERN SHORE": 'Eastern Shore',
                    'MUSQUODOBIIT VALLEY': 'Musquodobit Valley',
                },
            },
            inplace=True
        )

        loggy.info("Filtering out assets...")
        owners_of_interest = ['Halifax', 'Halifax Regional School Board', 'HRSB', 'Halifax Water', 'HW', 'Nova Scotia Power', 'NSPI']

        filtered_df = df[
            (
                    df["OWNER"].isin(owners_of_interest) |
                    df["Asset_name"].str.contains("School", regex=False, case=False)
             ) &
            (
                    (df["Subcategory_1"].str.len() > 0) | (df["Subcategory_2"].str.len() > 0)
            )
        ]

        keep_fields = [
            # "REC_TYPE",
            'OWNER', 'Install_Year',
            'INSTYRCONF', 'INSTDATE',
            'Material',
            # TODO: Could rename some of these fields
            'MATCONF', 'ASSETSTAT',  'RMLIFE', 'RMLIFECONF', 'WARNTYLAB', 'WARRANTYDATE', 'Condition',
            'CONDITDTE', 'CONDICONF', 'MAINRECUSE', 'CLASS',
            'DIST_ID', 'DISTNAME', 'Population', 'Lat', 'Long', 'School_in_name',
            'Subcategory_1',
            "Subcategory_2",
            'Number_of_courts_final',
            'DISTNAME_ID', 'Community_Name', 'Rural_Rec_Commuter_Area',
            'asset_location', 'Asset_name',
            'AssetID',
            # 'SDEADM_LND_park_recreation_feature_ADDDATE'
        ]

        df = df[:][keep_fields]

        try:
            final_df = filtered_df[:][keep_fields]
            final_df.to_excel(EXCEL_OUTPUT, index=False, encoding='utf-8-sig')

        except PermissionError as e:
            loggy.info(f"Can't create new csv because existing file is already open...")
            loggy.info(e)


        @func_logger
        def compare_results(model_output_file, script_output_file):
            """
            - Compare results from model vs results from script
                DUNCAN MACMILLAN HIGH SCHOOL PARK BASKETBALL COURT  -> Now MARINE DRIVE ACADEMY
                DUNCAN MACMILLAN HIGH SCHOOL PARK SPORT FIELD  -> Now MARINE DRIVE ACADEMY
            :param model_output_file:
            :param script_output_file:
            :return:
            """
            model_results_df = pd.read_excel(model_output_file)
            results_df = pd.read_excel(script_output_file)

            model_names = model_results_df['Asset_Name_Final'].values.tolist()
            names = results_df['Asset_name'].values.tolist()

            missing_names = [x for x in model_names if x not in names if x]
            missing_model_names = [x for x in names if x not in model_names if type(x) == str]

            with open("extra_assets.txt", "w") as file:
                print("Extra Assets:")
                file.write("Extra Assets:")

                for count, name in enumerate(sorted(missing_model_names), start=1):
                    print(f"\t{count}) {name}")
                    file.write(f"\n\t{count}) {name}")

            with open("missing_assets.txt", "w") as file:
                print("\nmissing_names:")
                file.write("Missing Assets:")

                for count, name in enumerate(sorted(missing_names), start=1):
                    print(f"\t{count}) {name}")
                    file.write(f"\n\t{count}) {name}")

        model_results_xl = r"T:\work\giss\monthly\202211nov\gallaga\parks dashboard\server_setup\scripts\HRM Park Asset Data 20221115.xls"
        compare_results(model_results_xl, EXCEL_OUTPUT)

    except arcpy.ExecuteError:
        arcpy_msg = arcpy.GetMessages(2)

        loggy.error(f"Arcpy Error:")
        loggy.error(arcpy_msg)

        print(arcpy_msg)

    except Exception as e:
        loggy.error(f"General Error: {e}")
        # TODO: Add email notifier
        # TODO: Add as cron job

    # TODO: Final report from Anders' has courts given to boat facilities...
    # TODO: boat facilities have a rec type

    # November 30, 2022 - Had to recreated R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\alex_data.gdb


