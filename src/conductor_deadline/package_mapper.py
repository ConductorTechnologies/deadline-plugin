import logging

LOG = logging.getLogger(__name__)
LOG.setLevel(10)

class DeadlineToConductorPackageMapper(object):
    '''
    A class for mapping a Deadline Job Plugin to a set of Conductor package ID's.
    
    This class is only directly responsible for mapping a Deadling Job Plugin to
    a corresponding DeadlinePluginMapper class. See that class for more details
    on implementation.
    
    To customize mapping behaviour changes should be made to the set of 
    DeadlinePluginMapper classes - not this class.
    
    All DeadlinePluginMapper classes must register with this class by calling
    register(). Only one DeadlinePluginMapper class can be reigsted at a time
    for each Deadline Job Plugin. Though one DeadlinePluginMapper class could
    be mapped to multiple Deadline Job Plugins (ex: MayaCmd and MayaBatch could
    both use :py:class:`~MayaCmdMapper`.
    
    '''

    PLUGIN_TO_PACKAGE_MAPPING = None
    
    @classmethod
    def clear_mapping(cls):
        '''
        Clears the internal registry of mapped classes
        ''' 
        
        from . import plugin_mappers
        cls.PLUGIN_TO_PACKAGE_MAPPING = None
        reload(plugin_mappers)
        
    @classmethod
    def get_mapping_class(cls, deadline_job):
        ''''
        Get the mapping class that has been registered for the given deadline
        job.
        '''
        
        if cls.PLUGIN_TO_PACKAGE_MAPPING is None:
        from . import plugin_mappers
        plugin_name = deadline_job.GetJobInfoKeyValue("Plugin")
        map_class = cls.PLUGIN_TO_PACKAGE_MAPPING.get(plugin_name, None)

        if map_class is None:
            raise Exception("No class has been registered for the Deadline plugin '{}'".format(plugin_name))
        
        LOG.debug("Using mapping class '{}' for plugin '{}'".format(map_class, plugin_name))
        
        return map_class         
            
    @classmethod
    def map(cls, deadline_job):
        '''
        Get the corresponding Conductor package ID's for the given Deadline job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of package ID's
        :rtype: list of str
        '''
        
        packages = cls.get_mapping_class(deadline_job).map(deadline_job)

        return packages

    @classmethod
    def register(cls, mapping_class):
        '''
        Register a DeadlinePluginMapper class.
        
        :param mapping_class: The mapping class to register
        :type mapping_class: :py:class:`~DeadlinePluginMapper`
        
        :return: None
        '''
        
        if cls.PLUGIN_TO_PACKAGE_MAPPING is None:
            cls.PLUGIN_TO_PACKAGE_MAPPING = {}
        
        for plugin in mapping_class.DEADLINE_PLUGINS:
            
            if plugin in cls.PLUGIN_TO_PACKAGE_MAPPING:
                raise Exception("The plugin '{}' has already been registered with the class {}".format(plugin, cls.PLUGIN_TO_PACKAGE_MAPPING[plugin]))
            
            LOG.debug("Registering mapping plugin '{}' to class '{}'".format(plugin, mapping_class))            
            cls.PLUGIN_TO_PACKAGE_MAPPING[plugin] = mapping_class
            
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output path for the given deadline job
        '''
        return cls.get_mapping_class(deadline_job).get_output_path(deadline_job)
