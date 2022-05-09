import logging

import ciocore
import ciocore.data

from . import job
from pip._vendor.distro import minor_version

LOG = logging.getLogger(__name__)


class DeadlineToConductorPackageMapperError(Exception):
    pass


class WorkerJobError(job.JobError):
    pass


class DeadlineWorkerJobError(WorkerJobError):
    pass


class WorkerJob(job.Job):
    pass


class DeadlineWorkerJob(WorkerJob):
    
    POST_TASK_SCRIPT_PATH = '/opt/thinkbox/deadline/{major_version}/deadline{version}/conductor/shutdown_conductor_instance.py'
    DEFAULT_CMD = "launch_deadline.sh"
    DEFAULT_WORKER_VERSION = "10.1.12.1"
    
    def __init__(self, *args , **kwargs):
    
        super(WorkerJob, self).__init__(*args, **kwargs)
        
        self.output_path = "/tmp"
    
        self.job_title = "Deadline Worker"
        self.instance_count = 1
        
        self.cmd = self.DEFAULT_CMD
        self.deadline_proxy_root = None
        self.deadline_ssl_certificate = None
        self.deadline_use_ssl = True
        self.deadline_worker_version = self.DEFAULT_WORKER_VERSION
        self.deadline_group_name = None
        
    def _get_task_data(self):
        task_data = []
        
        # Create a task for every instance that's been requested
        for instance_number in range(1, self.instance_count+1):
            task_data.append({"frames": str(instance_number), "command": self.cmd})
        
        return task_data
    
    def set_deadline_ssl_certificate(self, path):
        self.deadline_ssl_certificate =  ciocore.file_utils.conform_platform_filepath(ciocore.file_utils.strip_drive_letter(path))
        self.upload_paths.append(path)
    
    def _get_environment(self):

        self.environment['CONDUCTOR_DEADLINE_GROUP_NAME'] = self.deadline_group_name         
        self.environment['DCONFIG_ProxyUseSSL'] = str(self.deadline_use_ssl).lower()
        self.environment['CONDUCTOR_DEADLINE_CLIENT_VERSION'] = self.deadline_worker_version
        self.environment['DCONFIG_ProxyRoot'] = self.deadline_proxy_root
                        
        self.environment['CONDUCTOR_DEADLINE_SKIP_ENV_VAR_DUMP'] = "0"
        self.environment['CONDUCTOR_DEADLINE_SHOW_WATCHER_DEBUG'] = "1"
        
        if self.deadline_use_ssl:
            self.environment['DCONFIG_ProxySSLCertificate'] = self.deadline_ssl_certificate
        
        return super(WorkerJob, self)._get_environment()
    
    def validate_job(self):
        
        if self.deadline_proxy_root is None:
            raise DeadlineWorkerJobError("deadline_proxy_root has not been set. This must be the <hostname>:<port> of your Deadline RCS")
        
        if self.deadline_ssl_certificate is None:
            raise DeadlineWorkerJobError("deadline_ssl_certificate has not been set. This must be the local path to your Deadline client certificate")
        
        return True
    
    def submit_job(self):
        
        ciocore.data.init("deadline")          
        software_tree = ciocore.data.data()["software"]
        
        major_version, minor_version, release_version, build_version = self.deadline_worker_version.split(".")
        
        try:
            deadline_package = software_tree.find_by_keys( product='deadline',
#                                                            major_version=major_version,
#                                                            minor_version=minor_version,
#                                                            release_version = release_version,
#                                                            build_version = build_version
                                                           )
                                                           
        except (TypeError, KeyError) as errMsg:
            LOG.error(str(errMsg))
            #available_deadline_packages = [ p['package'] for p in software_tree.find_by_keys( product='deadline') ]
            available_deadline_packages = software_tree.find_by_keys( product='deadline')
            raise DeadlineWorkerJobError('Unable to find a package in Conductor for Deadline v{}.\nAvailable packages are {}:'.format(self.deadline_worker_version, 
                                                                                                                                      available_deadline_packages))
        
        self.software_packages.append(deadline_package)
        
        return super(DeadlineWorkerJob, self).submit_job()
    
    def get_post_task_script_path(self):
        
        major_version = self.deadline_worker_version.split(".")[0]         
        return self.POST_TASK_SCRIPT_PATH.format(major_version=major_version, version=self.deadline_worker_version)
         
        