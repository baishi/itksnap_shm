import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="itksnap_shm-baishi", # Replace with your own username
    version="0.2.2",
    author="Shi Bai",
    author_email="shi.bai@monash.edu",
    description="A convenient library to work with ITK-SNAP shared memory interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/baishi/itksnap_shm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
)
