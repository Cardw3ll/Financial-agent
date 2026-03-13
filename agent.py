import ollama
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory


#import from own files

from config import MODEL, AGENT_NAME , VERSION, SYSTEM_PROMPT, COMMANDS
from document import load_document

#create a console object - this is our rich printer
console = Console()
history = InMemoryHistory()

# this is our first function it sends a message to the AI and gets a response

#this is the agent personality and job discription
# this is the first thing sent to the AI on every conversation 
# try editing this text to how the Agent behaviours 



# now lets add a function to read file 


def ask_agent(messages):
  
    """Send conversation to AI and stream the response word by word."""
    stream = ollama.chat(
        model=MODEL,
        messages=messages,
        stream=True
    )

    full_reply = ""

    console.print("\n[green]{AGENT_NAME} >[/green]")

    # each chunk is small piece of the response 

    for chunk in stream:
        word = chunk.message.content
        full_reply += word

        # end=="" means don't ass a new line after each word 
        # flush=True measn print immediately 
        print(word, end="", flush=True)


    print("\n")

    return full_reply

    # return response.message.content

#this runs when you excute the file remember this wa a test to see if it will respond
# if __name__ == "__main__":
#     console.print(Panel("finance Agent v0.1", style="green"))

#     answer = ask_agent("What is a profit and loss statement?")
#     console.print(answer)

# now we are making it to be interactive
def show_help():
    """Print available commands"""
    console.print("\n[cyan]Available commands:[/cyan]")
    for command, description in COMMANDS.items():
        console.print(f" [yellow]{command}[/yellow] - {description}")
    console.print()



def main():
    console.print(Panel(f"{AGENT_NAME} v{VERSION}", style = "green"))
    console.print("[dim]Type your question, press Ctrl+C to exit.[/dim]\n")

    # this list stores the full conversation 
    # so the AI remmbers what was said before 
    conversation = [
        {
            "role":"system",
            "content": SYSTEM_PROMPT
        }
    ]

    while True:
        # get input from users 
        user_input = prompt("You > ", history=history).strip()

        # skip empty inputs 
        if not user_input:
            continue

        #handle help commands
        if user_input == "/help":
            show_help()
            continue

            # handle load command 
        
        if user_input.startswith("/load"):
            # split input to get file name 
            parts = user_input.split(" ", 1)

            if len(parts) < 2:
                console.print("[red] /load file name.pdf[/red]")
                continue

            filepath= parts[1].strip()
            content = load_documents(filepath)


            if content:
                # inject teh document into conversation as contect 
                # we will tell the AI here is the document, remember it 
                conversation.append({
                    "role":"user",
                    "content": f"I am loading this financial document for you yo analyse: \n\n{content}"
                })
                conversation.append({
                    "role":"assistant",
                    "content": "I have read the document and i am ready to answer questions about it"
                })
                console.print("[cyan]Document loaded. You can now ask questions about it[/cyan]")
            continue

        # handle the /clear command 
        if user_input == "/clear":
            # reset conversation 
            conversation = [conversation[0]]
            console.print("[cyan]Conversation cleared[/cyan]")
            continue

        # add user message to the conversation
        conversation.append({
            "role":"user",
            "content": user_input
        })

        # show thinking indication 
        # console.print("[cyan]Thinking...[/cyan]")

        #send full conversation to AI
        reply = ask_agent(conversation)

        # add AI reply conversation history
        conversation.append({
            "role":"assistant",
            "content": reply
        })


        #print the response
        # console.print("\n[green]Agent > [/green]")
        # console.print(Markdown(reply))
        # console.print()


if __name__ == "__main__":
    try:
        main()
    
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")