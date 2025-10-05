from flask import Flask, redirect, request, render_template, session, send_file, flash
import yt_dlp as youtube_dl
import math
app = Flask(__name__)
app.config['SECRET_KEY'] = "654c0fb3968af9d5e6a9b3edcbc7051b"

dictonary={}

@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')

@app.route('/', methods=['POST', 'GET'])
def home():
    try:
        if request.method == 'POST':
            ydl_opts={}
            session['link'] = request.form.get('inputbox')
            ydl=youtube_dl.YoutubeDL(ydl_opts)
            url =ydl.extract_info(session['link'], download=False)
            # Here we get all the resulation of a video
            video_streams = url.get('formats', [])
            # Here we file the size of the audio file
            video=youtube_dl.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'})
            info_dict = video.extract_info(session['link'], download = False)

            audioSize=[info_dict['format_id'], convert_size(info_dict['filesize'])]
            # Here we make a resolutions set for storing not repetitave resulations size in MB or GB
            resolutions={}
            for stream in video_streams:
                resolution = stream.get('format_note')
                size= convert_size(stream.get("filesize"))
                # print(f"{resolution}  {convert_size(stream.get('filesize'))} {stream['format_id']}")
                if(resolution.split("p")[0].isdigit() and size != "0 MB"):
                    if(resolutions.get(resolution) == None):
                        resolutions[resolution] = [stream['format_id'], convert_size(stream.get('filesize'))]
                    else:
                        before = float(resolutions[resolution][1].split(' ')[0])
                        after=float(convert_size(stream.get('filesize')).split(' ')[0])
                        if(before < after):
                            resolutions[resolution]=[stream['format_id'], convert_size(stream.get('filesize'))]
            # This is for Shorting the List basic of resulations
            list1 = helper(resolutions)
            return render_template("download.html", url=url, list1=list1, resolutions=resolutions, audioSize = audioSize)
        return render_template("index.html")
    except:
        return render_template("error.html")
@app.route('/download/<string:id>/<string:audio>', methods=['POST', 'GET'])
def download(id, audio):
    try:
        if request.method == 'POST':
            ydl_opts={
                'format': id,
                'outtmpl': '%(title)s.%(ext)s'
            }
            ydl = youtube_dl.YoutubeDL(ydl_opts)

            # Download the video and get the information about the downloaded file
            info_dict = ydl.extract_info(session['link'], download=True)
            filename = ydl.prepare_filename(info_dict)
            Fileformat="mp4"
            if(audio == "true"):
                Fileformat="mp3"
            Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
            # Now, use send_file to send the downloaded video to the client
            return send_file(filename, as_attachment=True, download_name=Filename)
        return redirect("/")
    except:
        return render_template("error.html")
@app.route('/playlist')
def playlist():
    return render_template("playlist.html")

@app.route('/playlistDownload', methods=['POST','GET'])
def playlistDownload():
    try:
        global dictonary, audioSize
        ydl_opts={}
        if(request.method == 'POST'):
            session['link']=request.form.get("inputbox")
            # This instance is for Video
            video=youtube_dl.YoutubeDL(ydl_opts)
            url = video.extract_info(session['link'], download=False)

            # This instance is for Audio
            audio=youtube_dl.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'})

            list=[] # This Stor the Playlist resulation
            object=[] # This stor all the videos Object of playlist
            res=[] # This stor every video their own resulation
            dictonary={} # It Stor the every video size
            audioSize=[] # This is stor size of audio
            totalaudiosize="0 MB"
            length=len(url['entries'])
            dict={
                '144p':[0,'0 MB'],
                '240p':[0,'0 MB'],
                '360p':[0,'0 MB'],
                '480p':[0,'0 MB'],
                '720p':[0,'0 MB'],
                '720p60':[0, '0 MB'],
                '1080p':[0,'0 MB'],
                '1080p60':[0, '0 MB']
            }

            for index,url in enumerate(url['entries']):
                # This is for audio size
                info_audio = audio.extract_info(url['id'], download = False)
                audioSize.append([info_audio['format_id'], convert_size(info_audio['filesize'])])
                totalaudiosize=calculate_total_size(totalaudiosize , audioSize[index][1])
                
                # This info_dict if for all the video on the playlist
                info_dict = video.extract_info(url['id'], download = False)
                object.append(info_dict)
                video_streams = info_dict.get('formats', [])

                # This resolution is stor the highest resulation of each resulation from each video
                resolutions={}
                for stream in video_streams:
                    resolution = stream.get('format_note')
                    size = convert_size(stream.get("filesize"))
                    if(resolution.split("p")[0].isdigit() and size != "0 MB"):

                        # print(f"{resolution}  {convert_size(stream.get('filesize'))}  {stream.get('format_id')}")
                        if(resolutions.get(resolution) == None):
                            resolutions[resolution] = [stream.get('format_id'), convert_size(stream.get('filesize'))]
                        else:
                            before = float(resolutions[resolution][1].split(' ')[0])
                            after=float(convert_size(stream.get('filesize')).split(' ')[0])
                            if(before < after):
                                resolutions[resolution] = [stream.get('format_id'), convert_size(stream.get('filesize'))]
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
                    if(dict.get(j) != None):
                        dict[j][1]=calculate_total_size(dict[j][1] , dictonary.get(i).get(j)[1])
            return render_template("playlistDownload.html", object=object, list=list, res=res, dictonary=dictonary,audioSize=audioSize, dict=dict,totalaudiosize=totalaudiosize)
        return render_template("playlist.html")
    except:
        return render_template("error.html")
