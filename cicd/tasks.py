# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import logging as log
import sys
import time

import jenkins
import requests
from celery import shared_task

from confs.ysx import prod as cf


reload(sys)
sys.setdefaultencoding('utf-8')


def get_job_name(project_name):
    project_conf = requests.get('http://127.0.0.1:8001/cicd/project_conf').json()
    for project_type, project_info in project_conf.items():
        if project_name in project_info.keys():
            if 'tmc' == project_type:
                job_name = 'java_prod'
            elif 'srv' == project_type:
                job_name = 'java_srv_prod'
            elif 'node' == project_type:
                job_name = 'node_prod'
            elif 'static' == project_type:
                job_name = 'fe_prod'
            break
    return job_name


def send2wechat(msg):
    url = 'http://msg.inf.bandubanxie.com/api/v0.2/msg/qiye_weixin'
    data = dict(
        group=u'技术部',
        content=msg,
        app='prod',  # 云舒写生产中心
        sed='quke'
    )
    r = requests.post(url, data=data)
    log.info('send msg to qiye_weixin: {}'.format(r.text))


def jenkins_server(job_name, project_name, release_data, synchronized=True):
    try:
        server = jenkins.Jenkins(url=cf['jenkins']['url'],
                                 username=cf['jenkins']['username'],
                                 password=cf['jenkins']['password'])

        next_build_number = server.get_job_info(job_name)['nextBuildNumber']
        server.build_job(job_name, parameters=release_data)
        log.info('invoke jenkins [{}] | {} | {}'.format(next_build_number, project_name, release_data))

        if synchronized:
            time.sleep(10)
            while True:
                time.sleep(2)
                last_build_info = server.get_build_info(job_name, int(next_build_number) - 1)
                if last_build_info['building']:
                    log.info('last build is not finished, waiting')
                    continue

                current_build_info = server.get_build_info(job_name, int(next_build_number))
                build_status = current_build_info['building']

                if not build_status:
                    built_status = current_build_info['result']
                    log.info('finished building: {}'.format(built_status))

                    if 'FAILURE' == built_status:
                        break
                    elif 'SUCCESS' == built_status:
                        return project_name
                    else:
                        break

        return project_name
    except:
        e_type, e_value, e_traceback = sys.exc_info()
        log.error('{}|{}|{}|{}|{}'.format(e_type, e_value, e_traceback.tb_lineno, project_name, release_data))


@shared_task
def emit_jenkins(apprival_content):
    approval_id = apprival_content[0]['approval_id']
    synchronized = True if apprival_content[0]['rely'] == 'true' else False

    for release_data in apprival_content:
        project_name = release_data.get('project')
        job_name = get_job_name(project_name)
        release_data.pop('approval_id')
        ret = jenkins_server(job_name, project_name, release_data, synchronized)

        if not ret:
            log.error('build {} failed, exit'.format(project_name))
            send2wechat('jenkins build failed: {}, {}'.format(project_name, release_data))
            break
        log.info('[{}]-[{}] send to jenkins successful'.format(approval_id, ret))

    return json.dumps(dict(status='success', approval_id=approval_id))
