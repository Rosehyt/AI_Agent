import urllib.request
import zipfile
import io
import os
import shutil

url = 'https://github.com/jason79461385/Assignment-3/archive/refs/heads/main.zip'
print('Downloading Assignment 3 repository...')
response = urllib.request.urlopen(url)
with zipfile.ZipFile(io.BytesIO(response.read())) as z:
    z.extractall()

# Rename the extracted folder 'Assignment-3-main' to 'repo'
if os.path.exists('Assignment-3-main'):
    if os.path.exists('repo'):
        shutil.rmtree('repo')
    os.rename('Assignment-3-main', 'repo')
    print('Successfully downloaded and extracted to repo/')
else:
    print('Error: Could not find extracted folder.')
