class Task(object):
    def __init__(self, task, answer_pattern, done, start_time):
        self.task = task
        self.answer_pattern = answer_pattern
        self.done = done
        self.start_time = start_time

    def __repr__(self):
        return "<Task('%s', '%s', '%s', '%s')>" % (self.task, self.answer_pattern, self.done, self.start_time)