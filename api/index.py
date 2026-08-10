from flask import Flask, request, redirect, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return 'Instagram Downloader API is running!'

@app.route('/api/download')
def download():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'url parameter required'}), 400
    
    if 'instagram.com' not in url:
        return jsonify({'error': 'only instagram urls supported'}), 400
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_url = None
            if 'url' in info:
                video_url = info['url']
            elif 'formats' in info and info['formats']:
                for f in info['formats']:
                    if f.get('url'):
                        video_url = f['url']
                        break
            elif 'entries' in info and info['entries']:
                first = info['entries'][0]
                if first and 'url' in first:
                    video_url = first['url']
            
            if not video_url:
                return jsonify({'error': 'video url not found'}), 500
            
            if request.args.get('redirect') == 'true':
                return redirect(video_url)
            
            return jsonify({
                'success': True,
                'video_url': video_url,
                'username': info.get('uploader', 'unknown'),
                'caption': (info.get('description') or '')[:200]
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
