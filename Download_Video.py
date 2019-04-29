from __future__ import unicode_literals
import os
import googleapiclient.discovery
import youtube_dl
import re
from tqdm import tqdm
import json
import time
# Package:
#        https://github.com/ytdl-org/youtube-dl
# Settings for downloading:
#        https://github.com/ytdl-org/youtube-dl/blob/611c1dd96efc36a788475e14cc4de64d554d28a0/youtube_dl/YoutubeDL.py#L248
# Sample code:
#        https://www.programcreek.com/python/example/98358/youtube_dl.YoutubeDL
# Sample API:
#        https://developers.google.com/apis-explorer/#p/youtube/v3/youtube.videos.list?part=contentDetails&id=jMeSar7_ECE&fields=etag%252CeventId%252Citems%252Ckind%252CnextPageToken%252CpageInfo%252CprevPageToken%252CtokenPagination%252CvisitorId&_h=2&
# Sample code:
#        https://www.youtube.com/watch?v=eZUpOY8mcRY&t=569s

short_video_ID_dict = {}
long_video_ID_dict = {}
no_duration_video_ID = []
result_json = {
    # List of downloaded video
    'downloaded_ID':[],
    # List of failed downloaded video
    'not_downloaded_ID':[],
    # The latest video in the playlist as the process executes from the lastest to the oldest
    'lastest_downloaded_ID':'',
    # List of short video ID (not downloaded)
    'short_video_ID':[],
    # List of long video ID (not downloaded)
    'long_video_ID':[],
}
total_videos =''

def retrieve_video_ID_list(response):
    # Get a dictionary of all Video IDs in 1 response
    for video in response:
        if ('contentDetails' not in video):
            no_duration_video_ID.append(video['id'])
        else:
            if re.search(r'H',video['contentDetails']['duration']) or re.search(r'd/d/',video['contentDetails']['duration'])  :
                long_video_ID_dict[video['id']]={
                'duration':video['contentDetails']['duration']
            }
            else:
                short_video_ID_dict[video['id']]={
                'duration':video['contentDetails']['duration']
            }

def check_requested_videoID_from_playlist(video_count,total_videos,list_id):
    if video_count == total_videos:
        print ('OK: No videos are missing')
    else:
        print ('Missing!!: Some videos are missing')
    print ('{} of short audios and {} long audios are available to download out of {} and {} are deleted'.format(len(short_video_ID_dict.keys()),len(long_video_ID_dict.keys()),total_videos,total_videos-len(short_video_ID_dict.keys())-len(long_video_ID_dict.keys())))
    print ('Those missing videos are',list(set(list_id)-set(list(short_video_ID_dict.keys())+list(long_video_ID_dict.keys()))))

def check_lost_duration_requested_videoID(response):
    for video in response:
        if 'contentDetails' not in video:
            print (video,'has no contentDetails')
    # print (json.dumps(response,indent=4,sort_keys=True))

def request_video_durations(youtube,list_ids_one_request):
    try:
        request_duration = youtube.videos().list(
            part='contentDetails',
            id=list_ids_one_request
        )
        response_duration = request_duration.execute()
        response_duration_result = response_duration['items']
    except KeyError as err:
        # print (response_page)
        print('BUG!!:', err)
    retrieve_video_ID_list(response_duration_result)
    check_lost_duration_requested_videoID(response_duration_result)

def initialize_API(api_key):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT']='1'

    # Initialize parameters for request
    api_service_name='youtube'
    api_version = 'v3'
    dev_api_key =api_key

    # Execute the request
    youtube = googleapiclient.discovery.build(api_service_name,api_version,developerKey=dev_api_key)
    return youtube

def prepare_API_request(api_key,playlistID):

    youtube = initialize_API(api_key)

    # Request playlist and store the video IDs
    flag=True
    pageToken = ''
    video_count = 0
    list_id = []
    while flag:
        try:
            request_playlist = youtube.playlistItems().list(
                part = 'snippet',
                maxResults=50,
                playlistId=playlistID,
                pageToken=pageToken,
            )
            response_playlist = request_playlist.execute()
            response_page = response_playlist['items']
            video_count += len(response_page)
            list_ids_one_request = ','.join([video['snippet']['resourceId']['videoId'] for video in response_page])
            list_id +=list_ids_one_request.split(',')
            request_video_durations(youtube,list_ids_one_request)
            if 'nextPageToken' not in response_playlist.keys():
                flag=False
                break
            pageToken = response_playlist['nextPageToken']
        except KeyError as err:
            print ('BUG!!:',err)
            break
    total_videos = response_playlist['pageInfo']['totalResults']
    # Checking
    check_requested_videoID_from_playlist(video_count,total_videos,list_id)
    print ('{} videos do not have a duration parameter'.format(len(no_duration_video_ID)))

