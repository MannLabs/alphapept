from pkg_resources import parse_version
from configparser import ConfigParser
import setuptools
assert parse_version(setuptools.__version__)>=parse_version('36.2')
import os
import re
import alphapept as package2install

# note: all settings are in settings.ini; edit there, not here
config = ConfigParser(delimiters=['='])
config.read('settings.ini')
cfg = config['DEFAULT']

cfg_keys = 'version description keywords author author_email'.split()
expected = cfg_keys + "lib_name user branch license status min_python audience language".split()
for o in expected: assert o in cfg, "missing expected setting: {}".format(o)
setup_cfg = {o:cfg[o] for o in cfg_keys}

licenses = {
    'apache2': ('Apache Software License 2.0','OSI Approved :: Apache Software License'),
    'mit': ('MIT License', 'OSI Approved :: MIT License'),
    'gpl2': ('GNU General Public License v2', 'OSI Approved :: GNU General Public License v2 (GPLv2)'),
    'gpl3': ('GNU General Public License v3', 'OSI Approved :: GNU General Public License v3 (GPLv3)'),
    'bsd3': ('BSD License', 'OSI Approved :: BSD License'),
}
statuses = [ '1 - Planning', '2 - Pre-Alpha', '3 - Alpha',
    '4 - Beta', '5 - Production/Stable', '6 - Mature', '7 - Inactive' ]
py_versions = '3.6 3.7 3.8 3.9 3.10'.split()

if cfg.get('pip_requirements'): requirements += cfg.get('pip_requirements','').split()
min_python = cfg['min_python']
lic = licenses.get(cfg['license'].lower(), (cfg['license'], None))

extra_requirements = {}
for extra, requirement_file_name in package2install.__requirements__.items():
    with open(requirement_file_name) as requirements_file:
        if extra != "":
            extra_stable = f"{extra}-stable"
        else:
            extra_stable = "stable"
        extra_requirements[extra_stable] = []
        extra_requirements[extra] = []
        for line in requirements_file:
            extra_requirements[extra_stable].append(line)
            requirement, *comparison = re.split("[><=~!]", line)
            requirement == requirement.strip()
            extra_requirements[extra].append(requirement)

requirements = extra_requirements.pop("")

setuptools.setup(
    name = cfg['lib_name'],
    license = lic[0],
    classifiers = [
        'Development Status :: ' + statuses[int(cfg['status'])],
        'Intended Audience :: ' + cfg['audience'].title(),
        'Natural Language :: ' + cfg['language'].title(),
    ] + ['Programming Language :: Python :: '+o for o in py_versions[py_versions.index(min_python):]] + (['License :: ' + lic[1] ] if lic[1] else []),
    url = cfg['git_url'],
    packages = setuptools.find_packages(),
    include_package_data = True,
    install_requires=requirements + [
        "pywin32==225; sys_platform=='win32'",
        "pythonnet==2.5.2; sys_platform=='win32'",
        "tables==3.6.1; sys_platform=='win32'"
    ],
    extras_require=extra_requirements,
    dependency_links = cfg.get('dep_links','').split(),
    python_requires  = '>=' + cfg['min_python'],
    long_description = open('README.md').read(),
    long_description_content_type = 'text/markdown',
    zip_safe = False,
    entry_points = {
        'console_scripts': cfg.get('console_scripts','').split(),
        'nbdev': [f'{cfg.get("lib_path")}={cfg.get("lib_path")}._modidx:d']
    },
    **setup_cfg)
