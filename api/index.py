from flask import Flask, request, redirect, jsonify
import yt_dlp
import json

app = Flask(__name__)

# root route — check karo API chal raha hai
@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Instagram downloader API is running',
        'endpoints': {
            '/api/download': '?url=INSTAGRAM_URL',
            '/api/health': 'health check'
        }
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'instagram downloader'})

@app.route('/api/download')
def download():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'url parameter required'}), 400
    
    if 'instagram.com' not in url:
        return jsonify({'error': 'only instagram urls supported'}), 400
    
    try:
        # yt-dlp options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'no data found'}), 500
            
            # extract video url
            video_url = None
            if 'url' in info:
                video_url = info['url']
            elif 'formats' in info and info['formats']:
                for f in info['formats']:
                    if f.get('url') and 'video' in f.get('format_note', '').lower():
                        video_url = f['url']
                        break
                if not video_url and info['formats']:
                    video_url = info['formats'][-1].get('url')
            
            # check if carousel
            if 'entries' in info and info['entries']:
                first_entry = info['entries'][0]
                if first_entry and 'url' in first_entry:
                    video_url = first_entry['url']
            
            if not video_url:
                return jsonify({'error': 'video url not found'}), 500
            
            # redirect mode
            if request.args.get('redirect') == 'true':
                return redirect(video_url)
            
            return jsonify({
                'success': True,
                'video_url': video_url,
                'username': info.get('uploader'),
                'caption': (info.get('description') or '')[:200],
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration')
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
