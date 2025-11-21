import logging
import os

import ciocore.conductor_submit as conductor_submit
import ciocore.data
import ciocore.package_environment


LOG = logging.getLogger(__name__)
LOG.setLevel(10)

class JobError(Exception):
    pass

class Job(object):
    
    # Class-level registry to store child classes
    _registry = {}
    
    # Optional: Override this in child classes to specify the deadline mapping(s)
    # Must be a list of strings
    deadline_mapping_class = None
    
    def __init_subclass__(cls, **kwargs):
        """
        Automatically register child classes when they are defined.
        Child classes should define a 'deadline_mapping_class' attribute
        as a list of deadline class names they handle.
        
        Example:
            deadline_mapping_class = ["MayaBatch", "MayaRender"]
        """
        super().__init_subclass__(**kwargs)
        
        # Register the child class if it has a deadline_mapping_class defined
        if cls.deadline_mapping_class is not None:
            # Expect a list of mappings
            if not isinstance(cls.deadline_mapping_class, (list, tuple)):
                raise TypeError(
                    f"{cls.__name__}.deadline_mapping_class must be a list or tuple, "
                    f"got {type(cls.deadline_mapping_class).__name__}"
                )
            
            # Register the class for each mapping
            for mapping in cls.deadline_mapping_class:
                Job._registry[mapping] = cls
                LOG.debug(f"Registered {cls.__name__} for deadline mapping: {mapping}")
    
    def __init__(self):
        
        self._core_data = None
    
        self.upload_paths = []
        self.software_packages = []
        self.user = None
        self.priority = 5
        self.location = ""
        self.instance_type = "n1-standard-8"
        self.metadata = {}
        self.local_upload = True
        self.auto_retry_policy = {}
        self.preemptible = True
        self.chunk_size = 1
        self.project = "default"
        self.output_path = ""
        self.job_title = ""
        self.docker_image = ""
        self._dependencies = None
        self.environment = {}
        self.scout_frames = ""
        
        self._dependency_scan_enabled = True
        self.conductor_job_id = None
        
    def validate_job(self):
        pass
    
    @property
    def core_data(self):
        
        if self._core_data is None:
                    
            ciocore.data.init(product="all")
            self._core_data = ciocore.data.data()
            
        return self._core_data
                
    def _get_task_data(self):
        pass
    
    def _get_frame_range(self):
        pass
    
    def _get_environment(self):

        env = ciocore.package_environment.PackageEnvironment()        
        for package in self.software_packages:
            env.extend(package) 
        
        env = dict(env)
        env.update(self.environment)
        
        return env
    
    def _get_package_ids(self):
        LOG.debug("Getting package ids ({}) from packages: {}".format(len(self.software_packages),
                                                                      self.software_packages))
        
        packages_ids = [ package['package_id'] for package in self.software_packages]
        LOG.debug("Got package ids: {}".format(packages_ids))
        return packages_ids
    
    def get_output_path(self):
        return self.output_path
    
    def scan_for_dependencies(self):
        return []
    
    def get_dependencies(self):
        
        if self._dependencies is None and self._dependency_scan_enabled:            
            self._dependencies = self.scan_for_dependencies()
            
        return self._dependencies + self.upload_paths

    def submit_job(self):
        
        self.validate_job()
        
        data = { "upload_paths": self.get_dependencies(),
                 "software_package_ids": self._get_package_ids(), 
                 "tasks_data": self._get_task_data(), 
                 "user": self.user, 
                 "frame_range": self._get_frame_range(),
                 "environment": self._get_environment(), 
                 "priority": self.priority,
                 "location": self.location, 
                 "instance_type": self.instance_type, 
                 "preemptible": self.preemptible, 
                 "metadata": self.metadata, 
                 "local_upload": self.local_upload, 
                 "autoretry_policy": self.auto_retry_policy,
                 "chunk_size": self.chunk_size, 
                 "project": self.project,
                 "output_path": self.get_output_path(), 
                 "job_title": self.job_title,
                 "scout_frames": self.scout_frames}
        
        if self.docker_image:
            data["docker_image"] = self.docker_image
        
        for key, value in os.environ.items():
            if key.startswith("CONDUCTOR_JOBPARM_"):
                job_parm_key = key.replace("CONDUCTOR_JOBPARM_", "")
                
                if value.lower() == "true":
                    value = True
                
                elif value.lower() == "false":
                    value = False
                    
                try:
                    value = int(value)
                except ValueError:
                    pass
                    
                data[job_parm_key.lower()] = value
        
        LOG.debug("Job Parameters:")
        for k, v in data.items():
            LOG.debug("  {}: '{}'".format(k, v))

        submitter = conductor_submit.Submit(data)

        response, response_code = submitter.main()
        LOG.debug("Response Code: %s", response_code)
        LOG.debug("Response: %s", response)
         
        if response_code in (201, 204):
            LOG.info("Submission Complete")
 
        else:
            LOG.error("Submission Failure. Response code: %s", response_code)
            raise JobError("Submission Failure. Response code: %s", response_code)
 
        self.conductor_job_id = response['jobid']
         
        return self.conductor_job_id
    
    @property
    def owner(self):
        return self.user
    
    @owner.setter
    def owner(self, value):
        self.user = value
    
    @classmethod
    def create_from_deadline_plugin(cls, deadline_mapping_class):
        '''
        A factory helper method to choose the appropriate child class based on
        the deadline plugin name.
        
        This method automatically discovers the appropriate Job subclass based on
        the deadline_mapping_class attribute defined in each child class.
        
        :param deadline_mapping_class: The deadline plugin name identifier
        :type deadline_mapping_class: str
        
        :return: The Job class that matches the given deadline plugin
        :rtype: A child class of :class: `Job`
        
        :raises JobError: If no matching class is found in the registry
        '''
        
        if deadline_mapping_class in cls._registry:
            return cls._registry[deadline_mapping_class]
        
        # If exact match not found, log available options for debugging
        available_mappings = list(cls._registry.keys())
        LOG.error(f"Unable to match deadline mapping '{deadline_mapping_class}' to an appropriate class")
        LOG.error(f"Available mappings: {available_mappings}")
        
        raise JobError(
            f"Unable to match the deadline mapping '{deadline_mapping_class}' to an appropriate class. "
            f"Available mappings: {available_mappings}"
        )
