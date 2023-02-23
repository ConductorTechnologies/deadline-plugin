#!/usr/bin/env python3

import os
import operator
import json
import PyQt5.QtWidgets
import logging
import sys
import traceback

logging.basicConfig()

import Deadline.Scripting
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import ciocore
import ciocore.package_tree
import cioseq.sequence

import conductor_job as conductorjob
import conductor_deadline.package_mapper


class ConductorErrorDialog(PyQt5.QtWidgets.QMessageBox):
    
    def __init__(self, exception, *args, **kwargs):
        
        super(ConductorErrorDialog, self).__init__(*args, **kwargs)
        self.setIcon(PyQt5.QtWidgets.QMessageBox.Critical)
        
        # For the dialog to be a certain width
        exception = "{:200}".format(exception)

        self.setWindowTitle("Submit to Conductor - Error")
        self.setText(str(exception))
        self.setDetailedText(traceback.format_exc())


class ConductorSubmitDialog(DeadlineScriptDialog):
    
    def __init__(self, deadlineJob, *args, **kwargs):
        
        super(ConductorSubmitDialog, self).__init__(*args, **kwargs)
        
        self.deadlineJob = deadlineJob
        
        self.selectedInstanceType = None
        self.jobTitle = ""
        self.instanceTypes = []
        
        self.conductorJob = None
        
        self._buildUI()
        
    def _buildUI(self):

        self.instanceTypes = self.getInstances()
        
        projects = ciocore.api_client.request_projects()
        
        self.resize(700, 225)
        
        self.SetTitle("Conductor Submit")
        
        self.AddGrid()
        self.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job", 0, 0, colSpan=2 )
    
        self.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0 , "The name of your job.", False )
        self.jobNameTextBox = self.AddControlToGrid( "NameBox", "TextControl", "[DEADLINE WORKER] {}".format(self.deadlineJob.JobName), 1, 1 )
    
        self.AddControlToGrid( "ProjectLabel", "LabelControl", "Project", 2, 0 , "The Conductor project", False )
        self.projectBox = self.AddControlToGrid( "ProjectBox", "ComboControl", "default", 2, 1 )
        self.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependency Sidecar", 3, 0 , "JSON file with all the dependencies", False )
        self.dependencyBox = self.AddControlToGrid( "DependencyBox", "TextControl", "", 3, 1 )
        self.dependencyButton = self.AddControlToGrid( "DependencyButton", "ButtonControl", "Choose file...", 3, 2, expand=False )
        self.dependencyButton.clicked.connect( self.onSelectSidecarFileButton )
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "Separator2", "SeparatorControl", "Instance", 0, 0, colSpan=3 )
        self.AddControlToGrid( "InstanceLabel", "LabelControl", "Type", 1, 0 , "The type of instance the job will run on", False )
        self.instanceTypeCombo = self.AddControlToGrid( "InstanceBox", "ComboControl", "", 1, 1 )        
        self.preemptibleCheckBox = self.AddSelectionControlToGrid( "IsPreemptible", "CheckBoxControl", True, "Preemptible", 1, 2, "The machine may get preempted" )
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "Separator3", "SeparatorControl", "Packages", 0, 0, colSpan=2 )
        self.nativeJobCheckBox = self.AddSelectionControlToGrid( "IsNative", "CheckBoxControl", False, "Native", 1, 0, "A native job won't launch a Deadline worker. Job will be only appear in the Conductor Dashboard" )
        self.AddControlToGrid( "WorkerLabel", "LabelControl", "Worker", 2, 0 , "Deadline Worker version to use on Conductor", False )
        self.deadlinePackageCombo = self.AddControlToGrid( "WorkerBox", "ComboControl", "", 2, 1 )
        
        self.AddControlToGrid( "DCCLabel", "LabelControl", "DCC", 3, 0 , "DCC package to use on Conductor", False )
        self.dccPackageCombo = self.AddControlToGrid( "PackageBox", "ComboControl", "", 3, 1 )
        
        self.AddControlToGrid( "PluginLabel", "LabelControl", "Plugins", 4, 0 , "Plugins to enable on Conductor", False )
        self.pluginPackagesCombo = self.AddControlToGrid( "PluginPackageBox", "MultiSelectListControl", "", 4, 1 )       
        
        self.EndGrid()        
        
        # Add control buttons
        self.AddGrid()
        self.AddHorizontalSpacerToGrid( "HSpacer", 0, 0 )
        okButton = self.AddControlToGrid( "OkButton", "ButtonControl", "Submit", 0, 1, expand=False )
        okButton.clicked.connect( self.onOKButtonClicked )
        cancelButton = self.AddControlToGrid( "CancelButton", "ButtonControl", "Cancel", 0, 2, expand=False )
        cancelButton.clicked.connect( self.onCancelButtonClicked )
        self.EndGrid()        

        # Populate the instance Combo box
        for instanceType in self.instanceTypes:
            self.instanceTypeCombo.addItem(instanceType['description'])
            
        self.selectedInstanceType = self.instanceTypes[0]['name']            
        self.instanceTypeCombo.currentIndexChanged.connect( self.onInstanceTypeChanged )
        
        # sort alphabetically. may be unicode, so can't use str.lower directly
        for project in sorted(projects, key=lambda x: x.lower()):
            self.projectBox.addItem(project)
  
        # Set the sidecar dependency (if it exists)
        dependencySidecarFile = self.getDependencySidecarFileFromPath()
        
        if os.path.exists(dependencySidecarFile):
            self.dependencyBox.setText(dependencySidecarFile)
            
        # Add packages to the controls
        packages = ciocore.api_client.request_software_packages()
        
        # Deadline worker
        deadline_packages = ciocore.package_tree.PackageTree(packages, product="deadline")
        
        for deadline_package in deadline_packages.supported_host_names():
            self.deadlinePackageCombo.addItem(deadline_package)
            
        if os.environ.get('CONDUCTOR_DEADLINE_WORKER_VERSION'):
            self.deadlinePackageCombo.setCurrentText("deadline {} linux".format( os.environ.get('CONDUCTOR_DEADLINE_WORKER_VERSION')))
        
        print ("Setting values to: {}".format("deadline {} linux".format( os.environ.get('CONDUCTOR_DEADLINE_WORKER_VERSION'))))    
        
        # DCC Host
        product_name = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.get_mapping_class(self.deadlineJob).PRODUCT_NAME
        host_packages = ciocore.package_tree.PackageTree(packages, product=product_name)
        
        for host_package in host_packages.supported_host_names():
            self.dccPackageCombo.addItem(host_package)
            
        dcc_host = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.get_mapping_class(self.deadlineJob).get_host_package(self.deadlineJob)
        
        if dcc_host:            
            dcc_package_name = ciocore.package_tree.to_name(dcc_host)
            self.dccPackageCombo.setCurrentText(dcc_package_name)
            print ("Setting values to: {}".format(dcc_package_name))
            
            plugin_package_names = [ciocore.package_tree.to_name(plugin_package) for plugin_package in dcc_host['children']]
            plugin_package_names.sort()
         
            # DCC Plugins 
            for plugin_package in plugin_package_names:
                self.pluginPackagesCombo.addItem(plugin_package)
                
            plugins = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.get_mapping_class(self.deadlineJob).get_plugins(self.deadlineJob, dcc_host)
            default_plugin_package_names = [ciocore.package_tree.to_name(plugin_package) for plugin_package in plugins]
            
            print ("Setting values to: {}".format(default_plugin_package_names))
            self.SetValue("PluginPackageBox", default_plugin_package_names)
            
        else:
            print ("WARNING: The Deadlie Package Mapper did not return a valid host package")
      
    def onSelectSidecarFileButton(self):
        
        dependencySidecarPath = self.dependencyBox.text()
        
        if dependencySidecarPath:
            openDir = os.path.dirname(dependencySidecarPath)
            
        else:
            openDir = os.path.dirname(self.deadlineJob.GetJobPluginInfoKeyValue('SceneFile'))

        selectedSidecarFile, fileType = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, "Select sidecar dependency file", openDir, "Conductor dependency files (*.cdepends);;JSON files (*.json);;All files (*.*)")
        
        if selectedSidecarFile:
            self.dependencyBox.setText(selectedSidecarFile)
                
    def onOKButtonClicked(self):

        try:
            
            if self.nativeJobCheckBox.isChecked():
                
                deadline_mapper = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.get_mapping_class(self.deadlineJob)
                
                host_package = deadline_mapper.get_host_package(self.deadlineJob)
                renderer_package = deadline_mapper.get_renderer_package(self.deadlineJob, host_package)
                #self.conductorJob = self._createNativeJob()
                self.conductorJob = conductorjob.MayaRenderJob()
                self.conductorJob.renderer = renderer_package['product']
                self.conductorJob.scene_path = self.deadlineJob.GetJobPluginInfoKeyValue("SceneFile") 
                self.conductorJob.project_path = self.deadlineJob.GetJobPluginInfoKeyValue("ProjectPath")
                self.conductorJob.frames = cioseq.sequence.Sequence.create(self.deadlineJob.GetJobInfoKeyValue("Frames"))
                self.conductorJob.render_layer = self.deadlineJob.GetJobPluginInfoKeyValue("RenderLayer") or self.conductorJob.render_layer
                self.conductorJob.chunk_size = 1
                self.conductorJob.local_upload = False

