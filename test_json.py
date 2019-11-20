import json,urllib.request
url = 'http://127.0.0.1:8080/circles/api/v1.0/users/202'
data = urllib.request.urlopen(url).read()
output = json.loads(data.decode('utf-8'))
print(output)
