import arcpy, getpass, os, extensions
from xml.etree import ElementTree

#Authors: John Tran Vu
#University of Washingngton Capital Projects Office - Information Systems

"""This script will sync any changes from sde offline floorplans to the file geodatabase specifically holding those 
same basic floorplans. Then it will also create a check-out replica from sde floorplans to a separate file geodatabase 
specifically holding the operational data."""

def list_replicas(sde_floorplans):
	"""Given the floorplans SDE location, returns a list of all the replica names it is hosting. This is to keep track of whether a check-out replica
	exists."""
	
	replicas = []
	for replica in arcpy.da.ListReplicas(sde_floorplans):
		replicas.append(replica.name)
	
	return replicas

def delete_features(sde_floorplans, file_GDB_data):
	"""Given the local file GDB location, delete any features inside them before creating the replica. This process must be done
	before the replica is created because there will be an issue if there are features inside the GDB when trying to create a check-out replica."""
	
	arcpy.AddMessage("Deleting")
	arcpy.env.workspace = file_GDB_data
	for objFeatureClass in arcpy.ListFeatureClasses():
		arcpy.Delete_management(objFeatureClass)
	for objTables in arcpy.ListTables():
		arcpy.Delete_management(objTables)
	arcpy.AddMessage("Done Deleting")
	
def remove_multiple_layers(in_data):
	"""Given a list of the features (feature classes and tables), remove them from the map. This must be done before the delete_features function can be called, so that there will be no schema lock issues."""
	
	arcpy.AddMessage("Removing")
	mxd = arcpy.mapping.MapDocument("CURRENT")
	df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
	for lyr in arcpy.mapping.ListLayers(mxd, "", df):
		for fc in in_data:
			if lyr.name == "DDPINDEX" or lyr.name == fc[15:]:
				arcpy.mapping.RemoveLayer(df, lyr)
				
	for tab in arcpy.mapping.ListTableViews(mxd, "", df):
		for ele in in_data:
			if tab.name == ele[15:]:
				arcpy.mapping.RemoveTableView(df, tab)
	
	arcpy.RefreshActiveView()
	arcpy.RefreshTOC()
				
	del df
	arcpy.AddMessage("Done Removing")
	
def add_multiple_layers_back(file_GDB_data, file_GDB_floorplans, in_data):
	"""Given the location of the local file GDB and the features, add the feature class from the local file GDB back into the map."""
	
	arcpy.AddMessage("Adding back")
	mxd = arcpy.mapping.MapDocument("CURRENT")
	df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
	
	#Tables aren't considered layers so have to treat tables differently
	#Create a new layer
	#When the feature class is replicated into the file geodatabase, the prefix "foorplans.DBO." needs to be stripped out
	for fc in in_data:
		try:
			fc_layer = arcpy.mapping.Layer(file_GDB_data + "\\" + fc[15:])
		except:
			fc_layer = arcpy.mapping.TableView(file_GDB_data + "\\" + fc[15:])
		#Add the layer to the map at the bottom of the TOC in data frame 0
		try:
			arcpy.mapping.AddLayer(df, fc_layer, "BOTTOM")
		except:
			arcpy.mapping.AddTableView(df, fc_layer)
			
		del fc_layer
			
	ddpindex_layer = arcpy.mapping.Layer(file_GDB_floorplans + "\DDPINDEX")
	arcpy.mapping.AddLayer(df, ddpindex_layer, "BOTTOM")
	
	for lyr in arcpy.mapping.ListLayers(mxd):
		if lyr.name == "DDPINDEX":
			lyr.visible = False
	
	#Refresh map		
	arcpy.RefreshTOC()
	arcpy.RefreshActiveView()
	
	del df, ddpindex_layer
	
	arcpy.AddMessage("Done Adding back")

def create_replica(in_data, file_GDB_data, sde_floorplans, checkout_name):
	"""Given the feature class and the locations of the local file GDB and the SDE where the feature class is coming from, creates a check-out replica from the SDE GDB to the local file GDB."""
	
	arcpy.AddMessage("Replica")
	arcpy.env.workspace = sde_floorplans
	
	arcpy.CreateReplica_management(in_data, "CHECK_OUT", file_GDB_data, checkout_name, "FULL", "PARENT_DATA_SENDER", "ALL_ROWS", "DO_NOT_REUSE", "GET_RELATED", "", "DO_NOT_USE_ARCHIVING")
	
	arcpy.AddMessage("Done Replica")
	
def sync_floorplans(sde_offline_floorplans, file_GDB_floorplans):
	"""Each time before a check-out replica is created, the floorplans will be updated from floorplansoffline SDE."""
	arcpy.AddMessage("Syncing")
	arcpy.SynchronizeChanges_management(sde_offline_floorplans, "DBO.floorplans_local", file_GDB_floorplans, "FROM_GEODATABASE1_TO_2", "", "", "")
	arcpy.AddMessage("Done Sync")
	
def export_DDPIndex(sde_offline_floorplans, file_GDB_floorplans):
	"""Given the location of the offline SDE and the local floorplans file GDB, exports the DDPINDEX view as a feature class from offline sde to the local GDB. Views cannot be replicated, so we will have to convert it into a feature class each time."""
	
	arcpy.AddMessage("DDPINDEX")
	arcpy.env.workspace = file_GDB_floorplans
	for fc in arcpy.ListFeatureClasses():
		if fc == "DDPINDEX":
			arcpy.Delete_management(fc)
			
	arcpy.env.workspace = sde_offline_floorplans
	arcpy.FeatureClassToGeodatabase_conversion("FLOORPLANSOFFLINE.DBO.DDPINDEX", file_GDB_floorplans)
	arcpy.AddMessage("Done DDPINdex")
	
def main():
	checkout_name = getpass.getuser() + "_CheckOut"
	
	sde_floorplans = os.path.join(os.getcwd(), settings["sde_connection_file"])
	
	file_GDB_data = os.path.join(os.getcwd(), settings["file_gdb"])
	file_GDB_floorplans = os.path.join(os.getcwd(), "Floorplans.gdb")
	
	sde_offline_floorplans = os.path.join(os.getcwd(), settings["sde_fpoffline_file"])
	
	if ("DBO." + checkout_name) not in list_replicas(sde_floorplans):
		remove_multiple_layers([settings["in_data"]])
		export_DDPIndex(sde_offline_floorplans, file_GDB_floorplans)
		sync_floorplans(sde_offline_floorplans, file_GDB_floorplans)
		delete_features(sde_floorplans, file_GDB_data)
		create_replica([settings["in_data"]], file_GDB_data, sde_floorplans, checkout_name)
		add_multiple_layers_back(file_GDB_data, file_GDB_floorplans, [settings["in_data"]])
		arcpy.AddMessage("Successfully checked out data for project")
	else:
		arcpy.AddError("Please sync changes before trying to check-out again.")
		
if __name__ == "__main__":
	connection = extensions.Connection("Config.xml")
	settings = connection.setting_details()
	
	version_name = getpass.getuser()
	version = extensions.Version([settings["in_data"]], settings["sde_connection_file"])
	version.create_version(version_name)
	version.switch_version(("DBO." + version_name))
	
	main()
