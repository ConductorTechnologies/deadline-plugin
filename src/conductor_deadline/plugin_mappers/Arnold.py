import logging

from . import deadline_plugin_mapper

LOG = logging.getLogger(__name__)
LOG.setLevel(10)


class ArnoldMapper(deadline_plugin_mapper.DeadlinePluginMapper):
    '''
    A class for mapping Conductor package ID's to the Arnold Deadline Plugin.
    
    It queries the Deadline Job plugin for details and is therefore limited
    by what that plugin exposes.
    
    It handles a hard-coded set of versions and render plugins. It will always
    try and use the latest render plugin. Currently does not support other
    plugins (Yeti, Goalem, etc...)
    '''
    
    DEADLINE_PLUGINS = ["Arnold"]
    PRODUCT_NAME = "arnold-maya"
    MTOA_PRODUCT_VERSION = "4.0.3.0"
 
    @classmethod
    def map(cls, deadline_job):        
        '''
        Get the corresponding Conductor package ID's for the given Deadline job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of package ID's
        :rtype: list of str
        '''           
        
        package_ids = []

        # Get the package id for Maya
        software_packages = conductor.lib.api_client.request_software_packages()

        for package in software_packages:
            
            package_version = ".".join( (package['major_version'], 
                                        package['minor_version'], 
                                        package['release_version'], 
                                        package['build_version']))
            
            LOG.debug("Checking packages {} {} for match".format(package['package'], package_version))
            
            if ( package['product'] == cls.PRODUCT_NAME and
                 package_version == cls.MTOA_PRODUCT_VERSION ):
        
                LOG.debug("Found package: {}".format(package))
                package_ids.append(package.get("package_id"))
                break
            
        if not packages:
            raise deadline_plugin_mapper.NoPackagesFoundError("Unable to locate packages for job '{}'".format(deadline_job))             

        return package_ids
    
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output path for the given deadline job
        '''        
        return deadline_job.GetJobPluginInfoKeyValue("OutputFile").replace("\\", "/")    
        