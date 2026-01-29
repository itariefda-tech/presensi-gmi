import os,urllib.request,subprocess  
url = 'https://github.com/git-for-windows/git/releases/download/v2.52.0.windows.1/Git-2.52.0-64-bit.exe'  
out = os.path.join(os.getcwd(),'git-setup.exe')  
urllib.request.urlretrieve(url,out)  
subprocess.run([out,'/VERYSILENT','/NORESTART'], check=True)  
