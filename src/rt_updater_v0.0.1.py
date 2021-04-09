#!/usr/bin/python3
#
# Copyright 2021 Jesse Cox
#
# title: rt_updater.py
#
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software 
# is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import json
import sys
import time
from time import localtime, strftime

my_config = {
    'github_user': '',
    'github_repository': '',
    'github_password': '',
    'secure': 'false',
    'current_version': '',
    'last_updated': ''
}

# get the current config and version
with open('/etc/rt_updater/config.json') as f_config:
    config_data = json.load(f_config)
    my_config['github_user'] = config_data["github_user"]
    my_config['github_repository'] = config_data["github_repository"]
    my_config['github_password'] = config_data["github_password"]
    my_config['secure'] = config_data["secure"]
    my_config['current_version'] = config_data["current_version"]
    print(my_config)

current_version = my_config['current_version']
git_user = my_config['github_user']
git_repo = my_config['github_repository']

# first curl the file to get the latest release
os.system("rm /etc/rt_updater/git_release.json")
if (os.system("curl --insecure -o /etc/rt_updater/git_release.json https://api.github.com/repos/" + my_config['github_user'] + "/" + my_config['github_repository'] + "/releases/latest") !- 0):
    print("error downloadnig git log ... exiting")
else:  # now compare the file to the existing version
    with open('/etc/rt_updater/git_release.json') as f_gitinfo:
        git_data = json.load(f_gitinfo)
        target_version = git_data["tag_name"]

# get the current time
mytime = strftime("%a, %d %b %Y %H:%M:%S %Z", localtime())

# open and write the log file
f_log = open("/etc/rt_updater/rt_updater.log", "a+")
f_log.write("runtime version check started at %s\r\n" % mytime)
f_log.write("local version is %s\r\n" % current_version)
f_log.write("latest version is %s\r\n" % target_version)
f_log.close()

# check the release
if current_version != target_version:
    git_url = ("https://github.com/" + git_user + "/" + git_repo +
               "/releases/download/" + target_version + "/firmware_backup_codesys.tgz")
    print("downloading new project from account: " + git_user +
          " fromo repo: " + git_repo + " verion: " + target_version)

    # # get the new release from git
    if (os.system("wget -q -O /tmp/home.tgz " + git_url) != 0):
        print("error downloading the latest program ... exiting")
        exit()
    else:
        # # # stop the runtime
        os.chdir("/etc/init.d")
        if (os.system("./codesyscontrol stop") != 0):
            print("error stopping runtime ... exiting")
            exit()
        else:
            # # # backup the exiisting project
            backup_version = ("rt_backup_v" + current_version + ".tgz")
            os.chdir("/var/opt")
            if (os.system("tar -czf /etc/rt_updater/%s codesys" % backup_version) != 0):
                print("error backing up exisitng runtime project ... exiting")
                exit()
            else:
                os.system("rm -r codesys")

                # # # unpackage the update package to /home
                if (os.system("tar -xzf /tmp/home.tgz -C .") != 0):
                    print("error extracting the runtime directories ... exiting")
                    exit()
                else:
                    # # # start the runtime
                    os.chdir("/etc/init.d")
                    if (os.system("./codesyscontrol start") != 0):
                        print("error restarting the runtime ... exiting")
                        exit()
                    else:
                        os.system("rm /tmp/home.tgz")
                        print("Project Update is Complete to version " +
                              target_version)
                        f_log = open("/etc/rt_updater/rt_updater.log", "a+")
                        f_log.write(
                            "successfully updated project version to %s\r\n" % target_version)
                        f_log.close()
                        my_config['current_version'] = target_version
                        my_config['last_updated'] = mytime
                        with open('/etc/rt_updater/config.json', 'w') as config_file:
                            json.dump(my_config, config_file,
                                      sort_keys=True, indent=4)
else:  # no updates required
    print("Project is already up to date")
    f_log = open("/etc/rt_updater/rt_updater.log", "a+")
    f_log.write(
        "update not required, current version is lattest %s\r\n" % target_version)
    f_log.close()
