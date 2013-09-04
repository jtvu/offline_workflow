import arcpy, getpass, os, sys, extensions
from xml.etree import ElementTree

#For multiple user editting. 
#This script will be a button where the user can click and it will sync all the changes made to the check-out replica.
#Authors: John Tran Vu
#University of Washingngton Capital Projects Office - Information Systems

def list_replicas(sde_gdb):
	"""Given the floorplans SDE location, returns a list of all the replica names it is hosting. This is to keep track of whether a check-out replica
	exists."""
	
	replicas = []
	for replica in arcpy.da.ListReplicas(sde_gdb):
		replicas.append(replica.name)
	return replicas

def sync_back(sde_gdb, file_gdb, checkout_name):
	arcpy.SynchronizeChanges_management(file_gdb, checkout_name, sde_gdb, "FROM_GEODATABASE1_TO_2", "IN_FAVOR_OF_GDB1", "", "TRUE")

def main():
	checkout_name = getpass.getuser() + "_CheckOut"
	sde_gdb = os.path.join(os.getcwd(), settings["sde_connection_file"])
	file_GDB_data = os.path.join(os.getcwd(), settings["file_gdb"])
	
	success = True
	
	if ("DBO." + checkout_name)  in list_replicas(sde_gdb):
		sync_back(sde_gdb, file_GDB_data, checkout_name)
		arcpy.AddMessage("Successfully synced changes.")
		return success
	else:
		arcpy.AddError("Please create a check-out replica first before syncing.")
		success = False
		return success
		
if __name__ == "__main__":
	connection = extensions.Connection("Config.xml")
	settings = connection.setting_details()
	
	success = main()
	version_name = ("DBO." + getpass.getuser())
	version = extensions.Version([settings["in_data"]], settings["sde_connection_file"])
	if success:
		version.reconcile(version_name)
		version.switch_version()
		version.clean_up()
	arcpy.RefreshTOC()
	arcpy.RefreshActiveView()

