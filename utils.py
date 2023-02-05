import arcpy

test_feature = r"R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\Dashboard Upates_20230119\output.gdb\NonMPtoSP_Merge_SpatialJoin_7"


def rename_field(feature, current_field_name, new_field_name):

    field_types = {
        "String": "TEXT", "x": "FLOAT", "x": "DOUBLE", "Integer": "SHORT", "String": "LONG", "x": "DATE"
    }

    try:
        field_props = [x for x in arcpy.ListFields(feature, current_field_name)][0]
        print(f"\nArcpy Field Type: {field_props.type}")

        field_type = field_types.get(field_props.type)

        # Add new temp field
        # Calculate temp field as existing field
        temp_field_name = arcpy.ValidateFieldName(f"{new_field_name}_TEMP")

        print(f"Creating temp field, '{temp_field_name}' from {current_field_name}...")
        arcpy.CalculateField_management(
            in_table=feature, field=temp_field_name, expression=f"!{current_field_name}!", expression_type="PYTHON3",
            field_type=field_type
        )

        # Delete existing field
        print(f"Deleting existing field, '{current_field_name}'...")
        arcpy.DeleteField_management(in_table=feature, drop_field=current_field_name)

        # Create new field with desired name
        # Calculate new field with desired name
        print(f"Creating new field, '{new_field_name}' from {temp_field_name}...")
        arcpy.CalculateField_management(
            in_table=feature, field=new_field_name, expression=f"!{temp_field_name}!", expression_type="PYTHON3",
            field_type=field_type
        )

        print(f"Deleting temp field, '{temp_field_name}'...")
        arcpy.DeleteField_management(in_table=feature, drop_field=temp_field_name)

        return feature

    except IndexError as e:
        print(f"{current_field_name} does not exist in {feature}!")

    except Exception as e:
        print(e)


def create_fgdb(out_folder_path: str, out_name: str="scratch.gdb") -> str:
    """
    Creates a file geodatabase (fgdb) in the specified output folder.
    :param out_folder_path: The path to the folder where the fgdb should be
    :param out_name: The name for the fgdb. Default is "scratch.gdb".
    :return: The path to the file geodatabase.
    """

    print(f"\nCreating File Geodatabase '{out_name}'...")
    workspace_path = os.path.join(out_folder_path, out_name)

    if arcpy.Exists(workspace_path):
        print(f"\tFile Geodatabase already exists!")
        return workspace_path

    fgdb = arcpy.CreateFileGDB_management(out_folder_path, out_name).getOutput(0)
    print(f"\tFile Geodatabase {out_name} created in {out_folder_path}!")

    return fgdb
