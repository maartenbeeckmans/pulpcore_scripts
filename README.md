# Pulpcore scripts

This repo contains different python scripts that can be used to perform some actions to pulpcore that are not supported by the CLI.

## Cherry picking

This is currently only implemented for the rpm plugin

### Basic usage

```bash
./pulpcore_helper.py rpm cherry_pick

```

### Flags

| Flag            | Explanation                                   | Default value     |
|-----------------|-----------------------------------------------|-------------------|
| -c, --config    | Path to pulpcore_helper.py configuration file | `config.ini`      |
| -d, --data-file | Path to cherry_pick data file                 | `cherrypick.yaml` |


### Configuration options

#### Pulpcore

- *host*: hostname of the pulpcore server
- *username*: username for connecting with the pulpcore api
- *password*: password for connecting with the pulpcore api

#### Example

```ini
[pulpcore]
host = http://pulp.example.com
username = user
password = pass
```

### Cherry picking data file

```yaml
---
# Hash containing the content that has to be copied
content:
  # Content accepts a list with packages and modules
  # Example: epel packages
  - desc: epel
    # Name of the source repository
    name: mirror-el8-x86_64-epel-everything
    # List of packages that should be copied
    packages:
      # Package format accepts the following parameters:
      # - name: name of the package
      # - version: version of the package
      # - release: release of the package
      # - arch: architecture of the package
      # - versions: number of packages that should be copied
      #     default is 1, which will copy the most recent package available
      #     when 2 is specified, but only 1 package is present,
      #       it will copy that one package
      #
      # All parameters except name are optional
      #   When only a name is specified it will copy over the latest version
      #     of that package
      #
      # Examples:
      # - Version pin the htop package
      - name: htop
        version: 3.0.5
        release: 1.el8
        arch: x86_64
      # - Copy over the latest 2 versions of the ncdu package
      - name: ncdu
        versions: 2
  # Example: epel modules
  - desc: epel-modular
    # Name of the source repository
    name: mirror-el8-x86_64-epel-modular
    # List of modules that should be copied over
    modules:
      # Module format accepts the following paramters:
      # - name: name of the module
      # - stream: stream of the module
      # - versions: number of modules that should be copied
      #     default is 1, which will copy the most recent module available
      #     when 2 is specified, but only 1 module is present,
      #       it will copy that one module
      #
      # All parameters except name are optional
      #   When only a module is specified it will copy over the latest version
      #     of that module
      #
      # Examples:
      # - Version pin the cri-o module
      - name: cri-o
        stream: 1.21
      # - Copy over the latest 2 versions of the nextcloud module
      - name: nextcloud
        versions: 2
# Name of the destination repo where the packages should be added
dest_repo: upstream
...
```
