import requests

read_file = open("D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Results\\repository.txt", "r")
lines = read_file.readlines()
repository_id = lines[0].strip()
read_file.close()

url = f"http://localhost:7200/repositories/{repository_id}/statements"

ontology_file_path = "D:\\Andrei\\ModellingTools\\Threat_Modeling_Tool\\Scripts\\Docs\\ontology.trig"
ontology_headers = {
    'Content-Type': 'application/x-trig'
}

with open(ontology_file_path, 'r') as file:
    content = file.read()

# Set the headers for the request
headers = ontology_headers

# Make the POST request to load the Turtle file
response = requests.post(
    url.format(repository_id=repository_id),
    headers=headers,
    data=content
)

# Check the response status code
print(response.status_code)
if response.status_code == 200 or response.status_code == 204:
    print('File loaded successfully.')
else:
    print('Error loading file:', response.text)