@app.route('/downloadPlaylist/<string:res>/<string:format_id>/<string:audio>', methods=['POST','GET'])
def downloadPlaylist(res, format_id, audio):
    try:
        if(request.method == 'POST'):
            ydl_opts={}
            ydl=youtube_dl.YoutubeDL(ydl_opts)
            url =ydl.extract_info(session['link'], download=False)
            videos=url['entries']
            desired_resolution=res

            # This if condition is for download the playlist
            if(desired_resolution.split("p")[-1] == ""):
                # This if condition is for download the audio of playlist
                if(desired_resolution == "audiop"):
                    # print(audioSize)
                    for index,video in enumerate(videos):
                        id = audioSize[index][0]
                        ydl_opts={
                            'format': id,
                            'outtmpl': '%(title)s.%(ext)s'
                        }
                        song=youtube_dl.YoutubeDL(ydl_opts)
                        info_dict = ydl.extract_info(video['id'], download=True)
                        filename = ydl.prepare_filename(info_dict)
                        Fileformat="mp3"
                        Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
                        # Now, use send_file to send the downloaded video to the client
                    return send_file(Filename, as_attachment=True, download_name=Filename)
                # This else condition is for download the video of playlist
                else:
                    for index, video in enumerate(videos):
                        info = ydl.extract_info(video['id'], download=False)
                        id=dictonary.get(index).get(desired_resolution)[0]
                        ydl_opts={
                            'format': id,
                            'outtmpl': '%(title)s.%(ext)s'
                        }
                        ydl=youtube_dl.YoutubeDL(ydl_opts)
                        info_dict = ydl.extract_info(video['id'], download=True)
                        filename = ydl.prepare_filename(info_dict)
                        Fileformat="mp4"
                        Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
                        # Now, use send_file to send the downloaded video to the client
                    return send_file(filename, as_attachment=True, download_name=Filename)
            else:
                ydl_opts={
                    'format': format_id,
                    'outtmpl': '%(title)s.%(ext)s'
                }
                song=youtube_dl.YoutubeDL(ydl_opts)
                obj=videos[int(desired_resolution.split("p")[-1])]
                info_dict = song.extract_info(obj['id'], download=True)
                filename = song.prepare_filename(info_dict)
                Fileformat="mp4"
                if(audio == "true"):
                    Fileformat="mp3"
                Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
                # Now, use send_file to send the downloaded video to the client
                return send_file(filename, as_attachment=True, download_name=Filename)
        return redirect("/playlistDownload")
    except:
        return render_template("error.html")
def helper(input_set):
    list1 = [resolution for resolution in input_set]  # Use list comprehension and sort in one step
    return list1

def getId(url):
    split_url = url.split('/')
    video_id = split_url[-1]
    id = video_id.split('?')[0]
    return id

def convert_size(size_in_bytes):
    if(size_in_bytes == None):
        return "0 MB"
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

def convert_to_bytes(size):
    size = str(size).lower()
    if size.endswith('kb'):
        size_in_bytes = int(float(size[:-2])) * 1024
    elif size.endswith('mb'):
        size_in_bytes = int(float(size[:-2])) * 1024 * 1024
    elif size.endswith('gb'):
        size_in_bytes = int(float(size[:-2])) * 1024 * 1024 * 1024
    else:
        raise ValueError("Invalid size format. Please provide a size in MB or GB.")
    return size_in_bytes

