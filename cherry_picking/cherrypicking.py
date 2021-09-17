#!/usr/bin/env python

#
# Imports
#

import pulpcore.client.pulp_rpm as pulp_rpm
import pulpcore.client.pulpcore as pulpcore
import yaml
import sys
import json
import colorama

from colorama import Fore
from colorama import Style
from time import sleep

#
# Variables
#

config_file = 'config.yaml'
data_file = 'cherrypicking.yaml'
config = yaml.load(open(config_file, 'r'), Loader=yaml.FullLoader)
data = yaml.load(open(data_file, 'r'), Loader=yaml.FullLoader)

#
# RPM Client config
#

client_config = pulp_rpm.Configuration (
    host=config['host'],
    username=config['username'],
    password=config['password']
)
api_client = pulp_rpm.ApiClient(configuration=client_config)

#
# Pulpcore Client config
#

pulpcore_client_config = pulpcore.Configuration (
    host=config['host'],
    username=config['username'],
    password=config['password']
)
pulpcore_api_client = pulpcore.ApiClient(configuration=pulpcore_client_config)

#
# Functions
#

def get_repo_href(api_client, name=None):
    """Get the href of an rpm repository

    Returns the Pulp Href of an rpm repository

    :param api_client: Pulp api client to use for the connection
    :param name: Name of the repository
    :return: String
             Pulp_href of the repository
    """
    api_instance=pulp_rpm.RepositoriesRpmApi(api_client=api_client)
    response=api_instance.list(limit=1, name=name)
    if response.count < 1:
        sys.exit("There were no repositories found")
    elif response.count >1:
        sys.exit("There were more then 1 repositories found")
    return response.results[0].pulp_href

def get_latest_repo_version_href(api_client, name=None):
    """Get the latest version href of an rpm repository

    Returns the Pulp Href of an rpm repository

    :param api_client: Pulp api client to use for the connection
    :param name: Name of the repository
    :return: String
             Pulp_latest_version_href of the repository
    """
    api_instance=pulp_rpm.RepositoriesRpmApi(api_client=api_client)
    response=api_instance.list(limit=1, name=name)
    if response.count < 1:
        sys.exit("There were no repositories found")
    elif response.count >1:
        sys.exit("There were more then 1 repositories found")
    return response.results[0].latest_version_href

def search_modulemd(api_client, name=None, stream=None, repository_version=None):
    """Search modules

    Search for modules in a specific repository_version of the whole of pulp

    :param api_client: Pulp api client to use for the connection
    :param name: Name of the modulemd
    :param stream: stream of the modulemd
    :param repository_version: repository version to look for modules
    :return: set(String)
             set with the pulp_href of the found modulemds
    """
    api_instance = pulp_rpm.ContentModulemdsApi(api_client=api_client)
    limit=5
    offset=0
    response=pulp_rpm.PaginatedrpmModulemdResponseList(next='foo')
    modulemds=set()
    while response.next != None:
        response=api_instance.list(limit=limit, offset=offset, name=name, stream=stream, repository_version=repository_version)
        for m in response.results:
            print("Adding following module:")
            print(json.dumps({"name": m.name, "stream": m.stream, "packages": m.packages}, sort_keys=False, indent=4))
            #modulemds.update(m.packages)
            modulemds.add(m.pulp_href)
        offset+=limit
    return(modulemds)

def search_package(api_client, name=None, version=None, release=None, arch=None, repository_version=None):
    """Search packages

    Search for packages in a specific repository_version of the whole of pulp

    :param api_client: Pulp api client to use for the connection
    :param name: Name of the packages
    :param version: Version of the package
    :param release: Release of the package
    :param arch: architecture of the package
    :param repository_version: repository version to look for modules
    :return: set(String)
             set with the pulp_href of the packages
    """
    api_instance = pulp_rpm.ContentPackagesApi(api_client=api_client)
    limit=5
    offset=0
    response=pulp_rpm.PaginatedrpmPackageResponseList(next='foo')
    packages=set()
    while response.next != None:
        response = api_instance.list(limit=limit, offset=offset, name=name, version=version, release=release, arch=arch, repository_version=repository_version, fields='name,version,release,arch,pulp_href')
        for p in response.results:
            print("Adding following package:")
            print(json.dumps({"name": p.name, "version": p.version, "release": p.release, "arch": p.arch}, sort_keys=False, indent=4))
            packages.add(p.pulp_href)
        offset+=limit
    return (packages)

def copy(api_client, config=None, dependency_solving=True):
    """Copy content

    Search for modules in a specific repository_version of the whole of pulp

    :param api_client: Pulp api client to use for the connection
    :param config: copy config
    :param dependency_solving: solve dependencies
    :return: String
             pulp_href of the generated task
    """
    api_instance = pulp_rpm.RpmCopyApi(api_client=api_client)
    copy = pulp_rpm.Copy(config=config, dependency_solving=dependency_solving)
    return api_instance.copy_content(copy)

