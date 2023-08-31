import logging
import sys

import ciocore.data

from . import  deadline_plugin_mapper

LOG = logging.getLogger(__name__)
LOG.setLevel(10)


class MayaCmdMapper(deadline_plugin_mapper.DeadlinePluginMapper):
    '''
    A class for mapping Conductor packages to the MayaCmd Deadline Plugin.
    
    It queries the Deadline Job plugin for details and is therefore limited
    by what that plugin exposes.
    
    It handles a hard-coded set of versions and render plugins. It will always
    try and use the latest render plugin. Currently does not support other
    plugins (Yeti, Goalem, etc...)
    '''
    
    DEADLINE_PLUGINS = ["MayaCmd", "MayaBatch"]
    PRODUCT_NAME = "maya-io"
    
    product_version_map = {"2018": "maya-io 2018.SP6 linux",
                           "2019": "maya-io 2019.SP2 linux",
                           "2020": "maya-io 2020.SP4 linux",
                           "2022": "maya-io 2022.SP3 linux"} # There's an error with the arnold package for 2019 that needs to be resolved
    render_version_map = {'arnold': {'plugin': 'arnold-maya', 'version': 'latest'},
                          'vray': {'plugin': 'v-ray-maya', 'version': 'latest'},
                          'renderman': {'plugin': 'renderman-maya', 'version': 'latest'}}
    
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
        
        # Get details from the Deadline Job plugin
        major_version = deadline_job.GetJobPluginInfoKeyValue("Version").lower()
        
        product_version = cls.product_version_map[major_version]

        # Get the package id for Maya
        host_package = software_tree_data.find_by_name(product_version)
        
        return host_package
    
    @classmethod
    def get_renderer_package(cls, deadline_job, host_package):
        '''
        Get the corresponding Conductor packages for the renderer used in the job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: The renderer package
        :rtype: dict
        '''        
        
        render_name = deadline_job.GetJobPluginInfoKeyValue("Renderer").lower()
        
        # The render plugin must be explicit
        if render_name == "File":
            raise Exception("Integration doesn't support 'File', please explicitly choose a renderer in the MayCmd plugin properties")
        
        if render_name not in cls.render_version_map:
            raise Exception("The render '{}' is not currently support by the Conductor Deadline integration.".format(render_name))
        
        
        # Map the info from the Deadline Job plugin to a Conductor friendly name
        conductor_render_plugin = cls.render_version_map[render_name]

        render_plugins = {}        
        for plugin in host_package['children']:

            if plugin['product'] == conductor_render_plugin['plugin']:
                
                plugin_version = "{major_version}.{minor_version}.{release_version}.{build_version}".format(**plugin)
                render_plugins[plugin_version] = plugin        
                   
        render_plugin_versions = list(render_plugins.keys())
        render_plugin_versions.sort()                
        
        # Always use the latest version of the render plugin
        if conductor_render_plugin['version'] == 'latest':

            if not render_plugin_versions:
                print( host_package)
                raise deadline_plugin_mapper.NoPackagesFoundError("Unable to find any versions of {} for {} {}-{} available on Conductor".format( render_name.capitalize(), 
                                                                                                                host_package['product'].capitalize(),
                                                                                                                host_package['major_version'],
                                                                                                                host_package['minor_version']  ))

            render_plugin = render_plugins[render_plugin_versions[-1]]
            
        else:
            if conductor_render_plugin['version'] not in render_plugin_versions:
                raise Exception("Unable to find {plugin} version '{verision}' in Conductor packages".format(conductor_render_plugin))
            
            render_plugin = render_plugins[conductor_render_plugin['version']]
            
        LOG.debug("Using render: {} {}".format(conductor_render_plugin, render_plugin['package']))
        
        return render_plugin

    @classmethod
    def get_plugins(cls, deadline_job, host_package):
        '''
        Get the corresponding Conductor packages for plugins
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of packages
        :rtype: list of dict
        '''
        
        return [cls.get_renderer_package(deadline_job, host_package)]
        
    @classmethod
    def map(cls, deadline_job):        
        '''
        Get the corresponding Conductor packages for the given Deadline job
        
        :param deaadline_job: The Deadline job to map
        :type deadline_job: :py:class:`~Deadline.Jobs.Job`
        
        :returns: A list of packages
        :rtype: list of dict
        '''
        
        ciocore.data.init(product="all")
        software_tree_data = ciocore.data.data()["software"]
        packages = []
        
        # Get details from the Deadline Job plugin
        major_version = deadline_job.GetJobPluginInfoKeyValue("Version").lower()        
        product_version = cls.product_version_map[major_version]

        # Get the package id for Maya
        host_package = cls.get_host_package(deadline_job)
        
        LOG.debug("Found host package: {}".format(host_package))
        packages.append(host_package)
        LOG.debug("Plugins: {}".format(software_tree_data.supported_plugins(product_version)))        
        
        packages.extend(cls.get_plugins(deadline_job, host_package))
        
        if not packages:
            raise deadline_plugin_mapper.NoPackagesFoundError("Unable to locate packages for job '{}'".format(deadline_job))        

        return packages
    
    @classmethod
    def get_output_path(cls, deadline_job):
        '''
        Get the output path for the given deadline job
        '''
        
        return deadline_job.GetJobPluginInfoKeyValue("OutputFilePath").replace("\\", "/")
        
