from celery import Celery, platforms

platforms.C_FORCE_ROOT = True
from  chain import settings
app = Celery('chain')
app.config_from_object('django.conf:settings',)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
import logging,json
logger = logging.getLogger('tasks')

from multiprocessing import current_process
from .ansible_2420.runner import AdHocRunner, PlayBookRunner
from .ansible_2420.inventory import BaseInventory


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task()
def  ansbile_tools(assets,tools,module):
    current_process()._config = {'semprefix': '/mp'}

    ret=[]
    if module == "script":
        for i  in  assets:
            inventory = BaseInventory(i)
            runner = AdHocRunner(inventory)
            tasks = [
                    {"action": {"module": "{}".format(module), "args": "{}".format(tools)}, "name": "script"},
            ]
            retsult = runner.run(tasks, "all")
            hostname = i[0]['hostname']

            try:
                try:
                    data = retsult.results_raw['ok'][hostname]
                    ret.append(json.dumps(data))
                except Exception as e:
                    logger.error(e)
                    try:
                        data = retsult.results_raw['failed'][hostname]
                        ret.append(json.dumps(data))
                    except Exception as  e:
                        logger.error(e)
                        data = retsult.results_raw['unreachable'][hostname]
                        ret.append(json.dumps(data))
            except Exception as e:
                logger.error(e)

    elif  module == 'yml':
        for i in assets:
            try:
                inventory = BaseInventory(i)
                runers = PlayBookRunner(playbook_path=tools, inventory=inventory)
                rets = runers.run()
                print(rets['results_callback'])
                ret.append(json.dumps(rets['results_callback']))
            except Exception as  e:
                logger.error(e)

    return   ret

