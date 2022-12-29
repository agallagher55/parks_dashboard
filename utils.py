import arcpy
import os
import logging
import pandas as pd


def with_msgs(command):
    print('-' * 100)
    command
    print(arcpy.GetMessages(0))
    print('-' * 100)


def create_fgdb(out_folder_path, out_name="scratch.gdb"):
    """
    Create scratch workspace (gdb)

    :param out_folder_path:
    :param out_name:
    :return: path to file geodatabase
    """

    print(f"\nCreating File Geodatabase '{out_name}'...")
    workspace_path = os.path.join(out_folder_path, out_name)

    if arcpy.Exists(workspace_path):
        print(f"\tFile Geodatabase already exists!")
        return workspace_path

    fgdb = arcpy.CreateFileGDB_management(out_folder_path, out_name).getOutput(0)
    print("\tFile Geodatabase created!")

    return fgdb


def copy_feature(copy_feature, output_workspace):
    """
    - Copy Features, carrying over domains
    :param copy_feature:
    :param output_workspace:
    :return:
    """

    print(f"\nCopying '{copy_feature}' to {output_workspace}...")

    feature_name = arcpy.Describe(copy_feature).name.replace("SDEADM.", "")  # Remove SDEADM.
    output_feature = os.path.join(output_workspace, feature_name)

    with arcpy.EnvManager(workspace=output_workspace):
        workspace_features = arcpy.ListFeatureClasses()

        # Check if feature already exists in workspace
        if feature_name not in workspace_features:

            arcpy.Copy_management(
                in_data=copy_feature,
                out_data=output_feature
            )

            return output_feature

        else:
            print(f"\t*{feature_name} already exists in {output_workspace}.")


def setupLog(fileName):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

    handler = logging.FileHandler(fileName)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def domain_mapping(domain_name: str, workspace) -> dict:
    print(f"\nGetting domain info for {domain_name}...")

    domain = [x for x in arcpy.da.ListDomains(workspace) if x.name == domain_name]
    if domain:
        return domain[0].codedValues

    else:
        print(f"\tCould not find domain in {workspace}")
        return dict()


def subcat_one_mapping(reference_gdb) -> dict:
    print("\nGetting Subcategory 1 mapping...")

    index_table = os.path.join(reference_gdb, "index_table_csv")

    index_fields = [x.name for x in arcpy.ListFields(index_table) if x.name != 'OBJECTID']
    df = pd.DataFrame([row for row in arcpy.da.SearchCursor(index_table, index_fields)], columns=index_fields)

    records = df.to_dict("records")
    mapping = {x["MPFU"]: x['New_NAME'] for x in records}

    return mapping


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

    model_names = model_results_df['Asset_name'].values.tolist()
    names = results_df['Asset_name'].values.tolist()

    missing_names = sorted([x for x in model_names if x not in names if x])
    missing_model_names = sorted([x for x in names if x not in model_names if type(x) == str])

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


if __name__ == "__main__":
    model_xl = r"R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\Output\model_output_20221025.xls"
    script_xl = r"R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\Output\park_assets.xlsx"

    # subcat_one_mapping(r"R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\GIS_for_Dashboard.gdb")

    compare_results(model_xl, script_xl)
