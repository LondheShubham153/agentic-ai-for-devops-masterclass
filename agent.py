# LLM
import subprocess
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain.agents import create_agent

# this is coming from Ollama (ollama connect)
llm = ChatOllama(
    model="qwen3-coder:30b",
    temperature=0,
    num_ctx=8192,      # avoid truncating large kubectl/docker output
)

# TOOL
@tool
def get_pods():
    """
    Lists the pods of a running kubernetes cluster
    """
    result = subprocess.run(["kubectl", "get", "pods" ,"-A"],capture_output=True, text=True)
    return result.stdout or result.stderr


@tool
def get_docker_containers():
    """
    Lists the running docker containers
    """
    result = subprocess.run(["docker","ps"],capture_output=True, text=True)
    return result.stdout or result.stderr


# AGENT 
# LLM + TOOLS

agent = create_agent(
    model=llm, 
    tools=[get_pods,get_docker_containers],
    system_prompt=(
        "You are a DevOps assistant that inspects live Kubernetes clusters and Docker "
        "environments using tools.\n"
        "Tools:\n"
        "- get_pods: lists all pods in all namespaces (kubectl get pods -A). Use it for any "
        "question about pods, namespaces, pod status, or restarts.\n"
        "- get_docker_containers: lists running containers (docker ps). Use it for any "
        "question about local containers, images, ports, or container status.\n"
        "Rules:\n"
        "- When a question needs live state, ALWAYS call the relevant tool. Never invent pod "
        "or container names.\n"
        "- Answer only from tool output. If a tool returns nothing or an error, say so and "
        "give the likely cause (cluster unreachable, Docker not running, or no resources).\n"
        "- Call out problem states (CrashLoopBackOff, Error, high restarts, Exited) and keep "
        "the rest concise. Use a short table or list when it helps.\n"
        "- If the question isn't about Kubernetes or Docker, answer briefly and note no tool "
        "was needed."
    )
    )

question = input("Ask your Kubernetes Agent a Question: >") # user input

response = agent.invoke({"messages": [("user",question)]})

print(response["messages"][-1].content)