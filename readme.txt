Parks Dashboard - GIS Overlay Analysis
---------------------------------------
Run process weekly on GIS server to output excel file to be consumed by the dashboard.


Requirements:
- SDE connection
- District populations lookup file (population_index_table_csv)
- Rural Recreation Commuter Areas geometry (ArcGIS Online: Rural Recreation Mapping)
- ArcGIS Pro installation of Python (v3.7)
- Access to R:\ICT\ICT BIDS\ETL Data Exchange\Parks and Rec Assets\GIS and Python Scripts\

Python Libraries:
1. arcpy
2. numpy
3. pandas
4. configparser
5. os 
6. logging


SDE tables:
1. AST_boat_facility
2. LND_park_recreation_feature
3. LND_outdoor_rec_poly
4. ADM_electoral_boundaries/ADM_polling_district
5. LND_hrm_parcel_parks/LND_hrm_park
6. ADM_gsa_boundaries/ADM_gsa_polygon
