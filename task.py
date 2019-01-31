from mongoengine import *
from datetime import datetime
import util
from catchup import Catchup

class Task(Document):

  catchup_id = ObjectIdField()
  run_date = DateTimeField()

  def create_task(catchup_id, run_date):
    task_obj = Task(catchup_id=catchup_id,
                    run_date=run_date
                  ).save()
    return task_obj
  
  def clean_tasks():
    curr_date = datetime.now()
    for task in Task.objects:
      if curr_date > task.run_date:
        task.delete()
  
  def init_tasks(sched):
    for task in Task.objects:
      catchup_obj = Catchup.objects.get(id=task.catchup_id)
      job = sched.add_job(util.run_catchup_event_generate, run_date=task.run_date, args=[catchup_obj, sched])
      print(job)