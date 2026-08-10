from flask import Flask, request, redirect, jsonify
import yt_dlp
import json
import re

app = Flask(__name__)

# yt-dlp options
def get_ydl_opts(quality='high'):
    """Return yt-dlp options based on quality"""
    quality_map = {
        'low': 'worstvideo[ext=mp4]',
        'medium': 'bestvideo[height<=480][ext=mp4]',
        'high': 'bestvideo[ext=mp4]'
    }
    format_filter = quality_map.get(quality, 'bestvideo[ext=mp4]')
    
    return {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'format': format_filter,
        'cookiefile': None  # no cookies needed
    }

def extract_media(url, quality='high'):
    """Extract media URL and metadata from Instagram URL"""
    ydl_opts = get_ydl_opts(quality)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return {'error': 'No data found'}
            
            # if it's a playlist/carousel
            if 'entries' in info and info['entries']:
                entries = info['entries']
                media_list = []
                
                for entry in entries:
                    if not entry:
                        continue
                    
                    # get video/photo URL
                    media_url = None
                    if 'url' in entry:
                        media_url = entry['url']
                    elif 'formats' in entry and entry['formats']:
                        # pick best quality
                        for f in entry['formats']:
                            if f.get('url') and 'video' in f.get('format_note', '').lower():
                                media_url = f['url']
                                break
                        if not media_url and entry['formats']:
                            media_url = entry['formats'][-1].get('url')
                    elif 'thumbnails' in entry and entry['thumbnails']:
                        # it's a photo
                        media_url = entry['thumbnails'][-1].get('url')
                    
                    if media_url:
                        media_list.append({
                            'url': media_url,
                            'type': 'video' if 'video' in str(entry.get('format_note', '')) else 'image',
                            'thumbnail': entry.get('thumbnail'),
                            'duration': entry.get('duration')
                        })
                
                # extract metadata from first entry
                first = entries[0] if entries else {}
                return {
                    'success': True,
                    'type': 'carousel',
                    'media_count': len(media_list),
                    'media': media_list,
                    'username': info.get('uploader') or first.get('uploader') or info.get('channel'),
                    'caption': info.get('description') or first.get('description') or info.get('title') or '',
                    'thumbnail': info.get('thumbnail') or first.get('thumbnail')
                }
            
            # single video/post
            media_url = None
            if 'url' in info:
                media_url = info['url']
            elif 'formats' in info and info['formats']:
                for f in info['formats']:
                    if f.get('url') and 'video' in f.get('format_note', '').lower():
                        media_url = f['url']
                        break
                if not media_url and info['formats']:
                    media_url = info['formats'][-1].get('url')
            
            if not media_url:
                return {'error': 'No media URL found'}
            
            return {
                'success': True,
                'type': 'single',
                'media': [{
                    'url': media_url,
                    'type': 'video',
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration')
                }],
                'username': info.get('uploader') or info.get('channel'),
                'caption': info.get('description') or info.get('title') or '',
                'thumbnail': info.get('thumbnail')
            }
            
    except Exception as e:
        return {'error': str(e)}

@app.route('/api/download')
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', 'high')  # low, medium, high
    format_type = request.args.get('format', 'json')  # json or redirect
    
    if not url:
        return jsonify({'error': 'url parameter required'}), 400
    
    if 'instagram.com' not in url:
        return jsonify({'error': 'only instagram urls supported'}), 400
    
    result = extract_media(url, quality)
    
    if result.get('error'):
        return jsonify({'error': result['error']}), 500
    
    # if user wants redirect (only works for single media)
    if format_type == 'redirect' and result.get('media') and len(result['media']) == 1:
        return redirect(result['media'][0]['url'])
    
    # if carousel and redirect requested, redirect to first media
    if format_type == 'redirect' and result.get('media') and len(result['media']) > 1:
        return redirect(result['media'][0]['url'])
    
    # return JSON with all data
    return jsonify(result)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'instagram downloader'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
