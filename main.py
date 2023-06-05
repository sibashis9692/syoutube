from flask import Flask, redirect, request, render_template, session, send_file
from pytube import YouTube, Playlist

app = Flask(__name__)
app.config['SECRET_KEY'] = "654c0fb3968af9d5e6a9b3edcbc7051b"


@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')

@app.route('/', methods=['POST', 'GET'])
def home():
    try:
        if request.method == 'POST':
            session['link'] = request.form.get('inputbox')
            url = YouTube(session['link'])
            video_streams = url.streams.filter(type='video')
            audioSize=convert_size(url.streams.get_audio_only().filesize)
            resolutions={}
            for stream in video_streams:
                if(resolutions.get(stream.resolution) == None):
                    resolutions[stream.resolution] = convert_size(stream.filesize)
                else:
                    before = resolutions[stream.resolution][:-1]
                    after=convert_size(stream.filesize)[:-1]
                    if(before < after):
                        resolutions[stream.resolution]=convert_size(stream.filesize)
            list1 = helper(resolutions) # This is for Shorting the List
            return render_template("download.html", url=url, list1=list1, resolutions=resolutions, audioSize= audioSize)
        return render_template("index.html")
    except Exception as e:
        return render_template("error.html")

@app.route('/download/<string:res>', methods=['POST', 'GET'])
def download(res):
    try:
        if request.method == 'POST':
            url=YouTube(session['link'])
            selected_format = res
            if selected_format == "audio":
                audio_stream = url.streams.get_audio_only()
                file = audio_stream.download()
                # file = audio_stream.download(output_path='./', filename=f'{url.title}.mp3')
                return send_file(file, as_attachment=True)
            video = url.streams.filter(res=selected_format).first()
            file = video.download()
        return send_file(file, as_attachment=True)
    except Exception as e:  
        return render_template("error.html")

@app.route('/playlist')
def playlist():
    return render_template("playlist.html")

@app.route('/playlistDownload', methods=['POST','GET'])
def playlistDownload():
    if(request.method == 'POST'):
        session['link']=request.form.get("inputbox")
        playlist=Playlist(session['link'])
        list=[] # This Stor the Playlist resulation
        object=[] # This stor all the videos Object of playlist
        res=[] # This stor every video their own resulation
        dictonary={} # It Stor the every video size
        audioSize=[] # This is stor size of 
        totalaudiosize="0 MB"
        length=len(playlist.video_urls)
        dict={
            '144p':[0,'0 MB'],
            '240p':[0,'0 MB'],
            '360p':[0,'0 MB'],
            '480p':[0,'0 MB'],
            '720p':[0,'0 MB'],
            '1080p':[0,'0 MB']
        }
        dictonary={}

        for index,url in enumerate(playlist.video_urls):
            link=YouTube(url)
            object.append(link)
            audioSize.append(convert_size(link.streams.get_audio_only().filesize))
            totalaudiosize=calculate_total_size(totalaudiosize , audioSize[index])
            video_stream=link.streams.filter(type='video')
            # This resolution is stor the highest resulation of each each resulation from each video
            resolutions={}
            for stream in video_stream:
                if(resolutions.get(stream.resolution) == None):
                    resolutions[stream.resolution] = convert_size(stream.filesize)
                else:
                    before = resolutions[stream.resolution][:-1]
                    after=convert_size(stream.filesize)[:-1]
                    if(before < after):
                        resolutions[stream.resolution]=convert_size(stream.filesize)
            dictonary[index]=resolutions

            # Here we increment item number if the item in avalable in dict
            for item in helper(resolutions):
                if(dict.__contains__(item)):
                    dict[item][0]=dict.get(item)[0] + 1
            res.append(helper(resolutions))
        for keys in dict:
            if(dict.get(keys)[0] == length):
                list.append(keys)
        for i in dictonary:
            for j in dictonary.get(i):
                dict[j][1]=calculate_total_size(dict[j][1] , dictonary.get(i).get(j))
        return render_template("playlistDownload.html", object=object, list=list, res=res, dictonary=dictonary,audioSize=audioSize, dict=dict,totalaudiosize=totalaudiosize)
    return render_template("playlist.html")

@app.route('/downloadPlaylist/<string:res>', methods=['POST','GET'])
def downloadPlaylist(res):
    if(request.method == 'POST'):
        playlist=Playlist(session['link'])
        videos=playlist.videos
        selected_format=res
        if(selected_format.split("p")[-1] == ""):
            if(selected_format == "audiop"):
                for video in videos:
                    audio_stream = video.streams.get_audio_only()
                    file = audio_stream.download()
                return(send_file(file, as_attachment=True))
            else:
                for video in videos:
                    url = video.streams.filter(res=selected_format).first()
                    file = url.download()
                return(send_file(file, as_attachment=True))
        else:
            if(selected_format[:-1] == "audio"):
                song=videos[int(selected_format.split("o")[-1])]
                audio_stream = song.streams.get_audio_only()
                file = audio_stream.download()
                return send_file(file, as_attachment=True)
            else:
                video=videos[int(selected_format.split("p")[-1])]
                url = video.streams.filter(res=selected_format[:-1]).first()
                file = url.download()
                return send_file(file, as_attachment=True)
    return redirect("/playlistDownload")
def helper(input_set):
    list1 = [int(resolution[:-1]) for resolution in input_set]  # Use list comprehension and sort in one step
    list1.sort()
    list = [f"{str(resolution)}p" for resolution in list1]
    return list

def getId(url):
    split_url = url.split('/')
    video_id = split_url[-1]
    id = video_id.split('?')[0]
    return id

def convert_size(size_in_bytes):
    size_units = ["bytes", "KB", "MB", "GB", "TB"]
    size = size_in_bytes
    unit_index = 0
    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {size_units[unit_index]}"

def calculate_total_size(size1, size2):
    total_size_mb = 0

    if 'MB' in size1:
        size_mb = float(size1.replace('MB', '').strip())
    elif 'GB' in size1:
        size_gb = float(size1.replace('GB', '').strip())
        size_mb = size_gb * 1024
    total_size_mb += size_mb

    if 'MB' in size2:
        size_mb = float(size2.replace('MB', '').strip())
    elif 'GB' in size2:
        size_gb = float(size2.replace('GB', '').strip())
        size_mb = size_gb * 1024
    total_size_mb += size_mb

    if total_size_mb > 1023:
        total_size_gb = total_size_mb / 1024
        return f"{total_size_gb:.2f} GB"

    return f"{total_size_mb:.2f} MB"

if __name__ == '__main__':
    app.run(debug=True)
