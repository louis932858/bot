from flask import Flask

app = Flask(__name__)

HTML = """
<h1>💎 NEXORA DASHBOARD</h1>
<p>Bot Status: <b>ONLINE</b></p>

<hr>

<h3>⚙️ System</h3>
<ul>
<li>Auto Moderation: ON</li>
<li>Anti Spam: ON</li>
<li>Voice Kick: ON</li>
</ul>

<p>Railway Deployment Active 🚀</p>
"""

@app.route("/")
def home():
    return HTML


def run():
    app.run(host="0.0.0.0", port=8080)
