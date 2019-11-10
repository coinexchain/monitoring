from slack_webhook import Slack
import requests
import subprocess
import json
import dateutil.parser
from datetime import datetime
import time

validator_address = 'BA58C4541A86F64854B892312144C2741578E433'
validator_valconspub = 'cettestvalconspub1zcjduepqwfyy05yc6vkf8jquueumx2hc940wxz46qcyhu9uq3dedfe3vvuuqxtz2ca'
blocks_rest_url = 'http://localhost:1317/blocks/latest?format=json&kind=block'
signing_rest_url = 'http://localhost:1317/slashing/validators/' + validator_valconspub + '/signing_info'
node_tcp_url = 'tcp://localhost:26657'
cetcli = '/home/ubuntu/cetcli'
alert_non_block = 60
alert_miss_block = 5
request_time_out = 5
slack_url = 'https://hooks.slack.com/services/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'
slack = Slack(url=slack_url)

# ------------------------------------------GET latest_block_time to check node receive block.
try:
    status_bytes = subprocess.check_output([cetcli, 'status', '--node=' + node_tcp_url], timeout=request_time_out)

    latest_block_time = json.loads(status_bytes)['sync_info']['latest_block_time']
    block_time = dateutil.parser.parse(latest_block_time)
    block_tval = time.mktime(block_time.timetuple())

    now_time = datetime.utcnow()
    now_tval = time.mktime(datetime.utcnow().timetuple())

    if now_tval - block_tval > alert_non_block:
        slack.post(text='The node has not received a new block for more than ' + str(alert_non_block) + ' seconds')
except subprocess.CalledProcessError as e:
    slack.post(text='Requests cetcli status ' + '--node=' + node_tcp_url + ' error code : ' + e.returncode + 'and \n'
                    + e.output)

# -------------------------------------------GET consensus_addresses to check node participates in the consensus.
r = requests.get(url=blocks_rest_url, timeout=request_time_out)
data = r.json()
if r.status_code == 200:
    consensus_addresses = []
    for pre_commits_info in data['block']['last_commit']['precommits']:
        if pre_commits_info is None:
            continue
        consensus_addresses.append(pre_commits_info['validator_address'])
    if validator_address not in consensus_addresses:
        slack.post(text='The node has not participates in the consensus. \n'
                        'See Request block ' + data['block']['header']['height'])
else:
    slack.post(text='Requests GET ' + blocks_rest_url + '\n error code : ' + str(r.status_code))

# -------------------------------------------GET signing_info to check node miss block.
r = requests.get(url=signing_rest_url, timeout=request_time_out)
data = r.json()
if r.status_code == 200:
    missed_blocks_counter = data['result']['missed_blocks_counter']
    if int(missed_blocks_counter) > alert_miss_block:
        slack.post(text='The node has miss ' + missed_blocks_counter + 'blocks')
else:
    slack.post(text='Requests GET ' + signing_rest_url + '\n error code : ' + str(r.status_code))
