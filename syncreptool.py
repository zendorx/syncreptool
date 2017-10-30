import json
import os
from sys import platform
import collections
from colorama import init
init()
from colorama import Fore, Back, Style
import sys


current_dir = os.getcwd()
current_config = "config.txt"
protocol = ""
action = "none"

template = collections.OrderedDict()
template["hg"] = collections.OrderedDict()
template["git"] = collections.OrderedDict()
template["hg"]["https"] = "https://bitbucket.org/{name}"
template["git"]["https"] = "https://github.com/{name}"
template["git"]["ssh"] = "git@github.com:{name}.git"
template["hg"]["ssh"] = "ssh://hg@bitbucket.org/{name}"


def get_env(name):
    if platform == "darwin":
        return os.popen("echo $" + name).read().replace('\n', '').replace('\r', '')
    else:
        return os.popen("echo %" + name + "%").read().replace('\n', '').replace('\r', '')

class Repository:
    def __init__(self, data):
        self.name = data["name"]
        self.type = data["type"]
        self.path = data["path"]
        self.commit = data["commit"]
        self.local = False
        self.local_path = ""
        self.local_env = ""
        self.manual = False

        if "manual" in data:
            self.manual = data["manual"]

        if "local" in data:
            self.local = True
            self.local_env = data["local"].replace('%','')
            p = get_env(self.local_env)
            self.local_path = get_env(self.local_env)


    def get_full_url(self):
        if self.local:
            return self.local_path

        global template
        global protocol
        if protocol == "":
            protocol = raw_input(Fore.MAGENTA + "Enter protocol(https,ssh):" + Fore.GREEN).replace('\n','').replace('\r','')
            if protocol == "":
                protocol = "https"

        return template[self.type][protocol].replace("{name}", self.name)



class Config:
    def __init__(self, fname):
        self.reps = []
        self.ndk = ""
        with open(fname) as config_file:
            data = json.load(config_file)
            for r in data["reps"]:
                self.reps.append(Repository(r))
            self.ndk = data["ndk"]

    def save(self, fname):
        data = {}
        data["ndk"] = self.ndk
        data["reps"] = []
        for r in self.reps:
            rep = {}
            rep["name"] = r.name
            rep["type"] = r.type
            rep["path"] = r.path
            rep["commit"] = r.commit

            if r.manual:
                rep["manual"] = True

            if r.local_env:
                rep["local"] = '%' + r.local_env + '%'

            data["reps"].append(rep)

        with open(fname, 'w') as config_file:
            config_file.write(json.dumps(data, indent=4))

    def check_ndk(self):
        cndk = self.read_ndk()
        if self.ndk != cndk:
            print "\n" + Fore.YELLOW + "Warrning! DIFFERENT NDK" + Style.RESET_ALL
            print "Current NDK: " + Fore.RED + cndk + Style.RESET_ALL
            print "Need NDK: " + Fore.MAGENTA + self.ndk + Style.RESET_ALL
        else:
            print "NDK: " + Fore.BLUE + "Ok!" + Style.RESET_ALL

    def save_ndk(self):
        cndk = self.read_ndk()
        if self.ndk != cndk:
            self.ndk = cndk
            print "ndk: " + self.ndk + ": " + Fore.MAGENTA + "Updated!" + Style.RESET_ALL
        else:
            print "ndk: " + self.ndk + ": " + Fore.BLUE + "Not Changed." + Style.RESET_ALL

    def read_ndk(self):
        path = get_env("NDK_ROOT")
        return os.path.basename(path)

def fetch_rep_ask(repositiory):
    pass




def get_rep_hash(repository):
    cwd = os.getcwd()
    result = ""
    if repository.type == "hg":
        os.chdir(repository.path)
        result = os.popen("hg parent --template {node}").read()
        os.chdir(cwd)

    if repository.type == "git":
        os.chdir(repository.path)
        result = os.popen("git rev-parse HEAD").read()
        os.chdir(cwd)

    if not result:
        print repository.path + ": " + Fore.RED + " Unknown type!" + Style.RESET_ALL
    return result.replace('\n', '').replace('\r','')


def update_to_commit(repository, commit):
    cwd = os.getcwd()

    if repository.type == "git":
        os.chdir(repository.path)
        command = "git pull"
        os.system(command)
        command = "git reset --keep " + commit
        os.system(command)
        os.chdir(cwd)

    if repository.type == "hg":
        os.chdir(repository.path)
        command = "hg pull"
        os.system(command)
        command = "hg update -c " + commit
        os.system(command)
        os.chdir(cwd)

    current_commit = get_rep_hash(repository)
    if commit != current_commit:
        print repository.path + ": " + Fore.RED + "NOT UPDATED!" + Style.RESET_ALL
    else:
        repository.commit = commit
        print repository.path + ": " + Fore.GREEN + "Done!" + Style.RESET_ALL


def clone_rep(repository):
    cwd = os.getcwd()
    print Fore.CYAN + repository.path + Fore.YELLOW + ": not exists. Cloning.." + Style.RESET_ALL
    url = repository.get_full_url()

    if repository.type == "git":
        command = "git clone " + url + " " + repository.path
        os.system(command)
        return

    if repository.type == "hg":
        os.mkdir(repository.path)
        os.chdir(repository.path + "/..")
        command = "hg clone " + url
        os.system(command)
        os.chdir(cwd)
        return

    print repository.path + ": " + Fore.RED + " Cloning failed!" + Style.RESET_ALL
    return



def update_rep(repository):
    pass

def sync_reps(config):
    for r in config.reps:
        if not os.path.exists(r.path):
            print "Repository not exists: ", r.name, " - ", r.type, Style.RESET_ALL
            clone_rep(r)
        else:
            curhash = get_rep_hash(r)

        print Style.RESET_ALL
        if curhash:
            if curhash == r.commit:
                print r.name + ": " + Fore.BLUE + "No changes. " + Style.RESET_ALL
            else:
                if r.manual:
                    print r.name + ": " + Fore.YELLOW + "DIFFERENT. (repository is manual)" + Style.RESET_ALL
                else:
                    print r.name + ": " + Fore.CYAN + "Updating..." + Style.RESET_ALL
                    update_to_commit(r, r.commit)



def save_reps(config):
    for r in config.reps:
        if not os.path.exists(r.path):
            print "Repository not exists: ", r.path, " - ", r.type, Style.RESET_ALL
            clone_rep(r)

        if not os.path.exists(r.path):
            print r.name + ": " + Fore.RED + "Still not exists. Skipping..." + Style.RESET_ALL
            continue

        curhash = get_rep_hash(r)
        if not curhash:
            print r.name + ": " + Fore.RED + "Can't get commit hash. Skipping..."
            continue

        if r.commit == curhash:
            print r.name + ": " + Fore.BLUE + "No changes. " + Style.RESET_ALL
        else:
            if r.manual:
                print r.name + ": " + Fore.YELLOW + "DIFFERENT. (repository is manual)" + Style.RESET_ALL
            else:
                r.commit = curhash
                print r.name + ": " + Fore.MAGENTA + "Changed." + Style.RESET_ALL

action = "sync"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]

    if action == "none":
        action = raw_input('Enter action(sync, save, init, update, ndk): ')

    if action == "sync":
        config = Config(current_config)
        sync_reps(config)
        config.check_ndk()

    if action == "save":
        config = Config(current_config)
        save_reps(config)
        config.save(current_config)

    if action == "ndk":
        config = Config(current_config)
        config.save_ndk()
        config.save(current_config)

    if action == "update":
        print "not implemented"

    if action == "init":
        print "not implemented"