def display_Info_response(response_playlist,response_duration):
    # Display response
    # General Information
    print('General information is {}. Each page contains {}'.format(response_playlist['pageInfo'], list(response_playlist.keys())))
    print('Next page token:', response_playlist['nextPageToken'])
    print('Response duration:',response_duration)

def display_Info_one_video(page):
    # Information for one video
    some_vid = page[1]
    some_vid_info = some_vid['snippet']
    print ('Keys of some vid:',some_vid.keys())
    print ('The first response ID is {}.\nIt contains {}'.format(some_vid['id'],some_vid_info.keys()))
    print ('Playlist ID:',some_vid_info['playlistId'])
    print ('Channel Titile:',some_vid_info['channelTitle'])
    print ('Channel ID:',some_vid_info['channelId'])
    print ('Song title:',some_vid_info['title'])
    print ('Position:',some_vid_info['position'])
    print ('Video ID:',some_vid_info['resourceId']['videoId'])

def display_Information(page):
    # Information
    display_Info_one_video(page)

def create_directory(path):
    if not os.path.exists(path + 'Download Youtube Audio/'):
        os.makedirs(path+'Download Youtube Audio/')
    else:
        os.chdir(path+'Download Youtube Audio/')
    return path

def check_last_stop_downloading():
    pass



def download_one_Youtube_video(video_info,default_link):
    # Download a Youtube video
    download_video_options = {}
    with youtube_dl.YoutubeDL(download_video_options) as ydl:
        ydl.download([default_link+video_info['resourceId']['videoId']])

def download_one_Youtube_audio(videoID,default_link):
    # Download a Youtube audio
    download_audio_options = {
        # Choice of video quality: bestaudio/best for best quality or worstaudio/worst for worst quality
        'format':'worstaudio/worst',
        # Only keep the audio
        'extractaudio':True,
        'forceduration':False,'quiet':True,
        # Download single, not playlist
        'noplaylist':True,
        'outtmpl':'%(title)s.%(ext)s',
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
            ydl.download([default_link+videoID])
            result_json['downloaded_ID'].append(videoID)
    except Exception as err:
        result_json['not_downloaded_ID'].append(videoID)
        print ('BUG!! Problem downloading with',videoID,'as follow',err)

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
        print ('BUG!! Problem downloading with',default_link_playlist,'as follow',err)

def download_Functions(playlist_ID):
    # Download a single audio
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    default_link = 'https://www.youtube.com/watch?v='

    # Download a song
    download_one_Youtube_audio('vxkN3o-KELo',default_link)


    # Download a playlist without long duration videos
    #result_json['lastest_downloaded_ID']=short_video_ID_dict[0]
    #check_last_stop_downloading()
    # for videoID in tqdm(short_video_ID_dict.keys()):
    #     download_one_Youtube_audio(videoID,default_link)
        #download_one_Youtube_video(sample_video_info,default_link)

    # Download Playlist
    # To access to each playlist then just need its ID. The link to access is https://www.youtube.com/playlist?list=
    # default_link_playlist='https://www.youtube.com/playlist?list='+playlist_ID
    # download_Youtube_playlist(default_link_playlist)

def writeToJson(path,filename,data):
    filePathName = path+filename+'.json'
    with open(filePathName,'w') as fp:
        json.dump(data,fp)

def main():
    start_time = time.time()
    # Default Variables
    playlist_ID = 'PL0an7prpX1ERTY4ohSEP2ZzQVkViY91ql'
    API_key = '**REMOVED**'
    path = os.path.join('C:/Users/pphuc/Desktop/Docs/Current Using Docs/')

    # Prepare API requests
    prepare_API_request(API_key, playlist_ID)
    print ('Length:',len(long_video_ID_dict),'Long:',long_video_ID_dict)
    print ('Length:',len(short_video_ID_dict),'Short:',short_video_ID_dict)

    # response_playlist,response_duration =prepare_API_request(API_key,playlist_ID)
    # display_Info_response(response_playlist,response_duration)
    # page = response_playlist
    # display_Information(page)

    path = create_directory(path)

    download_Functions(playlist_ID)

    result_json['long_video_ID'] = list(long_video_ID_dict.keys())
    result_json['short_video_ID'] = list(short_video_ID_dict.keys())

    report_store_path = 'C:/Users/pphuc/PycharmProjects/Download_List_of_Videos/'
    writeToJson(report_store_path,'Result',result_json)
    
    print('Done! from ', time.asctime(time.localtime(start_time)), ' to ',time.asctime(time.localtime(time.time())))

if __name__ == '__main__':
    main()


