import subprocess
import sys

def read_file():
    readFile = open("D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Results//llm_query.txt", "r")
    fileContent = readFile.readlines()
    mode = fileContent[4].strip()
    readFile.close()

    return mode

def main():
    mode = read_file()
    if mode.lower() in ["1", "1 hop", "1 Hop", "1 Hops"]:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_query_graph_1hops_exceptions.py"], check=True)
    elif mode.lower() in ["2", "2 hop", "2 Hop", "2 Hops"]:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_query_graph_2hops_exceptions.py"], check=True)
    elif mode.lower() in ["3", "3 hop", "3 Hop", "3 Hops"]:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_query_graph_3hops_exceptions.py"], check=True)
    elif mode.lower() in ["4", "4 hop", "4 Hop", "4 Hops"]:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_query_graph_4hops_exceptions.py"], check=True)
    elif mode.lower() in ["dynamic", "dynamic hop", "dynamic hops"]:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_query_graph_dynamic_hops_exceptions.py"], check=True)
    elif mode.lower() in ["ontology", "ontology traversal", "traversal"]:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_ontology_traversal_v3.py"], check=True)
    else:
        subprocess.run([sys.executable, "D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Py_scripts//flow_query_graph_dynamic_hops_exceptions.py"], check=True)
if __name__ == "__main__":
    main()