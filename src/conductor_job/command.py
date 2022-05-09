import logging

from . import job

LOG = logging.getLogger(__name__)

class CommandJobError(job.JobError):
    pass


class CommandJob(job.Job):

    def __init__(self, *args , **kwargs):
    
        super(CommandJob, self).__init__(*args, **kwargs)
        
        self.output_path = "/tmp"
        self.instance_count = 1
        
    def _get_task_data(self):
        task_data = []
        
        # Create a task for every instance that's been requested
        for instance_number in range(1, self.instance_count+1):
            task_data.append({"frames": str(instance_number), "command": self.cmd})
        
        return task_data
    
    def validate_job(self):
        return True