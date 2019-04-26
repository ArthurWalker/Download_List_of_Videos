from __future__ import unicode_literals
import os
import googleapiclient.discovery
import youtube_dl
# https://github.com/ytdl-org/youtube-dl
# Settings for downloading:
#        https://github.com/ytdl-org/youtube-dl/blob/611c1dd96efc36a788475e14cc4de64d554d28a0/youtube_dl/YoutubeDL.py#L248

def prepare_API_request(api_key,playlistID):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT']='1'

    # Initialize parameters for request
    api_service_name='youtube'
    api_version = 'v3'
    dev_api_key =api_key

    # Execute the request
    youtube = googleapiclient.discovery.build(api_service_name,api_version,developerKey=dev_api_key)
    request = youtube.playlistItems().list(
        part = 'snippet',
        maxResults=20,
        playlistId=playlistID,
        pageToken=''
    )
    response = request.execute()
    return response

def display_Info_response(response):
    # Display response
    # General Information
    print('General information is {}. Each page contains {}'.format(response['pageInfo'], list(response.keys())))
    print('Next page token:', response['nextPageToken'])

def display_Info_eachPage(page):
    # Information for each page
    for each_video in page:
        #print (each_page['snippet']['title'])
        print (list(each_video.keys()))

def display_Info_one_video(page):
    # Information for one video
    some_vid = page[1]
    some_vid_info = some_vid['snippet']
    print ('The first video ID is {}.\nIt contains {}'.format(some_vid['id'],some_vid_info.keys()))
    print ('Playlist ID:',some_vid_info['playlistId'])
    print ('Channel Titile:',some_vid_info['channelTitle'])
    print ('Channel ID:',some_vid_info['channelId'])
    print ('Song title:',some_vid_info['title'])
    print ('Position:',some_vid_info['position'])
    print ('Video ID:',some_vid_info['resourceId']['videoId'])

def display_video_ID_list(page):
    # Get a list of all Video IDs in 1 response
    lst_video_id = []
    for video in page:
        lst_video_id.append(video['snippet']['resourceId']['videoId'])
    return lst_video_id

def create_directory():
    path = os.path.join('C:/Users/pphuc/Desktop/Docs/Current Using Docs/')
    if not os.path.exists(path + 'Download Youtube Audio/'):
        os.makedirs(path+'Download Youtube Audio/')
    else:
        os.chdir(path+'Download Youtube Audio/')
    return path

def download_one_Youtube_video(video_info,default_link):
    # Download a Youtube video
    download_video_options = {}
    with youtube_dl.YoutubeDL(download_video_options) as ydl:
        ydl.download([default_link+video_info['resourceId']['videoId']])

def download_one_Youtube_audio(video_info,default_link):
    # Download a Youtube audio
    download_audio_options = {
        # Choice of video quality: bestaudio/best for best quality or worstaudio/worst for worst quality
        'format':'worstaudio/worst',
        # Only keep the audio
        'extractaudio':True,
        'forceduration':True,
        # Download single, not playlist
        'noplaylist':True,
        'outtmpl':video_info['title']+'.%(ext)s',
        'nocheckcertificate':True,
        # Print list of the formats to stdout and exit => Enable this will not download video, just print list of quality
        #'listformats':True,
        # Convert to audio
        'postprocessors':[{
                'key':'FFmpegExtractAudio',
                'preferredcodec':'mp3',
                'preferredquality':'192',
            }]
    }
    try:
        with youtube_dl.YoutubeDL(download_audio_options) as ydl:
            ydl.download([default_link+video_info['resourceId']['videoId']])
    except Exception as err:
        print ('!!!!!!!Problem downloading with',video_info['resourceId']['videoId'],'as follow',err)

def download_Youtube_playlist(default_link_playlist):
    download_option={
        'format':'worstaudio/worst',
        'extractaudio':True,
        'noplaylist':False,
        'playlistend':3,
        # Remove the download discription
        'quiet':True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    try:
        with youtube_dl.YoutubeDL(download_option) as ydl:
            ydl.download([default_link_playlist])
    except Exception as err:
        print ('!!!!!!!Problem downloading with',default_link_playlist,'as follow',err)


def main():

    playlist_ID = 'PL0an7prpX1ERTY4ohSEP2ZzQVkViY91ql'
    API_key = '**REMOVED**'
    video_id= ''
    response = prepare_API_request(API_key,playlist_ID)

    display_Info_response(response)

    page = response['items']

    # display_Info_eachPage(page)

    # display_Info_one_video(page)

    # display_video_ID_list(page)

    create_directory()

    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    # default_link = 'https://www.youtube.com/watch?v='
    # sample_video_info = page[2]['snippet']
    # download_one_Youtube_video(sample_video_info,default_link)
    # download_one_Youtube_audio(sample_video_info,default_link)

    # To access to each playlist then just need its ID. The link to access is https://www.youtube.com/playlist?list=
    # default_link_playlist='https://www.youtube.com/playlist?list='+playlist_ID
    # download_Youtube_playlist(default_link_playlist)

if __name__ == '__main__':
    main()


