import logging

import cioseq.sequence
import ciopath.gpath

from . import job

LOG = logging.getLogger(__name__)

class MayaRenderJob(job.Job):
    
        PRODUCT_TO_RENDERER_MAPPING = {"arnold-maya":"arnold",
                                       "renderman-maya": "renderman",
                                       "redshift-maya": "redshift",
                                       "vray-maya": "vray"}
    
        def __init__(self, scene_path=None, project_path=None, *args , **kwargs):
            
            super(MayaRenderJob, self).__init__(*args, **kwargs)
            
            self.cmd = "Render"
            self.render_layer = "defaultRenderLayer"
            self.scene_path = scene_path
            self.project_path = project_path            
            self.upload_paths.append(scene_path)
            self.additional_cmd_args = ""
            self.post_task_cmd = ""
            self.post_job_cmd = None
            self.frames = None
            self.frame_step = 1
            self.log_level = "2"
            self.renderer = "File"
 
        def _get_task_data(self):

            LOG.debug("Using a chunk size of {}".format(self.chunk_size))
            
            task_data = []
            
            if not self.frames:
                self.frames = cioseq.sequence.Sequence.create(self.start_frame, self.end_frame+1)
            
            LOG.debug("Frames: {}".format(self.frames))

            for start in range(0, len(self.frames), self.chunk_size):
                chunk_frames = self.frames[start:start+self.chunk_size]
                start_frame = chunk_frames[0]
                end_frame = chunk_frames[-1]
                
                command_args = {'cmd': self.cmd,
                                'renderer': self.PRODUCT_TO_RENDERER_MAPPING[self.renderer],
                                'start_frame': start_frame,
                                'end_frame': end_frame,
                                'frame_step': self.frame_step,
                                'render_layer': self.render_layer,
                                'output_path': ciopath.gpath.Path(self.output_path).fslash(with_drive=False),
                                'project_path': ciopath.gpath.Path(self.project_path).fslash(with_drive=False),
                                'scene_path': ciopath.gpath.Path(self.scene_path).fslash(with_drive=False),
                                'extra_args': self.additional_cmd_args,
                                'renderer_args': self.get_renderer_args(self.renderer),
                                'post_cmd': self.post_task_cmd}
                
                task_cmd = { "frames": "{}-{}".format(start_frame, end_frame),
                             "command": "{cmd} -r {renderer} -s {start_frame} -e {end_frame} -b {frame_step} -rl {render_layer} -rd {output_path} -proj {project_path} {renderer_args} {extra_args} {scene_path}".format(**command_args)}
                
                if self.post_job_cmd:
                    task_cmd["command"] += " && {}".format(self.post_task_cmd)
                    
                task_data.append(task_cmd)
                
            if self.post_job_cmd is not None:
                task_data.append({"frames": "999999", 
                                  "command": self.post_job_cmd})
                
                self.scout_frames = ",".join([str(f) for f in self.frames])
                
            return task_data
        
        def get_renderer_args(self, renderer):
            
            args = ""
                
            if renderer == "arnold-maya":
                # Use the same prefix as the Maya project path (ex: /projects/my_project)
                standin_path = "/".join(ciopath.gpath.Path(self.project_path).fslash(with_drive=False).split("/")[0:3])
                args = "-ai:lve {log_level} -ai:sptx {}".format(log_level=self.log_level, standin_path)
                
            return args
        