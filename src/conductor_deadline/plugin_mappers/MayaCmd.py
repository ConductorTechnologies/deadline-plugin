import logging

import conductor

import deadline_plugin_mapper

LOG = logging.getLogger(__name__)


class MayaCmdMapper(deadline_plugin_mapper.DeadlinePluginMapper):
    '''
    A class for mapping Conductor package ID's to the MayaCmd Deadline Plugin.
    
    It queries the Deadline Job plugin for details and is therefore limited
    by what that plugin exposes.
    
    It handles a hard-coded set of versions and render plugins. It will always
    try and use the latest render plugin. Currently does not support other
    plugins (Yeti, Goalem, etc...)
    '''
    
    DEADLINE_PLUGINS = ["MayaCmd"]
    PRODUCT_NAME = "maya-io"
    
    product_version_map = {"2018": "Autodesk Maya 2018.6",
                           "2019": "Autodesk Maya 2019.2"} # There's an error with the arnold package for 2019 that needs to be resolved
    render_version_map = {'arnold': {'plugin': 'arnold-maya', 'version': '3.2.1.1'},
                          'vray': {'plugin': 'v-ray-maya', 'version': 'latest'},
                          'renderman': {'plugin': 'renderman-maya', 'version': 'latest'}}
    
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
        
        # Get details from the Deadline Job plugin
        render_name = deadline_job.GetJobPluginInfoKeyValue("Renderer").lower()
        major_version = deadline_job.GetJobPluginInfoKeyValue("Version").lower()
        product_version = cls.product_version_map[major_version]
        
        LOG.debug("Mapping Deadline render '{}' '{}'".format(render_name, major_version))
        
        # The render plugin must be explicit
        if render_name == "File":
            raise Exception("Integration doesn't support 'File', please explicitly choose a renderer in the MayCmd plugin properties")
        
        if render_name not in cls.render_version_map:
            raise Exception("The render '{}' is not currently support by the Conductor Deadline integration.".format(render_name))
     
        # Get the package id for Maya
        host_package = conductor.lib.package_utils.get_host_package(cls.PRODUCT_NAME, product_version, strict=False)
        LOG.debug("Found package: {}".format(host_package))
        package_ids.append(host_package.get("package"))
        
        for k,v in host_package.iteritems():
            print k, v
        
        
        # Map the info from the Deadline Job plugin to a Conductor friendly name
        conductor_render_plugin = cls.render_version_map[render_name]
        
        # Always use the latest version of the render plugin
        if conductor_render_plugin['version'] == 'latest':
            render_plugin_versions = host_package[conductor_render_plugin['plugin']].keys()
            render_plugin_versions.sort()
            render_plugin_version = render_plugin_versions[-1]
            
        else:
            if conductor_render_plugin['version'] not in host_package[conductor_render_plugin['plugin']].keys():
                raise Exception("Unable to find {plugin} version '{verision}' in Conductor packages".format(conductor_render_plugin))
            
            render_plugin_version = conductor_render_plugin['version']
            
        LOG.debug("Using render: {} {} {}".format(conductor_render_plugin, render_plugin_version, host_package[conductor_render_plugin['plugin']][render_plugin_version]))
        
        # Get the package id for the render plugin
        render_package_id = host_package[conductor_render_plugin['plugin']][render_plugin_version]
        package_ids.append(render_package_id)

        return package_ids
    
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output path for the given deadline job
        '''
           
        return deadline_job.GetJobInfoKeyValue("OutputDirectory0").replace("\\", "/") 
        
