def build_logfile(job, task=None, user1=None, user2=None):
    """
    Builds the log filename based on the source host, destination host, and users.
    Format: {source_host}_{dest_host}_{user1}--{user2}.log
    """
    u1 = user1 or (task.user1 if task else None)
    u2 = user2 or (task.user2 if task else None)
    return f"{job.source_host}_{job.dest_host}_" f"{u1}--{u2}.log"