#                 self.conductorJob.startFrame = 
#                 self.conductorJob.endFrame =
                #deadline_job.GetJobInfoKeyValue("OutputDirectory0"
                
            else:
                
                #self.conductorJob = self._createDeadlineJob()
                self.conductorJob = conductorjob.DeadlineWorkerJob()
                self.conductorJob.deadline_proxy_root = os.environ.get('CONDUCTOR_DEADLINE_PROXY')
                self.conductorJob.set_deadline_ssl_certificate(os.environ.get('CONDUCTOR_DEADLINE_SSL_CERTIFICATE', ""))
                self.conductorJob.deadline_use_ssl = self.to_bool(os.environ.get('CONDUCTOR_DEADLINE_USE_SSL', ""))
                
                groupName = "conductorautogroup_{}".format(self.deadlineJob.JobId)
                groups = list(Deadline.Scripting.RepositoryUtils.GetGroupNames())
                
                if groupName in groups:
                    Deadline.Scripting.RepositoryUtils.DeleteGroup(groupName)
                
                Deadline.Scripting.RepositoryUtils.AddGroup(groupName)
        
                self.deadlineJob.JobGroup = groupName
                self.conductorJob.deadline_group_name = groupName
                
                self.deadlineJob.JobPostTaskScript = self.conductorJob.get_post_task_script_path()
                Deadline.Scripting.RepositoryUtils.SaveJob(self.deadlineJob)             
            
            self.conductorJob.environment['DEADLINE_JOBID'] = self.deadlineJob.JobId
            self.conductorJob.instance_type = self.selectedInstanceType
            self.conductorJob.instance_count = self.deadlineJob.TaskCount
            self.conductorJob.job_title = self.jobNameTextBox.text()            
            self.conductorJob.preemptible = self.preemptibleCheckBox.isChecked()       
            self.conductorJob.project = self.projectBox.currentText() 
            self.conductorJob.software_packages = self.getSoftwarePackages()            
            self.conductorJob.upload_paths.append(self.deadlineJob.GetJobPluginInfoKeyValue('SceneFile'))

            self.conductorJob.output_path = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.get_output_path(self.deadlineJob)                  
                
            dependencySidecarPath = self.dependencyBox.text()
            
            dependencies = []
            
            # If a command is being executed that doesn't require any files, the submission shouldn't
            # fail
            if dependencySidecarPath:
                with open(dependencySidecarPath, 'r') as fh:
                    dependencies = json.load(fh).get('dependencies')

    
            self.conductorJob.upload_paths.extend(dependencies)

            conductorJobId = self.conductorJob.submit_job()
            
            # This script is present on the Deadline worker

            PyQt5.QtWidgets.QMessageBox.information(self, "Job Submitted", "Job {} has been sucesffully submitted to Conductor".format(conductorJobId))

        except Exception as errMsg:
            error_dialog = ConductorErrorDialog(errMsg)
            error_dialog.exec_()            
            super( ConductorSubmitDialog, self ).reject()
            raise
        
        super( ConductorSubmitDialog, self ).accept()
        
    def onCancelButtonClicked(self):
        super( ConductorSubmitDialog, self ).reject()
    
    def onInstanceTypeChanged(self):
        
        instanceValue = self.instanceTypeCombo.currentText()
        
        for instanceType in self.instanceTypes:
            if instanceValue == instanceType['description']:
                self.selectedInstanceType = instanceType['name']
                
    def getInstances(self):
        from ciocore import data as coredata
        coredata.init(product="all")
        tree_data = coredata.data()["instance_types"]
        instances = [i for i in tree_data if i['operating_system'] == 'linux']
        instances = sorted(instances, key=operator.itemgetter("cores", "memory"), reverse=False)
        
        return instances
                
    def getDependencySidecarFileFromPath(self):
        scenePath = self.deadlineJob.GetJobPluginInfoKeyValue('SceneFile')            
        dependencySideCarFile = "{}.cdepends".format(scenePath)
        return dependencySideCarFile
    
    def getSoftwarePackages(self):
        
        package_names = [self.GetValue("PackageBox")]
        
        package_names.extend(self.GetValue("PluginPackageBox"))
        
        selected_packages = []
        
        # Add packages to the controls
        packages = ciocore.api_client.request_software_packages()
        package_tree = ciocore.package_tree.PackageTree(packages)
        
        # The package for the Deadline Worker is explicit
        self.conductorJob.deadline_worker_package = package_tree.find_by_name(self.GetValue("WorkerBox"))
        for package_name in package_names:
            package = package_tree.find_by_name(package_name)
            
            if package is None:
                raise ValueError("Unable to find a package for '{}'".format(package_name))
            
            selected_packages.append(package)
             
        return selected_packages  
    
    @staticmethod
    def to_bool(value):        
        return value.lower() not in ('0', 'false', 'no')


def __main__( *args ):

    selectedJobs = Deadline.Scripting.MonitorUtils.GetSelectedJobs()
    
    try:

        for deadlineJob in selectedJobs:
    
            dialog = ConductorSubmitDialog(deadlineJob=deadlineJob)
            result = dialog.ShowDialog( True )
            
    except Exception as errMsg:
        error_dialog = ConductorErrorDialog(errMsg)
        error_dialog.exec_()
        
