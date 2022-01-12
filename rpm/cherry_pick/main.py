import pulpcore.client.pulp_rpm as pulp_rpm
import pulpcore.client.pulpcore as pulpcore
import yaml
import sys
import json
import colorama

from colorama import Fore
from colorama import Style
from time import sleep
from datetime import date, datetime

class RpmCherryPick:
    """Class used for cherry picking rpm packages and modules in pulpcore
    """

    def __init__(self,data_file,host,username,password):
        """Initialize cherry picking class
        :param data_file: the path to the data file with the packages
        """
        self._data_file = data_file
        self._read_data_file()
        self._rpm_client_config = pulp_rpm.Configuration (
            host=host,
            username=username,
            password=password,
        )
        self._rpm_api_client = pulp_rpm.ApiClient(configuration=self._rpm_client_config)
        self._pulpcore_client_config = pulpcore.Configuration (
            host=host,
            username=username,
            password=password
        )
        self._pulpcore_api_client = pulpcore.ApiClient(configuration=self._pulpcore_client_config)

    def _read_data_file(self):
        print('Reading data file', self._data_file)
        try:
            self._data = yaml.load(open(self._data_file, 'r'), Loader=yaml.FullLoader)
        except:
            print('Error: Data file', self._data_file, 'could not be opened.')
            sys.exit(1)

    def cherry_pick(self):
        print('Starting cherry picking')
        dest_repo_href=self.__get_repo_href(self._data['dest_repo'])

        print(Fore.BLUE + Style.BRIGHT)
        print("##################################################")
        print("Cherry picking %s"%self._data['dest_repo'])
        print("##################################################")
        print(Style.RESET_ALL)

        for repo in self._data['content']:
            packages_copy_hrefs=set()
            modules_copy_hrefs=set()

            print(Fore.GREEN)
            print("Cherry picking %s from repo %s"%(repo['desc'],repo['name']))
            print(Style.RESET_ALL)

            repository_version=self.__get_latest_repo_version_href(name=repo['name'])
            print(repository_version)

            if 'packages' in repo:
                packages_copy_config=list()
                print(Fore.RED)
                print("Searching packages %s"%repo['desc'])
                print(Style.RESET_ALL)

                for package in repo['packages']:
                    packages_copy_hrefs.update(self.__search_package(**package, repository_version=repository_version))

                packages_copy_config.append({
                    "source_repo_version": repository_version,
                    "dest_repo": dest_repo_href,
                    "content": list(packages_copy_hrefs),
                })

                self.__copy_content('packages', packages_copy_config)

            if 'modules' in repo:
                modules_copy_config=list()
                print(Fore.RED)
                print("Searching modules %s"%repo['desc'])
                print(Style.RESET_ALL)

                for module in repo['modules']:
                    modules_copy_hrefs.update(self.__search_modulemd(**module, repository_version=repository_version))

                modules_copy_config.append({
                    "source_repo_version": repository_version,
                    "dest_repo": dest_repo_href,
                    "content": list(modules_copy_hrefs),
                })

                self.__copy_content('modules', modules_copy_config)


        print('Cherry picking complete')

    def __get_repo_href(self, name=None):
        """Get the href of an rpm repository

        Returns the Pulp Href of an rpm repository

        :param api_client: Pulp api client to use for the connection
        :param name: Name of the repository
        :return: String
                 Pulp_href of the repository
        """
        api_instance=pulp_rpm.RepositoriesRpmApi(api_client=self._rpm_api_client)
        response=api_instance.list(limit=1, name=name)
        if response.count < 1:
            sys.exit("There were no repositories found")
        elif response.count >1:
            sys.exit("There were more then 1 repositories found")
        return response.results[0].pulp_href

    def __get_latest_repo_version_href(self, name=None):
        """Get the latest version href of an rpm repository

        Returns the Pulp Href of an rpm repository

        :param api_client: Pulp api client to use for the connection
        :param name: Name of the repository
        :return: String
                 Pulp_latest_version_href of the repository
        """
        api_instance=pulp_rpm.RepositoriesRpmApi(api_client=self._rpm_api_client)
        response=api_instance.list(limit=1, name=name)
        if response.count < 1:
            sys.exit("There were no repositories found")
        elif response.count >1:
            sys.exit("There were more then 1 repositories found")
        return response.results[0].latest_version_href

    def __search_modulemd(self, name=None, stream=None, versions=1, repository_version=None):
        """Search modules

        Search for modules in a specific repository_version of the whole of pulp

        :param api_client: Pulp api client to use for the connection
        :param name: Name of the modulemd
        :param stream: stream of the modulemd
        :param repository_version: repository version to look for modules
        :return: set(String)
                 set with the pulp_href of the found modulemds
        """
        api_instance = pulp_rpm.ContentModulemdsApi(api_client=self._rpm_api_client)
        response=pulp_rpm.PaginatedrpmModulemdResponseList(next='foo')
        modulemds=set()
        response=api_instance.list(limit=versions, name=name, stream=stream, repository_version=repository_version)
        for m in response.results:
            print("Adding following module:")
            print(json.dumps({"name": m.name, "stream": m.stream, "packages": m.packages}, sort_keys=False, indent=4))
            modulemds.add(m.pulp_href)
        return(modulemds)

    def __search_package(self, name=None, version=None, release=None, arch=None, versions=1, repository_version=None):
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
        api_instance = pulp_rpm.ContentPackagesApi(api_client=self._rpm_api_client)
        response=pulp_rpm.PaginatedrpmPackageResponseList(next='foo')
        packages_response=list()
        packages=set()
        response = api_instance.list(limit=versions, name=name, version=version, release=release, arch=arch, repository_version=repository_version, fields='name,version,release,arch,pulp_href')
        for p in response.results:
            package = {
                "name": p.name,
                "version": p.version,
                "release": p.release,
                "arch": p.arch,
                "pulp_href": p.pulp_href
            }
            packages_response.append(package)
            print("Adding following package:")
            print(json.dumps({"name": p.name, "version": p.version, "release": p.release, "arch": p.arch}, sort_keys=False, indent=4))
            #print(json.dumps(packages_response, sort_keys=False, indent=4))
            packages.add(p.pulp_href)
        return (packages)

    def __copy(self, config=None, dependency_solving=True):
        """Copy content

        Search for modules in a specific repository_version of the whole of pulp

        :param api_client: Pulp api client to use for the connection
        :param config: copy config
        :param dependency_solving: solve dependencies
        :return: String
                 pulp_href of the generated task
        """
        api_instance = pulp_rpm.RpmCopyApi(api_client=self._rpm_api_client)
        copy = pulp_rpm.Copy(config=config, dependency_solving=dependency_solving)
        return api_instance.copy_content(copy)

    def __wait_until_task_has_finished(self, task_href=None):
        """ Wait until pulp task is finished

        Wait until pulp task is finished, if the task failed, the program will be exited

        :param api_client: Pulp api client to use for the connection
        :param task_href: The href of the pulp task
        """
        api_instance = pulpcore.TasksApi(api_client=self._pulpcore_api_client)
        task = api_instance.read(task_href)
        print(json.dumps(task.to_dict(), cls=ComplexEncoder, sort_keys=False, indent=4))
        print()
        while task.state != 'completed':
            sleep(2)
            task = api_instance.read(task_href)
            print(json.dumps(task.to_dict(), cls=ComplexEncoder, sort_keys=False, indent=4))
            print()
            if task.state == 'failed':
                sys.exit("Task failed with following error %s"%json.dumps(task.error, sort_keys=False, indent=4))

    def __copy_content(self,  content_type, copy_config):
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
        response = self.__copy(config=copy_config)

        print(Fore.BLUE + Style.BRIGHT)
        print("##################################################")
        print("Waiting until task %s has finished for %s"%(response.task,content_type))
        print("##################################################")
        print(Style.RESET_ALL)
        self.__wait_until_task_has_finished(task_href=response.task)

class ComplexEncoder(json.JSONEncoder):
    """Class used for decoding datetimes in task outputs
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)