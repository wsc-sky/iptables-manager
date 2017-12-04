from django.shortcuts import render
import json, requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
import base64
import os, time
from django.shortcuts import render, render_to_response, redirect
from django.views.decorators.csrf import csrf_exempt
import subprocess32 as subprocess

# Create your views here.
# !/usr/bin/python
# -*- coding: UTF-8 -*-
def encode_base64(s):
    return base64.b64encode(s)


def check_angent_status(request, ip, plat_id):
    url = 'http://paas.bk.garenanow.com:80/api/c/compapi/job/get_agent_status/'
    post_data = {
        "app_code": "iptables-manager",
        "app_secret": "4d075307-f088-496d-b073-3fb0fd6983bb",
        "bk_token": "9NUyTFIfBihjuK7peFdXcEuvZbD1BTyII12ORxhnu50",
        "app_id": 9,
        "ip_infos": [
            {
                "ip": ip,
                "plat_id": int(plat_id)
            }
        ]
    }
    result = requests.post(url, data=json.dumps(post_data)).json()

    return JsonResponse(result)


def fast_push_file(filename,ip):
    url = 'http://paas.bk.garenanow.com:80/api/c/compapi/job/fast_push_file/'

    check_restart = iptables_check(filename)

    if check_restart['test_restart'] == None:
        return check_restart

    if check_restart['test_restart'] == False:
        return check_restart

    post_data = {
        "app_code": "iptables-manager",
        "app_secret": "4d075307-f088-496d-b073-3fb0fd6983bb",
        "bk_token": "9NUyTFIfBihjuK7peFdXcEuvZbD1BTyII12ORxhnu50",
        "app_id": 9,
        "file_source": [
            {
                "account": "root",
                "ip_list": [
                    {
                        "ip": '10.10.60.198',
                        "source": 1
                    }
                ],
                "file": '/etc/sysconfig/iptables'
            }
        ],
        "account": "root",
        "file_target_path": "/etc/sysconfig/",
        "ip_list": [
            {
                "ip": ip,
                "source": 1
            }
        ],
    }

    result =  requests.post(url, data=json.dumps(post_data)).json()

    time.sleep(1)

    return  result

def fast_execute_script(script_name,ip):
    url = 'http://paas.bk.garenanow.com:80/api/c/compapi/job/fast_execute_script/'
    f = open(os.path.join(settings.BASE_DIR + '/script/', script_name), 'r')
    script_content = encode_base64(f.read())
    post_data = {
        "app_code": "iptables-manager",
        "app_secret": "4d075307-f088-496d-b073-3fb0fd6983bb",
        "bk_token": "9NUyTFIfBihjuK7peFdXcEuvZbD1BTyII12ORxhnu50",
        "app_id": 9,
        "content": script_content,
        "ip_list": [
            {
                "ip": ip,
                "source": 1
            }
        ],
        "type": 1,
        "account": "root",
    }

    result =  requests.post(url, data=json.dumps(post_data)).json()

    time.sleep(1)

    return result

def check_task_log(task_id):
    url = 'http://paas.bk.garenanow.com:80/api/c/compapi/job/get_task_ip_log/'
    post_data = {
        "app_code": "iptables-manager",
        "app_secret": "4d075307-f088-496d-b073-3fb0fd6983bb",
        "bk_token": "9NUyTFIfBihjuK7peFdXcEuvZbD1BTyII12ORxhnu50",
        "task_instance_id": str(task_id)
    }

    result = requests.post(url, data=json.dumps(post_data)).json()

    if result['result']:
        log_content = result['data'][0]['stepAnalyseResult'][0]['ipLogContent'][0]['logContent']
        return log_content
    else:
        return ''

def fetch_iptables(ip):
    result = fast_execute_script('fetch_iptables.sh', ip)


    if result['result']:
        task_id = result['data']['taskInstanceId']
        log_content = check_task_log(task_id)
        if log_content!='':
            return {'result': 'true', 'iptables': log_content, 'message': result}
        else:
            return {'result': 'true', 'iptables': '', 'message': result}
    else:
        return {'result': 'true', 'iptables': '', 'message': result}

    return {'result': 'true', 'iptables': '', 'message': result}


def iptables_check(filename):
    command = "scp {path} {username}@{ip}:/home/ld-sgdev/weisc".format(
        path =os.path.join(settings.BASE_DIR + '/upload_tmp_file/', 'iptables'),
        username = 'ld-weisc',
        ip = '203.117.172.198',
    )
    print os.path.join(settings.BASE_DIR + '/upload_tmp_file/', 'iptables')
    result1 = subprocess.call(command,shell=True)

    print result1

    result = fast_execute_script('check_iptables.sh', '10.10.60.198')
    if result['result']:
        task_id = result['data']['taskInstanceId']
        log_content = check_task_log(task_id)
        if 'OK' in log_content and 'FAILED' not in log_content and 'Error' not in log_content:
            result['test_restart'] = True
            return result
        else:
            result['test_restart'] = False
            result['message'] = 'Restart on test server failed !! \n'+log_content
            return result

    return result



def upload_file(ip, filename):


    result = fast_push_file(filename, ip)

    if result.get('test_restart', True) == False:
        result['excute_success'] = False
        return result

    if result['result']:

        result = fast_execute_script('restart_iptables.sh',ip)

        if result['result']:
            task_id = result['data']['taskInstanceId']
            log_content = check_task_log(task_id)
            if 'OK' in log_content and 'FAILED' not in log_content:
                result['message'] = log_content.split('stdin: is not a tty')[1]
                result['excute_success'] = True
                return result


    return result


def home(request):
    return render(request, 'home.html', {'iptables': '', 'message': '', 'ip': '', 'excute_success': False})


def search_by_ip(request):
    ip = request.GET['ip']
    result = fetch_iptables(ip)
    message = result['message']['message']
    try:
        iptables = result['iptables'].split('stdin: is not a tty\n')[1]
    except:
        iptables = ''
        pass

    print iptables

    if message != '':
        return render(request, 'home.html', {'iptables': '', 'ip': ip, 'message': message, 'excute_success': False})

    return render(request, 'home.html', {'iptables': iptables, 'ip': ip, 'message': 'Fetch iptables successfully' ,'excute_success': True})


@csrf_exempt
def submit_iptables(request):
    ip = request.POST['ip']
    iptables = request.POST['iptables']


    f = open(os.path.join(settings.BASE_DIR + '/upload_tmp_file/', 'iptables'), 'w+t')
    f.write(iptables)
    print f.read()

    result = upload_file(ip, 'iptables')

    excute_success = False if result['excute_success']==None else result['excute_success']

    return render(request, 'home.html', {'iptables': iptables, 'ip': ip, 'message': result['message'], 'excute_success': excute_success })
