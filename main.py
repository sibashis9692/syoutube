from flask import Flask, request, render_template, session, send_file, redirect
from pytube import YouTube, Playlist
from io import BytesIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "654c0fb3968af9d5e6a9b3edcbc7051b"

# Temporary download folder for Vercel
DOWNLOAD_FOLDER = "/tmp"

# Helper: convert file size in bytes to MB/GB
def convert_size(size_in_bytes):
    if not size_in_bytes:
        return "0 MB"
    size_units = ["bytes", "KB", "MB", "GB"]
    size = size_in_bytes
    unit_index = 0
    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {size_units[unit_index]}"

@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        if request.method == 'POST':
            url_link = request.form.get('inputbox')
            session['link'] = url_link
            yt = YouTube(url_link)
            
            # Gather streams info
            streams_info = []
            for stream in yt.streams.filter(progressive=True).order_by('resolution').desc():
                streams_info.append({
                    'itag': stream.itag,
                    'resolution': stream.resolution,
                    'filesize': convert_size(stream.filesize)
                })
            
            # Audio-only stream info
            audio_stream = yt.streams.filter(only_audio=True).first()
            audio_info = {
                'itag': audio_stream.itag,
                'filesize': convert_size(audio_stream.filesize)
            }

            return render_template("download.html", yt=yt, streams=streams_info, audio=audio_info)
        return render_template("index.html")
    except Exception as e:
        return f"Error: {e}"

@app.route('/download/<int:itag>/<string:audio>', methods=['POST', 'GET'])
def download(itag, audio):
    try:
        yt = YouTube(session['link'])
        if audio == "true":
            stream = yt.streams.get_audio_only()
            file_ext = "mp3"
        else:
            stream = yt.streams.get_by_itag(itag)
            file_ext = stream.subtype

        # Download to /tmp
        out_path = os.path.join(DOWNLOAD_FOLDER, f"{yt.title}.{file_ext}")
        stream.download(output_path=DOWNLOAD_FOLDER, filename=f"{yt.title}.{file_ext}")

        return send_file(out_path, as_attachment=True, download_name=f"{yt.title}.{file_ext}")
    except Exception as e:
        return f"Error: {e}"

@app.route('/playlist', methods=['GET', 'POST'])
def playlist():
    try:
        if request.method == 'POST':
            url_link = request.form.get('inputbox')
            session['link'] = url_link
            pl = Playlist(url_link)

            videos = []
            for video_url in pl.video_urls:
                yt = YouTube(video_url)
                streams_info = []
                for stream in yt.streams.filter(progressive=True).order_by('resolution').desc():
                    streams_info.append({
                        'itag': stream.itag,
                        'resolution': stream.resolution,
                        'filesize': convert_size(stream.filesize)
                    })
                audio_stream = yt.streams.filter(only_audio=True).first()
                audio_info = {
                    'itag': audio_stream.itag,
                    'filesize': convert_size(audio_stream.filesize)
                }
                videos.append({'yt': yt, 'streams': streams_info, 'audio': audio_info})

            return render_template("playlistDownload.html", videos=videos, playlist_title=pl.title)
        return render_template("playlist.html")
    except Exception as e:
        return f"Error: {e}"

@app.route('/downloadPlaylist/<int:index>/<int:itag>/<string:audio>', methods=['POST', 'GET'])
def download_playlist(index, itag, audio):
    try:
        pl = Playlist(session['link'])
        video_url = pl.video_urls[index]
        yt = YouTube(video_url)
        
        if audio == "true":
            stream = yt.streams.get_audio_only()
            file_ext = "mp3"
        else:
            stream = yt.streams.get_by_itag(itag)
            file_ext = stream.subtype

        out_path = os.path.join(DOWNLOAD_FOLDER, f"{yt.title}.{file_ext}")
        stream.download(output_path=DOWNLOAD_FOLDER, filename=f"{yt.title}.{file_ext}")

        return send_file(out_path, as_attachment=True, download_name=f"{yt.title}.{file_ext}")
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
