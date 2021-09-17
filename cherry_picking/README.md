# Cherry picking

Script is used to perform some rpm copy operations between different pulp repositories.

2 configuration files are required.

- config.yaml: contains information for connection to pulp.
- cherrypicking.yaml: contains cherry picking configuration

This scripts supports copying rpm packages and dnf modules.

Packages have the following parameters: `name`, `version`, `release` and `arch`. If all paramters are defined, it will copy packages with that specific version, release and arch from the source repo. If only name is added, it will copy all packages with that name (multiple versions).

Modules have the following parameters: `name` and `stream`. If only name is provided, all modules with that name will be copied over.

It is not possible to delete old versions of packages with this script, you should use the `retain_package_versions` option in the repository for deleting old packages.
