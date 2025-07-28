from flask import Flask, request, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "upload.pdf")
        file.save(pdf_path)

        try:
            result = subprocess.run(
                ["pdfimages", "-list", pdf_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split("\n")
            image_lines = [l for l in lines if l.strip().startswith(tuple("0123456789"))]
            image_count = len(image_lines)

            max_dpi = 0
            for line in image_lines:
                parts = line.strip().split()
                if len(parts) >= 6:
                    try:
                        xdpi = int(parts[4])
                        ydpi = int(parts[5])
                        dpi = (xdpi + ydpi) // 2
                        if dpi > max_dpi:
                            max_dpi = dpi
                    except:
                        continue

            art_type = "Raster" if image_count > 0 and max_dpi > 100 else "Vector"

            return jsonify({
                "image_count": image_count,
                "max_dpi": max_dpi,
                "art_type": art_type
            })

        except subprocess.CalledProcessError as e:
            return jsonify({"error": e.stderr}), 500

@app.route("/")
def health():
    return "PDF Analyzer running", 200
