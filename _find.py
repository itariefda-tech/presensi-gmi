data=open('app.py','r',encoding='utf-8',errors='ignore').read();print([i for i,l in enumerate(data.splitlines()) if '_list_policies' in l][:10]) 