if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, redirect, request, render_template, session, send_file, flash
import yt_dlp as youtube_dl
import math
app = Flask(__name__)
app.config['SECRET_KEY'] = "654c0fb3968af9d5e6a9b3edcbc7051b"

dictonary={}

@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')

@app.route('/', methods=['POST', 'GET'])
def home():
    try:
        if request.method == 'POST':
            ydl_opts={}
            session['link'] = request.form.get('inputbox')
            ydl=youtube_dl.YoutubeDL(ydl_opts)
            url =ydl.extract_info(session['link'], download=False)
            # Here we get all the resulation of a video
            video_streams = url.get('formats', [])
            # Here we file the size of the audio file
            video=youtube_dl.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'})
            info_dict = video.extract_info(session['link'], download = False)

            audioSize=[info_dict['format_id'], convert_size(info_dict['filesize'])]
            # Here we make a resolutions set for storing not repetitave resulations size in MB or GB
            resolutions={}
            for stream in video_streams:
                resolution = stream.get('format_note')
                size= convert_size(stream.get("filesize"))
                if(resolution.split("p")[0].isdigit() and size != "0 MB"):
                    # print(f"{resolution}  {convert_size(stream.get('filesize'))} {stream['format_id']}")
                    if(resolutions.get(resolution) == None):
                        resolutions[resolution] = [stream['format_id'], convert_size(stream.get('filesize'))]
                    else:
                        before = float(resolutions[resolution][1].split(' ')[0])
                        after=float(convert_size(stream.get('filesize')).split(' ')[0])
                        if(before < after):
                            resolutions[resolution]=[stream['format_id'], convert_size(stream.get('filesize'))]
            # This is for Shorting the List basic of resulations
            list1 = helper(resolutions)
            return render_template("download.html", url=url, list1=list1, resolutions=resolutions, audioSize = audioSize)
        return render_template("index.html")
    # except:
    #     return render_template("error.html")
    except Exception as e:
        return f"{e}"
@app.route('/download/<string:id>/<string:audio>', methods=['POST', 'GET'])
def download(id, audio):
    try:
        if request.method == 'POST':
            ydl_opts={
                'format': id,
                'outtmpl': '%(title)s.%(ext)s'
            }
            ydl = youtube_dl.YoutubeDL(ydl_opts)

            # Download the video and get the information about the downloaded file
            info_dict = ydl.extract_info(session['link'], download=True)
            filename = ydl.prepare_filename(info_dict)
            Fileformat="mp4"
            if(audio == "true"):
                Fileformat="mp3"
            Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
            # Now, use send_file to send the downloaded video to the client
            return send_file(filename, as_attachment=True, download_name=Filename)
        return redirect("/")
    # except:
    #     return render_template("error.html")
    except Exception as e:
        return f"{e}"
@app.route('/playlist')
def playlist():
    return render_template("playlist.html")

@app.route('/playlistDownload', methods=['POST','GET'])
def playlistDownload():
    # try:
        global dictonary, audioSize
        ydl_opts={}
        if(request.method == 'POST'):
            session['link']=request.form.get("inputbox")
            # This instance is for Video
            video=youtube_dl.YoutubeDL(ydl_opts)
            url = video.extract_info(session['link'], download=False)

            # This instance is for Audio
            audio=youtube_dl.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'})

            list=[] # This Stor the Playlist resulation
            object=[] # This stor all the videos Object of playlist
            res=[] # This stor every video their own resulation
            dictonary={} # It Stor the every video size
            audioSize=[] # This is stor size of audio
            totalaudiosize="0 MB"
            length=len(url['entries'])
            dict={
                '144p':[0,'0 MB'],
                '240p':[0,'0 MB'],
                '360p':[0,'0 MB'],
                '480p':[0,'0 MB'],
                '720p':[0,'0 MB'],
                '720p60':[0, '0 MB'],
                '1080p':[0,'0 MB'],
                '1080p60':[0, '0 MB']
            }

            for index,url in enumerate(url['entries']):
                # This is for audio size
                info_audio = audio.extract_info(url['id'], download = False)
                audioSize.append([info_audio['format_id'], convert_size(info_audio['filesize'])])
                totalaudiosize=calculate_total_size(totalaudiosize , audioSize[index][1])
                
                # This info_dict if for all the video on the playlist
                info_dict = video.extract_info(url['id'], download = False)
                object.append(info_dict)
                video_streams = info_dict.get('formats', [])

                # This resolution is stor the highest resulation of each resulation from each video
                resolutions={}
                for stream in video_streams:
                    resolution = stream.get('format_note')
                    size = convert_size(stream.get("filesize"))
                    if(resolution.split("p")[0].isdigit() and size != "0 MB"):

                        # print(f"{resolution}  {convert_size(stream.get('filesize'))}  {stream.get('format_id')}")
                        if(resolutions.get(resolution) == None):
                            resolutions[resolution] = [stream.get('format_id'), convert_size(stream.get('filesize'))]
                        else:
                            before = float(resolutions[resolution][1].split(' ')[0])
                            after=float(convert_size(stream.get('filesize')).split(' ')[0])
                            if(before < after):
                                resolutions[resolution] = [stream.get('format_id'), convert_size(stream.get('filesize'))]
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
                    if(dict.get(j) != None):
                        dict[j][1]=calculate_total_size(dict[j][1] , dictonary.get(i).get(j)[1])
            return render_template("playlistDownload.html", object=object, list=list, res=res, dictonary=dictonary,audioSize=audioSize, dict=dict,totalaudiosize=totalaudiosize)
        return render_template("playlist.html")
    # except:
    #     return render_template("error.html")
    # except Exception as e:
    #     return f"{e}"
