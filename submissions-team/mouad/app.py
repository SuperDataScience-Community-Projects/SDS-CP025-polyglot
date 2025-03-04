import gradio as gr

def respond(message, history):
    return "Hello! I’m Polyglot, your language tutor. Ready to learn?"

interface = gr.ChatInterface(fn=respond, title="Polyglot")
interface.launch()