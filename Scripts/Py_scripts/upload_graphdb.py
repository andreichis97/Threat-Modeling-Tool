import requests

readFile = open("D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\repository.txt", "r")
lines = readFile.readlines()
repositoryID = lines[0].strip()
readFile.close()

readFile = open("D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\dfd_serialization_type.txt", "r")
lines = readFile.readlines()
dfdSerializationType = lines[0].strip()
readFile.close()

readFile = open("D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\threat_serialization_type.txt", "r")
lines = readFile.readlines()
threatSerializationType = lines[0].strip()
readFile.close()

url = f"http://localhost:7200/repositories/{repositoryID}/statements"

if (dfdSerializationType == "turtle"):
    dfdFilePath = "D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\dfd_graph.ttl"
    dfd_defined_headers = {
    'Content-Type': 'application/x-turtle'
    }
else:
    dfdFilePath = "D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\dfd_graph.trig"
    dfd_defined_headers = {
    'Content-Type': 'application/x-trig'
    }

if (threatSerializationType == "turtle"):
    threatFilePath = "D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\threat_diagram_graph.ttl"
    threat_defined_headers = {
    'Content-Type': 'application/x-turtle'
    }
else:
    threatFilePath = "D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\threat_diagram_graph.trig"
    threat_defined_headers = {
    'Content-Type': 'application/x-trig'
    }

with open(dfdFilePath, 'r') as file:
    content = file.read()

# Set the headers for the request
headers = dfd_defined_headers

# Make the POST request to load the Turtle file
response = requests.post(
    url.format(repositoryID=repositoryID),
    headers=headers,
    data=content
)

# Check the response status code
print(response.status_code)
if response.status_code == 200:
    print('Turtle file loaded successfully.')
else:
    print('Error loading Turtle file:', response.text)

#-----

with open(threatFilePath, 'r') as file:
    content = file.read()

# Set the headers for the request
headers = threat_defined_headers

# Make the POST request to load the Turtle file
response = requests.post(
    url.format(repositoryID=repositoryID),
    headers=headers,
    data=content
)

# Check the response status code
print(response.status_code)
if response.status_code == 200:
    print('Turtle file loaded successfully.')
else:
    print('Error loading Turtle file:', response.text)