@app.route('/downloadPlaylist/<string:res>/<string:format_id>/<string:audio>', methods=['POST','GET'])
def downloadPlaylist(res, format_id, audio):
    try:
        if(request.method == 'POST'):
            ydl_opts={}
            ydl=youtube_dl.YoutubeDL(ydl_opts)
            url =ydl.extract_info(session['link'], download=False)
            videos=url['entries']
            desired_resolution=res

            # This if condition is for download the playlist
            if(desired_resolution.split("p")[-1] == ""):
                # This if condition is for download the audio of playlist
                if(desired_resolution == "audiop"):
                    for index,video in enumerate(videos):
                        id = audioSize[index][0]
                        ydl_opts={
                            'format': id,
                            'outtmpl': '%(title)s.%(ext)s'
                        }
                        song=youtube_dl.YoutubeDL(ydl_opts)
                        info_dict = ydl.extract_info(video['id'], download=True)
                        filename = ydl.prepare_filename(info_dict)
                        Fileformat="mp3"
                        Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
                        # Now, use send_file to send the downloaded video to the client
                    return send_file(filename, as_attachment=True, download_name=Filename)
                # This else condition is for download the video of playlist
                else:
                    for index, video in enumerate(videos):
                        info = ydl.extract_info(video['id'], download=False)
                        id=dictonary.get(index).get(desired_resolution)[0]
                        ydl_opts={
                            'format': id,
                            'outtmpl': '%(title)s.%(ext)s'
                        }
                        ydl=youtube_dl.YoutubeDL(ydl_opts)
                        info_dict = ydl.extract_info(video['id'], download=True)
                        filename = ydl.prepare_filename(info_dict)
                        Fileformat="mp4"
                        Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
                        # Now, use send_file to send the downloaded video to the client
                    return send_file(filename, as_attachment=True, download_name=Filename)
            else:
                ydl_opts={
                    'format': format_id,
                    'outtmpl': '%(title)s.%(ext)s'
                }
                song=youtube_dl.YoutubeDL(ydl_opts)
                obj=videos[int(desired_resolution.split("p")[-1])]
                info_dict = song.extract_info(obj['id'], download=True)
                filename = song.prepare_filename(info_dict)
                Fileformat="mp4"
                if(audio == "true"):
                    Fileformat="mp3"
                Filename=f"{filename.title().split('.')[0]}.{Fileformat}"
                # Now, use send_file to send the downloaded video to the client
                return send_file(filename, as_attachment=True, download_name=Filename)
        return redirect("/playlistDownload")
    # except:
    #     return render_template("error.html")
    except Exception as e:
        return f"{e}"
def helper(input_set):
    list1 = [resolution for resolution in input_set]  # Use list comprehension and sort in one step
    return list1

def getId(url):
    split_url = url.split('/')
    video_id = split_url[-1]
    id = video_id.split('?')[0]
    return id

def convert_size(size_in_bytes):
    if(size_in_bytes == None):
        return "0 MB"
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

def convert_to_bytes(size):
    size = str(size).lower()
    if size.endswith('kb'):
        size_in_bytes = int(float(size[:-2])) * 1024
    elif size.endswith('mb'):
        size_in_bytes = int(float(size[:-2])) * 1024 * 1024
    elif size.endswith('gb'):
        size_in_bytes = int(float(size[:-2])) * 1024 * 1024 * 1024
    else:
        raise ValueError("Invalid size format. Please provide a size in MB or GB.")
    return size_in_bytes

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
