import os

def write_version_file(version):
    documents_dir = os.path.expanduser("~/Documents")
    version_file = os.path.join(documents_dir, "version.txt")
    with open(version_file, "w") as f:
        f.write(version)