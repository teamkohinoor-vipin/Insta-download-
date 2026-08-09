from flask import Flask, request, redirect, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/api/download')
def download():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'url parameter required'}), 400
    
    if 'instagram.com' not in url:
        return jsonify({'error': 'only instagram urls supported'}), 400
    
    try:
        # video url fetch karo
        result = subprocess.run(
            ['yt-dlp', '-g', url],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode != 0:
            return jsonify({'error': 'failed to fetch video'}), 500
        
        video_url = result.stdout.strip().split('\n')[0]
        
        # agar redirect chahiye toh
        if request.args.get('redirect') == 'true':
            return redirect(video_url)
        
        # warna json return karo
        return jsonify({
            'success': True,
            'video_url': video_url
        })
        
    except:
        return jsonify({'error': 'something went wrong'}), 500

if __name__ == '__main__':
    app.run(debug=True)
