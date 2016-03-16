from apscheduler.schedulers.blocking import BlockingScheduler
from banking import PlaidData

dataObject = PlaidData()
def tick():
	dataObject.getData('wells', 'joefarned', 'angela0816', 'joefarned@gmail.com')

sched = BlockingScheduler()
sched.add_job(tick, 'interval', seconds = 15)
sched.start()
