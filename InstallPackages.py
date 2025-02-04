#!/usr/bin/env python
import yaml
import subprocess
import sys

def install_conda_package(package, channels):
    """
    Installs a conda package with auto-confirmation (-y) using the specified channels.
    """
    cmd = ["conda", "install", "-y"] + channels + [package]
    print("Installing conda package: {}".format(package))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print("Error installing {}: {}".format(package, e))

def install_pip_package(package):
    """
    Installs a pip package.
    """
    cmd = ["pip", "install", package]
    print("Installing pip package: {}".format(package))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print("Error installing {}: {}".format(package, e))

def main(yaml_file):
    # Define channels to use for conda installs. Order matters.
    channels = ["-c", "anaconda", "-c", "default", "-c", "conda-forge"]

    # Load the environment YAML.
    with open(yaml_file, "r") as f:
        env_data = yaml.safe_load(f)

    if "dependencies" not in env_data:
        print("The YAML file does not contain a 'dependencies' section.")
        sys.exit(1)

    conda_packages = []
    pip_packages = []

    # Parse the dependencies.
    for dep in env_data["dependencies"]:
        # In Python 2.7, use basestring to catch both str and unicode.
        if isinstance(dep, basestring):
            conda_packages.append(dep)
        elif isinstance(dep, dict):
            for key, value in dep.items():
                if key == "pip":
                    # Assume value is a list of pip packages.
                    pip_packages.extend(value)
                else:
                    print("Encountered an unrecognized dependency section: {}".format(key))

    # Install conda packages one by one.
    for pkg in conda_packages:
        install_conda_package(pkg, channels)

    # Then install pip packages.
    if pip_packages:
        print("Installing pip packages:")
        for pkg in pip_packages:
            install_pip_package(pkg)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} environment.yaml".format(sys.argv[0]))
        sys.exit(1)
    main(sys.argv[1])
