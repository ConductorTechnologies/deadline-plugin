import os

from Deadline.Events import *
from Deadline.Scripting import *

def GetDeadlineEventListener():
    return OnConductorWorkerStart()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


###############################################################
# The event listener class.
###############################################################
class OnConductorWorkerStart(DeadlineEventListener):

    def __init__(self):
        self.OnSlaveStartedCallback += self.OnSlaveStarted

    def Cleanup(self):
        del self.OnSlaveStalledCallback

    def OnSlaveStarted(self, slave_name):

        slaveSettings = RepositoryUtils.GetSlaveSettings(slave_name, True)
        
        if os.environ.get('CONDUCTOR', False):
            
            jobId = str(os.environ['DEADLINE_JOBID'])
            
            deadlineJob = RepositoryUtils.GetJob(jobId, False)

            groupName = "conductorautogroup_{}".format(jobId)

            slaveSettings.SlaveDescription = "Conductor instance for job {}".format(jobId)
            slaveSettings.SlaveName = "Conductor_{}_{}".format(jobId, "000")
            slaveSettings.SetSlaveGroups([groupName])
            RepositoryUtils.SaveSlaveSettings(slaveSettings)
            
            print "Adding Slave to group {}".format(groupName)
            print "Slave Groups: {}".format( slaveSettings.SlaveGroups)

            deadlineJob.JobPostTaskScript = '/opt/Thinkbox/Deadline10/bin/shutdown_conductor_instance.py'
            RepositoryUtils.SaveJob(deadlineJob)