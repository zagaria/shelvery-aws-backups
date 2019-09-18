import logging
import json
import os

from shelvery.factory import ShelveryFactory
from shelvery.queue import ShelveryQueue



def lambda_handler(event, context):

    sqs_url = os.environ['shelvery_sqs_queue_url']
    sqs_wait = os.environ['shelvery_sqs_queue_wait_period']

    sqs = ShelveryQueue(sqs_url,sqs_wait);
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(f"Received event\n{json.dumps(event,indent=2)}")

    # handle messages from sns, sqs, cloudwatch secheduled events
    if 'Records' in event:
        for record in event['Records']:
            if 'Sns' in record:
                payload = json.loads(record['Sns']['Message'])
            elif 'body' in record:
                payload = json.loads(record['body'])
    else:
        payload = event

    if 'backup_type' not in payload:
        raise Exception("Expecting backup type in event payload in \"backup_type\" key")

    if 'action' not in payload:
        raise Exception("Expecting backup action in event payload in \"action\" key")

    backup_type = payload['backup_type']
    action = payload['action']

    # create backup engine
    backup_engine = ShelveryFactory.get_shelvery_instance(backup_type)
    backup_engine.set_lambda_environment(payload, context)

    method = backup_engine.__getattribute__(action)

    if 'arguments' in payload:
        try:
           method(payload['arguments'])
        except:
           logger.info(f"Exception in action {action} for {backup_type}. Retry again (push message to queue again)")
           sqs.send(payload);
    else:
        method()

    return 0
