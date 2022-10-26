import logging

from . import deadline_plugin_mapper

LOG = logging.getLogger(__name__)


class GenericCmdMapper(deadline_plugin_mapper.DeadlinePluginMapper):
    '''
    A class for mapping Conductor packages to Deadline's generic job types.
    
    Since these jobs require no packages from Conductor, it returns an empty list.
    '''
    
    DEADLINE_PLUGINS = ["CommandLine", "CommandScript", "Python"]
    
    @classmethod
    def map(cls, deadline_job):        
        return []
    
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output path for the given deadline job. For Command jobs, there's no natural
        output path so provide something generic.
        '''
           
        return "/my_output_path"