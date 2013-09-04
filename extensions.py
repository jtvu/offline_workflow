import arcpy, getpass, os
from xml.etree import ElementTree

#This is a module that holds a variety of functions related in the Versioning process. Class and functions can be called within __main__ if desired.
#Authors: John Tran Vu
#University of Washingngton Capital Projects Office - Information Systems

class Version():
	"""Version is an object that represents what you can do with versioning."""
	
	def __init__(self, feature_classes, workspace):
		"""Creates a Version object with the workspace and the feature class(es) that is being edited"""
		
		self.workspace = os.path.join(os.getcwd(), workspace)
		self.FC = feature_classes
		
	def create_version(self, version_name):
		"""Creates a new version as a branch off of dbo.DEFAULT. If the version already exists, deletes it and creates a brand new one."""
		
		lst = arcpy.ListVersions(self.workspace)
		if ("DBO." + version_name) not in lst:
			arcpy.CreateVersion_management(self.workspace, "dbo.DEFAULT", version_name, "PRIVATE")
		#else:
			#arcpy.DeleteVersion_management(self.workspace, version_name)
			#arcpy.CreateVersion_management(self.workspace, "dbo.DEFAULT", version_name, "PRIVATE")
			#arcpy.AlterVersion_management(self.workspace, version_name, version_name, "", "PRIVATE")
		
	def switch_version(self, version="dbo.DEFAULT"):
		"""Switches to the targeted version. Unless the child version is specifically called, it will change to the default parent version, dbo.DEFAULT"""
	
		for fc in self.FC:
			arcpy.ChangeVersion_management(fc, "TRANSACTIONAL", version, "")
		
	def reconcile(self, version_name):
		"""Given the name of the child version, will reconcile and post to the parent, dbo.DEFAULT."""
	
		arcpy.ReconcileVersions_management(self.workspace, "ALL_VERSIONS", "dbo.DEFAULT", version_name, "LOCK_ACQUIRED", "ABORT_CONFLICTS", "BY_OBJECT", "FAVOR_TARGET_VERSION", "POST", "DELETE_VERSION")
		
		arcpy.AddMessage("Successfully posted changes to parent.")
		
	def clean_up(self):
		arcpy.ClearWorkspaceCache_management(self.workspace)
		arcpy.Compress_management(self.workspace)
		
	def delete_version(self, version_name):
		"""Deletes the specified child version."""
		
		arcpy.DeleteVersion_management(self.workspace, version_name)
		
class Connection():
	""" """
	
	def __init__(self, config_file):
		self.config = config_file
		
	def setting_details(self):
		with open(self.config, 'rt') as file:
			tree = ElementTree.parse(file)
		
		return {"file_gdb": tree.find('./file_gdb').text, "in_data": tree.find('./fc_data').text, "sde_connection_file": tree.find('./sde_connection_file').text, "sde_fpoffline_file": tree.find('./sde_fpoffline_file').text}
