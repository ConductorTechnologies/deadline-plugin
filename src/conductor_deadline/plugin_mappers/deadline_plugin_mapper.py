class NoPackagesFoundError(Exception):
    pass

class DeadlinePluginMapper(object):
    '''
    Base class for mapping a specific Deadline Job Plugin to a set of Conductor
    packages. It's the responsiblity of the child classes to handle plugins,
    specific versions, etc... 
    '''

    DEADLINE_PLUGINS = []
    PRODUCT_NAME = None
    
    @classmethod
    def get_host_package(cls, deadline_job):
        '''
        Get the corresponding Conductor package for the primary (aka host) package.
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A package
        :rtype: dict
        '''
        
        return ""
    
    @classmethod
    def get_plugins(cls, deadline_job, host_package):
        '''
        Get the corresponding Conductor packages for plugins
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of packages
        :rtype: list of dict
        '''
        
        return [] 
    
    @classmethod
    def map(cls, deadline_job):
        '''
        Get the corresponding Conductor packages for the given Deadline job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of packages
        :rtype: list of dict
        '''           
        
        raise NotImplementedError    