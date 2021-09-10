# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import JsonResponse

import re
import json
import requests
import logging as log

from tasks import emit_jenkins

from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def index(request):
    if request.method == 'GET':
        return JsonResponse({'code': 200})
    elif request.method == 'POST':
        return JsonResponse(json.loads(request.body))


@cache_page(60 * 60 * 12)
def get_project_conf(request):
    backend_url = 'http://static-config.sys.bandubanxie.com/release/project_config/project_tmc.conf'
    static_url = 'http://static-config.sys.bandubanxie.com/release/project_config/project_static.conf'
    node_url = 'http://static-config.sys.bandubanxie.com/release/project_config/project_fe.conf'

    machine_list = 'http://static-config.sys.bandubanxie.com/release/release_list_config'
    machine_rc = re.compile(r'bj-.*[0-9]')

    tmc_compile = re.compile('(clcn-(home|admin)|wacc-[a-zA-Z-]+|crm-live|ysx-(in-bi|etl|bi|log|chatcrm|seckill|crm)|(crm|pay|msg)timer).*')
    srv_compile = re.compile('(ysx-[a-zA-Z-]+|yunshuxie-(passport|message)-(service|provider)).*')

    tmc_collections = {}
    srv_collections = {}
    static_collections = {}
    node_collections = {}

    for line in requests.get(backend_url, stream=True).iter_lines():
        proj_config = line.split('|')
        proj_name = proj_config[0]
        proj_git = proj_config[2]

        if tmc_compile.match(proj_name):
            machine_ret = requests.get('{}/{}_prod'.format(machine_list, proj_name)).text
            machines = machine_rc.findall(machine_ret)
            tmc_collections[proj_name] = {'git': proj_git, 'machine': machines}
        elif srv_compile.match(proj_name):
            machine_ret = requests.get('{}/{}_prod'.format(machine_list, proj_name)).text
            machines = machine_rc.findall(machine_ret)
            srv_collections[proj_name] = {'git': proj_git, 'machine': machines}
        else:
            log.error('{} does not belong project_tmc.conf'.format(proj_name))

    for line in requests.get(static_url, stream=True).iter_lines():
        static_config = line.split('|')
        static_name = static_config[0]
        static_git = static_config[2]

        machine_ret = requests.get('{}/{}_prod'.format(machine_list, static_name)).text
        machines = machine_rc.findall(machine_ret)
        static_collections[static_name] = {'git': static_git, 'machine': machines}

    for line in requests.get(node_url, stream=True).iter_lines():
        node_config = line.split('|')
        node_name = node_config[0]
        node_git = node_config[2]

        machine_ret = requests.get('{}/{}_prod'.format(machine_list, node_name)).text
        machines = machine_rc.findall(machine_ret)
        node_collections[node_name] = {'git': node_git, 'machine': machines}

    project_collections = dict(tmc=tmc_collections,
                               srv=srv_collections,
                               static=static_collections,
                               node=node_collections)

    return JsonResponse(project_collections)


@csrf_exempt
def deploy_to_jenkins(request):
    if request.method != 'POST':
        return JsonResponse({'ErrCode': 400, 'ErrMsg': '不支持的操作'})
    else:
        request_data = json.loads(request.body)
        ret = emit_jenkins.delay(request_data)
        task_id = ret.task_id

        log.info('[{}]: {}'.format(task_id, request_data))

        return JsonResponse({'status': 'success', 'task_id': task_id})
