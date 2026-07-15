import logging

import cioseq.sequence

from . import job

LOG = logging.getLogger(__name__)

class HuskRenderJob(job.Job):
    
        # Deadline plugin names for automatic registration
        # Husk can be submitted through different deadline plugins
        deadline_plugin_names = ["Husk", "HuskStandalone"]
        
        def __init__(self, scene_path=None, *args , **kwargs):
            
            super(HuskRenderJob, self).__init__(*args, **kwargs)
            
            self.cmd = "husk"
            self.scene_path = scene_path            
            if scene_path:
                self.upload_paths.append(scene_path)
            
            # Husk-specific rendering parameters
            self.render_settings = None  # Render settings prim path
            self.camera = None  # Camera prim path
            self.render_delegate = "HdStormRendererPlugin"  # Default to Storm, can be Karma, Arnold, etc.
            self.purpose = None  # USD purposes to render
            self.complexity = None  # Geometry complexity
            
            self.additional_cmd_args = ""
            self.pre_task_cmd = ""
            self.post_task_cmd = ""
            self.post_job_cmd = None
            self.frame_step = 1
            self.frames = None

        def _get_task_data(self):

            task_data = []
            
            if not self.frames:
                self.frames = cioseq.sequence.Sequence.create(self.start_frame, self.end_frame+1)

            LOG.debug("Using a chunk size of {}".format(self.chunk_size))
            LOG.debug("Frames: {}".format(self.frames))

            for start in range(0, len(self.frames), self.chunk_size):
                chunk_frames = self.frames[start:start+self.chunk_size]
                start_frame = chunk_frames[0]
                end_frame = chunk_frames[-1]
                
                # Build husk-specific arguments
                husk_args = []
                
                # Render delegate (e.g., HdStormRendererPlugin, BRAY::HdKarmaRendererPlugin, HdArnoldRendererPlugin)
                if self.render_delegate:
                    husk_args.append("-R {}".format(self.render_delegate))
                
                # Camera path
                if self.camera:
                    husk_args.append("-c {}".format(self.camera))
                
                # Output path
                if self.output_path:
                    husk_args.append("-o {}".format(self.output_path))
                
                # Render settings prim
                if self.render_settings:
                    husk_args.append("-s {}".format(self.render_settings))
                
                # Purpose (geometry, render, proxy, guide)
                if self.purpose:
                    husk_args.append("--purpose {}".format(self.purpose))
                
                # Complexity
                if self.complexity:
                    husk_args.append("--complexity {}".format(self.complexity))
                
                husk_args_str = " ".join(husk_args)
                
                command_args = {'cmd': self.cmd,
                                'start_frame': start_frame,
                                'end_frame': end_frame,
                                'husk_args': husk_args_str,
                                'scene_path': self.scene_path,
                                'extra_args': self.additional_cmd_args,
                                'pre_task_cmd': self.pre_task_cmd if self.pre_task_cmd else '',
                                'post_cmd': self.post_task_cmd if self.post_task_cmd else ''}
                
                # Build the full command
                cmd_parts = []
                if command_args['pre_task_cmd']:
                    cmd_parts.append(command_args['pre_task_cmd'])
                
                husk_cmd = "{cmd} {husk_args} -f {start_frame} {end_frame} {extra_args} {scene_path}".format(**command_args)
                cmd_parts.append(husk_cmd)
                
                if command_args['post_cmd']:
                    cmd_parts.append(command_args['post_cmd'])
                
                full_command = " && ".join([part for part in cmd_parts if part])
                
                task_data.append({"frames": "{}-{}".format(start_frame, end_frame),
                                  "command": full_command})
                
            if self.post_job_cmd is not None:
                task_data.append({"frames": "999999", 
                                  "command": self.post_job_cmd})
                
                self.scout_frames = ",".join([str(f) for f in self.frames])
                
            return task_data
        
        def _get_frame_range(self):
            """Get the frame range for the job"""
            if hasattr(self, 'start_frame') and hasattr(self, 'end_frame'):
                return "{}-{}".format(self.start_frame, self.end_frame)
            return ""

