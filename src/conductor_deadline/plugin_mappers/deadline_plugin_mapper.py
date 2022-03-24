class NoPackagesFoundError(Exception):
    pass

class DeadlinePluginMapper(object):
    '''
    Base class for mapping a specific Deadline Job PLugin to a set of Conductor
    package ID's. It's the responsiblity of the child classes to handle plugins,
    specific versions, etc... 
    '''

    DEADLINE_PLUGINS = []
    PRODUCT_NAME = None
    
    @classmethod
    def map(cls, deadline_job):
        '''
        Get the corresponding Conductor package ID's for the given Deadline job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of package ID's
        :rtype: list of str
        '''           
        
        raise NotImplementedError    