import logging

import conductor

LOG = logging.getLogger(__name__)     

class DeadlineToConductorPackageMapper(object):
    
    PLUGIN_TO_PACKAGE_MAPPING = {}
    
    @classmethod
    def map(cls, deadline_job):
        
        plugin_name = deadline_job.GetJobInfoKeyValue("Plugin")
        map_class = cls.PLUGIN_TO_PACKAGE_MAPPING.get(plugin_name, None)

        if map_class is None:
            raise Exception("No class has been registered for the Deadline plugin '{}'".format(plugin_name))
        
        LOG.debug("Using mapping class '{}' for plugin '{}'".format(map_class, plugin_name))
        
        return map_class.map(deadline_job)

    @classmethod
    def register(cls, mapping_class):
        
        for plugin in mapping_class.DEADLINE_PLUGINS:
            
            if plugin in cls.PLUGIN_TO_PACKAGE_MAPPING:
                raise Exception("The plugin '{}' has already been registered with the class {}".format(cls.PLUGIN_TO_PACKAGE_MAPPING[plugin]))
            
            LOG.debug("Registering mapping plugin '{}' to class '{}'".format(plugin, mapping_class))
            cls.PLUGIN_TO_PACKAGE_MAPPING[plugin] = mapping_class
    

class MayaCmdMapper(object):
    
    DEADLINE_PLUGINS = ["MayaCmd"]
    PRODUCT_NAME = "maya-io"
    
    product_version_map = {"2018": "Autodesk Maya 2018.6"}
    render_version_map = {'Arnold': {'plugin': 'arnold-maya', 'version': 'latest'},
                          'Vray': {'plugin': 'v-ray-maya', 'version': 'latest'},
                          'Renderman': {'plugin': 'renderman-maya', 'version': 'latest'}}
    
    @classmethod
    def map(cls, deadline_job):
        
        package_ids = []
        
        render_name = deadline_job.GetJobPluginInfoKeyValue("Renderer")
        major_version = deadline_job.GetJobPluginInfoKeyValue("Version")
        product_version = cls.product_version_map[major_version]
        
        if render_name == "File":
            raise Exception("Integration doesn't support 'File', please explicitly choose a renderer in the MayCmd plugin properties")
        
        if render_name not in cls.render_version_map:
            raise Exception("The render '{}' is not currently support by the Conductor Deadline integration.".format(render_name))
        
        host_package = conductor.lib.package_utils.get_host_package(cls.PRODUCT_NAME, product_version, strict=False)
        LOG.debug("Found package: {}".format(host_package))
        package_ids.append(host_package.get("package"))
        
        conductor_render_plugin = cls.render_version_map[render_name]
        
        if conductor_render_plugin['version'] == 'latest':
            render_plugin_versions = host_package[conductor_render_plugin['plugin']].keys()
            render_plugin_versions.sort()
            render_plugin_version = render_plugin_versions[-1]
            
        else:
            if conductor_render_plugin['version'] not in conductor_render_plugin['plugin'].keys():
                raise Exception("Unable to find {plugin} version '{verision}' in Conductor packages".format(conductor_render_plugin))
            
            render_plugin_version = conductor_render_plugin['plugin']
            
        LOG.debug("Using render: {} {} {}".format(conductor_render_plugin, render_plugin_version, host_package[conductor_render_plugin['plugin']][render_plugin_version]))
        
        render_package_id = host_package[conductor_render_plugin['plugin']][render_plugin_version]
        package_ids.append(render_package_id)

        return package_ids
    
    
DeadlineToConductorPackageMapper.register(MayaCmdMapper) 