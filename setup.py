import setuptools
import alphapept.__version__
from pkg_resources import parse_version
assert parse_version(setuptools.__version__) >= parse_version('36.2')

license_options = {
    'apache2': (
        'Apache Software License 2.0',
        'OSI Approved :: Apache Software License'
    ),
    'MIT': (
        'MIT License',
        'OSI Approved :: MIT License'
    )
}
status_options = {
    '1': 'Planning',
    '2': 'Pre-Alpha',
    '3': 'Alpha',
    '4': 'Beta',
    '5': 'Production/Stable',
    '6': 'Mature',
    '7': 'Inactive'
}
maximum_python3_available = 8

with open("README.md") as readme_file:
    long_description = readme_file.read()

strict_requirements = {
    "numba": "numba>=0.4.8",
    "matplotlib": "matplotlib==3.2.2",
}
with open("requirements.txt") as requirements_file:
    requirements = []
    for line in requirements_file:
        # TODO, this should be a proper regex parsing
        requirement, version = line.split("==")
        if requirement not in strict_requirements:
            requirements.append(requirement)
        else:
            requirements.append(strict_requirements[requirement])

setuptools.setup(
    name=alphapept.__version__.LIB_NAME,
    license=license_options[alphapept.__version__.LICENSE][0],
    classifiers=[
        f'Development Status :: {alphapept.__version__.STATUS} - {status_options[alphapept.__version__.STATUS]}',
        f'Intended Audience :: {alphapept.__version__.AUDIENCE}',
        f'License :: {license_options[alphapept.__version__.LICENSE][1]}',
        f'Natural Language :: {alphapept.__version__.LANGUAGE}',
    ] + [
        f'Programming Language :: Python :: 3.{i}' for i in range(
            int(alphapept.__version__.MIN_PYTHON.split(".")[1]),
            maximum_python3_available + 1
        )
    ],
    version=alphapept.__version__.VERSION_NO,
    description=alphapept.__version__.DESCRIPTION,
    keywords=alphapept.__version__.KEYWORDS,
    author=alphapept.__version__.AUTHOR,
    author_email=alphapept.__version__.AUTHOR_EMAIL,
    url=alphapept.__version__.URL,
    packages=setuptools.find_packages(),
    # TODO: Modifying this should allow to remove the MAINFEST.in
    include_package_data=True,
    install_requires=requirements,
    python_requires=f'>={alphapept.__version__.MIN_PYTHON},<{alphapept.__version__.MAX_PYTHON}',
    long_description=long_description,
    long_description_content_type='text/markdown',
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "alphapept=alphapept.__main__:main",
        ],
    },
)
