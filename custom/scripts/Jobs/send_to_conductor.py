import os
import operator
import json
import PyQt5.QtWidgets
import logging
import traceback

logging.basicConfig()

import Deadline.Scripting
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import conductor
from conductor.__beta__ import job as conductorjob
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

        self._buildUI()
        
    def _buildUI(self):
        
        instanceTypes = conductor.lib.api_client.request_instance_types()
        self.instanceTypes = sorted(instanceTypes, key=operator.itemgetter("cores", "memory"), reverse=False)
        
        projects = conductor.CONFIG.get("projects") or conductor.lib.api_client.request_projects()
        
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
        self.AddControlToGrid( "InstanceLabel", "LabelControl", "Type", 1, 0 , "The type of istance the job will run on", False )
        self.instanceTypeCombo = self.AddControlToGrid( "InstanceBox", "ComboControl", "", 1, 1 )        
        self.preemptibleCheckBox = self.AddSelectionControlToGrid( "IsPreemptible", "CheckBoxControl", True, "Preemptible", 1, 2, "The machine may get preempted" )
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
    
            conductorJob = conductorjob.DeadlineWorkerJob()
            conductorJob.environment['DEADLINE_JOBID'] = self.deadlineJob.JobId
            conductorJob.instance_type = self.selectedInstanceType
            conductorJob.instance_count = self.deadlineJob.TaskCount
            conductorJob.job_title = self.jobNameTextBox.text()            
            conductorJob.preemptible = self.preemptibleCheckBox.isChecked()       
            conductorJob.project = self.projectBox.currentText() 
            
            conductorJob.deadline_proxy_root = os.environ.get('CONDUCTOR_DEADLINE_PROXY')
            conductorJob.set_deadline_ssl_certificate(os.environ.get('CONDUCTOR_DEADLINE_SSL_CERTIFICATE'))
            conductorJob.deadline_use_ssl = bool(os.environ.get('CONDUCTOR_DEADLINE_USE_SSL', False))
            
            conductorJob.software_packages_ids = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.map(self.deadlineJob)
            conductorJob.output_path = conductor_deadline.package_mapper.DeadlineToConductorPackageMapper.get_output_path(self.deadlineJob)                  
                
            dependencySidecarPath = self.dependencyBox.text()
            
            with open(dependencySidecarPath, 'r') as fh:
                dependencies = json.load(fh)
    
            conductorJob.upload_paths.extend(dependencies['dependencies'])
            
            groupName = "conductorautogroup_{}".format(self.deadlineJob.JobId)
            groups = list(Deadline.Scripting.RepositoryUtils.GetGroupNames())
            
            if groupName in groups:
                Deadline.Scripting.RepositoryUtils.DeleteGroup(groupName)
            
            Deadline.Scripting.RepositoryUtils.AddGroup(groupName)
    
            self.deadlineJob.JobGroup = groupName
            conductorJob.deadline_group_name = groupName

            conductorJobId = conductorJob.submit_job()
            
            # This script is present on the Deadline worker
            self.deadlineJob.JobPostTaskScript = conductorJob.POST_TASK_SCRIPT_PATH
            Deadline.Scripting.RepositoryUtils.SaveJob(self.deadlineJob)
            PyQt5.QtWidgets.QMessageBox.information(self, "Job Submitted", "Job {} has been sucesffully submitted to Conductor".format(conductorJobId))

        except Exception, errMsg:
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
                
    def getDependencySidecarFileFromPath(self):
        scenePath = self.deadlineJob.GetJobPluginInfoKeyValue('SceneFile')            
        dependencySideCarFile = "{}.cdepends".format(scenePath)
        return dependencySideCarFile


def __main__( *args ):

    selectedJobs = Deadline.Scripting.MonitorUtils.GetSelectedJobs()
    
    try:

        for deadlineJob in selectedJobs:
    
            dialog = ConductorSubmitDialog(deadlineJob=deadlineJob)
            result = dialog.ShowDialog( True )
            
    except Exception, errMsg:
        error_dialog = conductorplugin.ConductorErrorDialog(errMsg)
        error_dialog.exec_()
        
