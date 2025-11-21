import logging
import os.path

import ciocore

from . import deadline_plugin_mapper

LOG = logging.getLogger(__name__)


class HuskMapper(deadline_plugin_mapper.DeadlinePluginMapper):
    '''
    A class for mapping Conductor packages to the Husk Deadline Plugin.
    
    It queries the Deadline Job plugin for details and is therefore limited
    by what that plugin exposes.

    This is intended to be a placeholder.

    1) DEADLINE_PLUGINS needs to contain the names of the correct Deadline plugins
    2) get_output_path needs to query the Deadline plugin for the output path (parent folder only)
    3) get_host_package() needs to query or hard-code the packages (Host: Houdini & pluging: Arnold) - https://dashboard.conductortech.com/api/v1/ee/packages?all=true
    '''
    
    DEADLINE_PLUGINS = ["Husk", "HuskStandalone"]
    PRODUCT_NAME = "houdini"
    
    @classmethod
    def get_host_package(cls, deadline_job):
        '''
        Get the corresponding Conductor package for the primary (aka host) package.
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A package
        :rtype: dict
        '''
        
        ciocore.data.init(product="all")
        software_tree_data = ciocore.data.data()["software"]
        
        # Try to get Houdini version from the deadline job if available
        version = deadline_job.GetJobPluginInfoKeyValue("Version")
        
        if version:
            package = software_tree_data.find_by_name("{} {} linux".format(cls.PRODUCT_NAME, version))
        else:
            # Fallback to latest available Houdini package
            packages = [p for p in software_tree_data.to_path_list() if p.startswith(cls.PRODUCT_NAME)]
            if packages:
                package = software_tree_data.find_by_name(packages[-1] + " linux")
            else:
                package = None
            
        if not package:
            raise deadline_plugin_mapper.NoPackagesFoundError(
                "Unable to locate Houdini packages for job '{}'. Version requested: {}".format(
                    deadline_job.GetJobInfoKeyValue("Name"), version or "latest"
                )
            )             

        return package      
  
    @classmethod
    def map(cls, deadline_job):        
        '''
        Get the corresponding Conductor packages for the given Deadline job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of package's
        :rtype: list of dict
        '''           

        return [cls.get_host_package(deadline_job)]
    
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output directory for the given deadline job
        '''        
        
        output_file = deadline_job.GetJobPluginInfoKeyValue("OutputFile")        
        return os.path.dirname(output_file.replace("\\", "/"))

