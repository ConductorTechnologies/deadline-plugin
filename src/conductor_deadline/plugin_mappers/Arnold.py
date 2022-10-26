import logging

import ciocore

from . import deadline_plugin_mapper

LOG = logging.getLogger(__name__)
LOG.setLevel(10)


class ArnoldMapper(deadline_plugin_mapper.DeadlinePluginMapper):
    '''
    A class for mapping Conductor packages to the Arnold Deadline Plugin.
    
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
        
        package = software_tree_data.find_by_name("{} {} linux".format(cls.PRODUCT_NAME, cls.MTOA_PRODUCT_VERSION))
            
        if not package:
            raise deadline_plugin_mapper.NoPackagesFoundError("Unable to locate packages for job '{}'".format(deadline_job))             

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

        ciocore.data.init(product="all")
        software_tree_data = ciocore.data.data()["software"]
        
        package = software_tree_data.find_by_name("{} {} linux".format(cls.PRODUCT_NAME, cls.MTOA_PRODUCT_VERSION))
            
        if not package:
            raise deadline_plugin_mapper.NoPackagesFoundError("Unable to locate packages for job '{}'".format(deadline_job))             

        return [cls.get_host_package(deadline_job)]
    
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output path for the given deadline job
        '''        
        return deadline_job.GetJobPluginInfoKeyValue("OutputFile").replace("\\", "/")    
        