def wait_until_task_has_finished(pulpcore_api_client, task_href=None):
    """ Wait until pulp task is finished

    Wait until pulp task is finished, if the task failed, the program will be exited

    :param api_client: Pulp api client to use for the connection
    :param task_href: The href of the pulp task
    """
    api_instance = pulpcore.TasksApi(api_client=pulpcore_api_client)
    task = api_instance.read(task_href)
    print(task.to_dict)
    print()
    while task.state != 'completed':
        sleep(2)
        task = api_instance.read(task_href)
        print(task.to_dict)
        print()
        if task.state == 'failed':
            sys.exit("Task failed with following error %s"%json.dumps(task.error, sort_keys=False, indent=4))
        
def copy_content(api_client, pulpcore_api_client, content_type, copy_config):
    """Copy content wrapper funtion

    Wrapper function around copy that will print verbose output, wait until task has finished,
    show task status etc ...
    """
    print(Fore.BLUE + Style.BRIGHT)
    print("##################################################")
    print("Using following copy config for %s:"%content_type)
    print("##################################################")
    print(Style.RESET_ALL)
    print(json.dumps(copy_config, sort_keys=False, indent=4))
    response = copy(api_client=api_client, config=copy_config)
    
    print(Fore.BLUE + Style.BRIGHT)
    print("##################################################")
    print("Waiting until task %s has finished for %s"%(response.task,content_type))
    print("##################################################")
    print(Style.RESET_ALL)
    wait_until_task_has_finished(pulpcore_api_client, task_href=response.task)

#
# Script prober
#

dest_repo_href=get_repo_href(api_client=api_client, name=data['dest_repo'])
packages_copy_config=list()
modules_copy_config=list()

print(Fore.BLUE + Style.BRIGHT)
print("##################################################")
print("Cherry picking %s"%data['dest_repo'])
print("##################################################")
print(Style.RESET_ALL)

for repo in data['content']:
    packages_copy_hrefs=set()
    modules_copy_hrefs=set()

    print(Fore.GREEN)
    print("Cherry picking %s from repo %s"%(repo['desc'],repo['name']))
    print(Style.RESET_ALL)

    repository_version=get_latest_repo_version_href(api_client, name=repo['name'])
    print(repository_version)

    if 'packages' in repo:
        print(Fore.RED)
        print("Searching packages %s"%repo['desc'])
        print(Style.RESET_ALL)

        for package in repo['packages']:
            packages_copy_hrefs.update(search_package(api_client=api_client, **package, repository_version=repository_version))

        packages_copy_config.append({
            "source_repo_version": repository_version,
            "dest_repo": dest_repo_href,
            "content": list(packages_copy_hrefs),
        })

    if 'modules' in repo:
        print(Fore.RED)
        print("Searching modules %s"%repo['desc'])
        print(Style.RESET_ALL)

        for module in repo['modules']:
            modules_copy_hrefs.update(search_modulemd(api_client=api_client, **module, repository_version=repository_version))

        modules_copy_config.append({
            "source_repo_version": repository_version,
            "dest_repo": dest_repo_href,
            "content": list(modules_copy_hrefs),
        })


copy_content(api_client, pulpcore_api_client, 'packages', packages_copy_config)
copy_content(api_client, pulpcore_api_client, 'modules', modules_copy_config)
#print(Fore.BLUE + Style.BRIGHT)
#print("##################################################")
#print("Using following copy config for packages:")
#print("##################################################")
#print(Style.RESET_ALL)
#print(json.dumps(packages_copy_config, sort_keys=False, indent=4))
#packages_response = copy(api_client=api_client, config=packages_copy_config)
#
#print(Fore.BLUE + Style.BRIGHT)
#print("##################################################")
#print("Waiting until task %s has finished for packages"%packages_response.task)
#print("##################################################")
#print(Style.RESET_ALL)
#wait_until_task_has_finished(pulpcore_api_client, task_href=packages_response.task)
#
#print(Fore.BLUE + Style.BRIGHT)
#print("##################################################")
#print("Using following copy config for modules:")
#print("##################################################")
#print(Style.RESET_ALL)
#print(json.dumps(modules_copy_config, sort_keys=False, indent=4))
#modules_response = copy(api_client=api_client, config=modules_copy_config)
#
#print(Fore.BLUE + Style.BRIGHT)
#print("##################################################")
#print("Waiting until task %s has finished for modules"%modules_response.task)
#print("##################################################")
#print(Style.RESET_ALL)
#wait_until_task_has_finished(pulpcore_api_client, task_href=modules_response.task)
