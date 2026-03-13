# flash web server - the bridge between your UI and your AI agent
# think of this as your Express/Node backen but in python 

from flask import Flask, render_template, request, Response, stream_with_context
import ollama
import json

from config import MODEL, AGENT_NAME , VERSION, SYSTEM_PROMPT, COMMANDS
from document import load_document

from flask import send_from_directory



app = Flask(__name__)


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# this stores conversion in memory 
# key is a session id, value is list of messages 
# later we will save this to files 

conversations = {}

#  Routes 

# serve the main file 
# this is like your index 
@app.route("/")
def index():
    return render_template("index.html",
    agent_name = AGENT_NAME,
    version = VERSION
    )


# chat endpoint recieves a message, streams response back 
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not message:
        return {"error": "Empty message"}, 400

    if session_id not in conversations:
        conversations[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # Find the document content from conversation history
    # We look for the message where the user loaded a document
    document_context = ""
    for msg in conversations[session_id]:
        if msg["role"] == "user" and "I am loading this financial document" in msg["content"]:
            document_context = msg["content"]
            break

    # Build a fresh message list for every request
    # This forces the document into every single AI call
    # instead of hoping the AI remembers it from history
    messages_to_send = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # If a document is loaded, inject it right after system prompt
    # This makes it impossible for the AI to ignore
    if document_context:
        messages_to_send.append({
            "role": "user",
            "content": document_context
        })
        messages_to_send.append({
            "role": "assistant", 
            "content": "I have read the document carefully. I will only use the exact figures from this document in my analysis."
        })

    # Add recent conversation history (last 6 messages only)
    # Skip the original document load messages to avoid duplication
    recent = []
    for msg in conversations[session_id]:
        if msg["role"] == "system":
            continue
        if "I am loading this financial document" in msg.get("content", ""):
            continue
        if msg.get("content", "") == "I have read the document and I am ready to answer questions about it.":
            continue
        recent.append(msg)

    # Only keep last 6 exchanges
    messages_to_send.extend(recent[-6:])

    # Add current user message
    messages_to_send.append({
        "role": "user",
        "content": f"Using ONLY the figures from the document provided above, answer this: {message}"
    })

    # Save to history
    conversations[session_id].append({
        "role": "user",
        "content": message
    })

    def generate():
        full_reply = ""

           # ADD THIS LINE
        print(f">>> Sending {len(messages_to_send)} messages to model")
        print(f">>> Document injected: {bool(document_context)}")
        print(f">>> First 100 chars of message 2: {messages_to_send[1]['content'][:100] if len(messages_to_send) > 1 else 'NONE'}")
    
        stream = ollama.chat(
            model=MODEL,
            messages=messages_to_send,
            stream=True
        )

        for chunk in stream:
            word = chunk.message.content
            full_reply += word
            yield f"data: {json.dumps({'word': word})}\n\n"

        conversations[session_id].append({
            "role": "assistant",
            "content": full_reply
        })

        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
    
# upload endpoint recieves a file, loads it, adds to the conversation
@app.route("/upload", methods=["POST"])
def upload():
    session_id =  request.form.get("session_id", "default")

    if "file" not in request.files:
        return {"error": "No file provided"}, 400

    file =  request.files["file"]
    filename =  file.filename

    # save temporarily to read it 
    temp_path = f"temp_{filename}"
    file.save(temp_path)

    # use our existing documets 
    content = load_document(temp_path)

    # clean up temp file 
    import os
    os.remove(temp_path)

    if not content:
        return {"error": "Could not read file"}, 400

    # inject document into conversation 
    if session_id not in conversations:
        conversations[session_id] = [
            {
                "role":"system", "content": SYSTEM_PROMPT
            }
        ]

       # Make sure it's actually a list before appending
    if not isinstance(conversations[session_id], list):
        conversations[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    conversations[session_id].append(
        {
            "role":"user",
            "content": f"I am loading this financial document called {filename}:\n\n {content}"
        } )

    conversations[session_id].append({
        "role":"assistant",
        "content":f"I have read {filename} and i am ready to answer questions about it."
    })

    return {"success": True, "filename":filename}

# clear conversation 
@app.route("/clear", methods=["POST"])
def clear():
    session_id =  request.json.get("session_id", "default")
    conversations[session_id] = [
        {"role":"system", "content": SYSTEM_PROMPT}
    ]
    return {"success": True}


@app.route("/debug", methods=["GET"])
def debug():
    session_id = request.args.get("session_id", "default")
    if session_id in conversations:
        # Return the full conversation so we can see what was loaded
        return {"messages": conversations[session_id]}
    return {"messages": []}

# Start server 

if  __name__ == "__main__":
    print(f"\n  {AGENT_NAME} v{VERSION}")
    print("open your browser at: http://localhost:5000\n")
    app.run(debug=True, port=5000)