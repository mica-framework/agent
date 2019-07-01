# ================================================
# Welcome to the MiCA Framework - Agent
# MiCA = Microservice-based Simulation of Cyber Attacks
# --
#
# This Agent basically works as a so called Job-Agent. That means, the Server provides a list of
# Jobs which should be processed by the agent. Those jobs are basically docker run commands which
# will be executed through the agent at the victims host.
# This Agent allows to run the docker-commands at a windows (within powershell) or unix-based os (within a shell).
#
# For a more detailed overview of the Server please check out the README.md.
# --
#
# Developed By
# Andreas Zinkl
# E-Mail: zinklandi@gmail.com
# ================================================
from sys import platform
import sys
import subprocess
import shlex
import requests
import socket
import time
import os
import docker
import argparse

# ===================== CONFIG STARTS HERE ===========================

# the MiCA-API Version
API_VERSION = "1"

# is needed! within the laboratory, it is the IM-SEC-001 for now
MICA_SERVER_URL = "localhost" # e.g. http://127.0.0.1

# will be automatically overwritten - so it is kind of deprecated
HOSTNAME = "LOCALHOST"

# Request-Delay
POLLING_DELAY = 5

# ===================== CONFIG ENDS HERE ===========================

# get arguments which can be given
parser = argparse.ArgumentParser()
parser.add_argument('-b', '--backend', action='store',
    help='The host address of the backend server e.g. http://127.0.0.1')
parser.add_argument('-l', '--logging', action='store_true',
    help='Setting the logging to a local logfile')
args = parser.parse_args()
if args.backend:
    MICA_SERVER_URL = str(args.backend)
LOGGING = args.logging


# auto configure the hostname
host = socket.gethostname()
if host is not None:
    HOSTNAME = str(host).upper()

MICA_SERVER_API = "{}/api/v{}/attack".format(MICA_SERVER_URL, API_VERSION)

# create a list of running jobs
running_jobs = []
waiting_jobs = []


# add a new job to the job list
def _add_new_job(uuid):
    running_jobs.append("{}".format(uuid))


# remove a job from the job list
def _delete_job(uuid):
    running_jobs.remove("{}".format(uuid))


def _add_waiting_job(uuid):
    waiting_jobs.append("{}".format(uuid))

def _delete_job_from_waiting(uuid):
    waiting_jobs.remove("{}".format(uuid))


# gets a docker run command and adds a name to it
def _add_name_to_docker_command(command, container_name):
    run_text = "docker run "
    index = command.find(run_text)
    return "{} {} {}".format(command[:index+len(run_text)], "--name {}".format(container_name), command[index+len(run_text):])


# executing the attack simulation command on a windows os
def execute_powershell_command(command, uuid):
    try:
        cmd_str = 'start /MIN powershell -windowstyle hidden -command "%s"' % command
        log("### >> EXEC: {}".format(command))
        notify_attack_start(cmd_str, uuid)
        subprocess.Popen(cmd_str, shell=True)

        # only notify it if the docker command is not detached or it is no docker command
        if "docker run " not in cmd_str:
            notify_attack_end(uuid)
    except os.error as err:
        log("### execution error = {}".format(err))


# executing the attack simulation command on a unix-based os
def execute_shell_command(command, uuid):
    try:
        log("### >> EXEC: {}".format(command))
        notify_attack_start(command, uuid)
        subprocess.Popen(command, shell=True)

        # only notify it if the docker command is not detached or it is no docker command
        if "docker run " not in command:
            notify_attack_end(uuid)
    except os.error as err:
        log("### execution error = {}".format(err))


# registering the agent at the server
def register_at_sever():
    server_url = "{}/api/v{}/register".format(MICA_SERVER_URL, API_VERSION)
    log(">> Registering the Agent at the MiCA-Server (at URL={})".format(server_url))
    req_url = "{}?victim={}".format(server_url, HOSTNAME)
    res = requests.post(req_url)
    if res.status_code != 200:
        log("#### Error while registering the Agent! Please verify that everything is running!")
        log(">> Agent is shutting down..")
        exit(500)
    else:
        log(">> Successfully registered the Agent!")


# notify the server that an attack has started
def notify_attack_start(command, uuid):
    log("Notifying the Start of the Attack: {}".format(command, uuid))
    server_url = "{}/api/v{}/attack/start".format(MICA_SERVER_URL, API_VERSION)
    res = requests.post(server_url, json={
        'hostName': HOSTNAME,
        'uuid': uuid,
        'command': command
    })


# notify the server that an attack has finished
def notify_attack_end(uuid):
    log("Notifying the End of the Attack: {}".format(uuid))
    server_url = "{}/api/v{}/attack/end".format(MICA_SERVER_URL, API_VERSION)
    res = requests.post(server_url, json={
        'hostName': HOSTNAME,
        'uuid': uuid,
    })


# check if the given attack is still running
def _job_is_running(uuid):
    log("Start checking if job is running")
    docker_client = docker.from_env()
    docker_client.containers.prune()
    running_container = docker_client.containers.list(filter={"name": uuid})
    if len(running_container) > 0:
        return True
    else:
        return False


# logging of the agent
def log(message, print_to_console=True):
    # check if we should print the log message
    if print_to_console:
        print(message)

    # check if we should write the logs to a file
    if LOGGING:
        with open('./process.log', 'a') as logfile:
            logfile.write(message + "\n")


# now we know we are at a windows system
log(">> Agent is up and running on a {} OS!!".format(platform))
register_at_sever()

# check the server for jobs
url = "{}?victim={}".format(MICA_SERVER_API, HOSTNAME)
log(">> Running the Agent and waiting for jobs..")
while True:

    # we need to wait 5 seconds for each request... that does not generate to much traffic
    time.sleep(POLLING_DELAY)

    # try to get a new job
    try:
        # check if a waiting job was executed right now
        for job_uuid in waiting_jobs:
            is_running = _job_is_running(job_uuid)
            log("Job {} is {}".format(job_uuid, 'running' if is_running else 'waiting'))
            if is_running:
                _delete_job_from_waiting(job_uuid)
                _add_new_job(job_uuid)

        # each time check the running jobs
        for job_uuid in running_jobs:
            is_running = _job_is_running(job_uuid)
            log("Job {} is {}".format(job_uuid, 'running' if is_running else 'stopped'))
            if not is_running:
                _delete_job(job_uuid)
                notify_attack_end(job_uuid)

        # handle the jobs
        response = requests.get(url)
        if response.status_code != 200:
            continue

        result = response.json()
        if result['data']:
            # get the data
            data = result['data']

            # we have a job!
            cmd = data['job']
            uuid = data['uuid']

            # is it a docker run command - if so, then add a name = uuid
            if "docker run" in cmd:
                cmd = _add_name_to_docker_command(cmd, uuid)
                _add_waiting_job(uuid)
                log("Start new docker job {}".format(uuid))

            # check for an empty cmd string
            if cmd:
                # check if we are at a windows system or unix-based
                log("Got a new Job! {}".format(cmd))
                if platform == 'win32' or platform == 'cygwin':
                    execute_powershell_command(cmd, uuid)
                else:
                    execute_shell_command(cmd, uuid)

    except requests.exceptions.RequestException as reqErr:
        log("#### Error while requesting a job.. = {}".format(reqErr.strerror))
    except Exception as err:
        log("#### GENERAL ERROR = {}".format(err))
