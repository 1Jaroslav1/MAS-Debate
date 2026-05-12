from langgraph.types import Command, interrupt

def human_argument():
    argument = interrupt("Please enter your argument: ")
    return argument
