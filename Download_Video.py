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
# Testing API:
#        https://developers.google.com/apis-explorer/#p/youtube/v3/youtube.playlistItems.list
# Sample code:
#        https://www.youtube.com/watch?v=eZUpOY8mcRY&t=569s

short_video_ID_dict = {}
long_video_ID_dict = {}
total_videos =''
no_duration_video_ID = []
result_json = {
    # List of downloaded video
    'downloaded_video_ID':[],
    # List of downloaded short video
    'downloaded_short_video_ID':[],
    # List of downloaded long video
    'download_long_video_ID':[],
    # List of failed downloaded video
    'failed_downloaded_video_ID':[],
    # List of short video ID (not downloaded)
    'short_video_ID':[],
    # List of long video ID (not downloaded)
    'long_video_ID':[],
    'video_ID_playlist':[],
}

def check_requested_videoID_from_playlist(video_count,total_videos,list_id):
    # Feature Report: results of requested video ID from playlist to filter those have long or short duration
    print ('Feature Report: Requesting video IDs from playlist to filter long/short duration ones')
    if video_count == total_videos:
        print ('    +OK: No videos are missing')
    else:
        print ('    +Missing!!: Some videos are missing')
    print ('    +{} of short audios and {} long audios are available to download out of {} and {} are deleted'.format(len(short_video_ID_dict.keys()),len(long_video_ID_dict.keys()),total_videos,total_videos-len(short_video_ID_dict.keys())-len(long_video_ID_dict.keys())))
    print ('    +Those missing videos are',list(set(list_id)-set(list(short_video_ID_dict.keys())+list(long_video_ID_dict.keys()))))
    print ('    +{} videos do not have a duration parameter'.format(len(no_duration_video_ID)))

def check_lost_duration_video_requested_videoID(response):
    # Check error information for error request of each video
    for video in response:
        if 'contentDetails' not in video:
            print (video,'has no contentDetails')
    # print (json.dumps(response,indent=4,sort_keys=True))

def check_existed_ID_download(video_ID):
    with open('.json') as json_file:
        data = json.load(json_file)
    if video_ID not in data['downloaded_video_ID']:
        return 'Existed'
    return 'Not existed'

def find_all_songs_downloaded(path):
    download_list = os.listdir(path)
    id_list = [re.search(r'.{11}',title).group() for title in download_list]
    return id_list

def open_Json_file(JSONfile):
    try:
        with open('C:/Users/pphuc/PycharmProjects/Download_List_of_Videos/'+JSONfile) as json_file:
            data = json.load(json_file)
    except Exception as err:
        print('BUG!!', err)
        data = {}
    return data

def track_prev_download_with_Json(with_duration):
    result = {
        'still remain':False,
        'short ID':[],
        'long ID': [],
        'remain ID':[],
    }
    data = open_Json_file('A_playlist_with_filter.json')
    if with_duration=='no':
        havent_download_ID = list(set(short_video_ID_dict.keys+long_video_ID_dict.keys) - set(data['downloaded_video_ID']))
        result['still remain']=True
        result['remain ID'] = havent_download_ID
    else:
        havent_download_short_ID = list(set(short_video_ID_dict.keys()) - set(data['downloaded_short_video_ID']))
        havent_download_long_ID = list(set(long_video_ID_dict.keys()) - set(data['download_long_video_ID']))
        result['still remain']=True
        result['downloaded_short_video_ID'] = havent_download_short_ID
        result['download_long_video_ID'] = havent_download_long_ID
    return result

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

def retrieve_video_ID_list(response):
    # Get a dictionary of all Video IDs in 1 response
    for video in response:
        if ('contentDetails' not in video):
            no_duration_video_ID.append(video['id'])
        else:
            if re.search(r'H',video['contentDetails']['duration']) or re.search(r'\d\dM',video['contentDetails']['duration']):
                long_video_ID_dict[video['id']]={
                'duration':video['contentDetails']['duration']
            }
            else:
                short_video_ID_dict[video['id']]={
                'duration':video['contentDetails']['duration']
            }

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
    check_lost_duration_video_requested_videoID(response_duration_result)

def request_video_ID_in_playlist(api_key,playlistID,ask_duration):
    youtube = initialize_API(api_key)

    # Request playlist and store the video IDs
    flag=True
    pageToken = ''
    video_count = 0
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
            result_json['video_ID_playlist'] +=list_ids_one_request.split(',')
            if ask_duration =='yes':
                request_video_durations(youtube,list_ids_one_request)
            if 'nextPageToken' not in response_playlist.keys():
                flag=False
                break
            pageToken = response_playlist['nextPageToken']
        except KeyError as err:
            print ('BUG!!:',err)
            break
    total_videos = response_playlist['pageInfo']['totalResults']

    # Checking result of requested playlist with filter of duration
    check_requested_videoID_from_playlist(video_count,total_videos,result_json['video_ID_playlist'])

    # Display response
    # General Information (from the last page of playlist)
    print('General information from last page of playlist is {}. Each page contains {}'.format(response_playlist['pageInfo'], list(response_playlist.keys())))
    if 'nextPageToken' in response_playlist:
        print('Next page token:', response_playlist['nextPageToken'])
    elif 'prevPageToken' in response_playlist:
        print ('Previous page token:', response_playlist['prevPageToken'])
    #display_Information(response_playlist)

def display_Information(page):
    # Information for one video
    some_vid = page[0]
    some_vid_info = some_vid['snippet']
    print ('Keys of some vid:',some_vid.keys())
    print ('The first response ID is {}.\nIt contains {}'.format(some_vid['id'],some_vid_info.keys()))
    print ('Playlist ID:',some_vid_info['playlistId'])
    print ('Channel Titile:',some_vid_info['channelTitle'])
    print ('Channel ID:',some_vid_info['channelId'])
    print ('Song title:',some_vid_info['title'])
    print ('Position:',some_vid_info['position'])
    print ('Video ID:',some_vid_info['resourceId']['videoId'])

def create_directory(path):
    if not os.path.exists(path + 'Download Youtube Audio/'):
        os.makedirs(path+'Download Youtube Audio/')
    else:
        os.chdir(path+'Download Youtube Audio/')

def download_one_Youtube_video(video_link):
    # Download a Youtube video
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    download_video_options = {}
    with youtube_dl.YoutubeDL(download_video_options) as ydl:
        ydl.download([video_link])

def download_one_Youtube_audio(video_link):
    # Download a single audio
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    download_audio_options = {
        # Choice of video quality: bestaudio/best for best quality or worstaudio/worst for worst quality
        'format':'worstaudio/worst',
        # Only keep the audio
        'extractaudio':True,
        'forceduration':False,
        'quiet':False,
        # Download single, not playlist
        'noplaylist':True,
        'outtmpl':'%(id)s_%(title)s.%(ext)s',
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
    with youtube_dl.YoutubeDL(download_audio_options) as ydl:
        ydl.download([video_link])

def download_one_Youtube_audio_for_playlist(videoID,default_link):
    # Download a single audio for playlist
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    download_audio_options = {
        # Choice of video quality: bestaudio/best for best quality or worstaudio/worst for worst quality
        'format':'worstaudio/worst',
        # Only keep the audio
        'extractaudio':True,
        'forceduration':False,
        'quiet':True,
        # Download single, not playlist
        'noplaylist':True,
        'outtmpl':'%(id)s_%(title)s.%(ext)s',
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
            result_json['downloaded_video_ID'].append(videoID)
            if videoID in result_json['short_video_ID']:
                result_json['downloaded_short_video_ID'].append(videoID)
            elif videoID in result_json['download_long_video_ID']:
                result_json['download_long_video_ID'].append(videoID)
            result_json['downloaded_short_video_ID'].append(videoID)
    except Exception as err:
        result_json['failed_downloaded_video_ID'].append(videoID)
        print ('BUG!! Problem downloading with',videoID,'as follow',err)

def download_Youtube_playlist(default_link_playlist):
    print ('Number of songs limited to download: ',end='')
    numb_song = int(input())
    download_option={
        'format':'worstaudio/worst',
        'extractaudio':True,
        'noplaylist':False,
        'playlistend':numb_song,
        # Remove the download discription
        'quiet':False,
        'outtmpl':'%(id)s_%(title)s.%(ext)s',
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

def download_a_list_audio(video_ID_list):
    # Download a playlist without long duration videos
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    default_link = 'https://www.youtube.com/watch?v='
    # Download short audio
    for videoID in tqdm(video_ID_list):
        download_one_Youtube_audio_for_playlist(videoID, default_link)

def download_Functions(video_link='',playlist_ID='',type='',list_video=[]):
    print ('Downloading ...')
    if video_link != None and type =='video':
        # Download a video
        try:
            download_one_Youtube_video(video_link)
            result_json['downloaded_video_ID'].append(video_link)
        except Exception as err:
            result_json['failed_downloaded_video_ID'].append(video_link)
            print('BUG!! Problem downloading with', video_link, 'as follow', err)

    if video_link != None and type == 'audio':
        # Download a song
        try:
            download_one_Youtube_audio(video_link)
            result_json['downloaded_video_ID'].append(video_link)
        except Exception as err:
            result_json['failed_downloaded_video_ID'].append(video_link)
            print('BUG!! Problem downloading with', video_link, 'as follow', err)

    if playlist_ID != None and type=='playlist':
        # Download Playlist
        # To access to each playlist then just need its ID. The link to access is https://www.youtube.com/playlist?list=
        default_link_playlist='https://www.youtube.com/playlist?list='+playlist_ID
        download_Youtube_playlist(default_link_playlist)

    if type=='filter_short' and len(short_video_ID_dict)>0:
        # Download short audio
        download_a_list_audio(short_video_ID_dict.keys())

    if type =='filter_long' and len(long_video_ID_dict) > 0:
        # Download long audio
        download_a_list_audio(long_video_ID_dict.keys())

    if type=='conti' and len(list_video)>0:
        download_a_list_audio(list_video)

def writeToJson(path,filename,data):
    result_json['long_video_ID'] = list(long_video_ID_dict.keys())
    result_json['short_video_ID'] = list(short_video_ID_dict.keys())
    filePathName = path+filename+'.json'
    with open(filePathName,'w') as fp:
        json.dump(data,fp)

def input_variables():
    print ('1. Download a video')
    print ('2. Download an audio')
    print ('3. Download a playlist of audios')
    print ('4. Download a playlist of audios with a filter of duration')
    print ('5. Download songs from play list which are not available in the JSON file')
    print ('6. Download songs from play list which are not available in the download folder')
    print ('7. Download songs which are failed from the playlist')
    print ('Choose action service from Youtube (by selecting number)): ',end='')
    option = input()
    return option

def input_single_download():
    print('Video ID: ', end='')
    videoID = input()
    return videoID

def input_multiple_download():
    print('Playlist ID: ', end='')
    playlist_ID = input()
    return playlist_ID

def input_API_key():
    print ('Your API key: ',end='')
    api = input()
    #
    return api

def ask_for_which_task():
    print ('Get type of songs (short/long): ',end='')
    return input()

def option1(report_store_path):
    download_Functions(video_link='https://www.youtube.com/watch?v=' + input_single_download(), type='video')
    writeToJson(report_store_path, 'One_video', result_json)

def option2(report_store_path):
    download_Functions(video_link='https://www.youtube.com/watch?v=' + input_single_download(), type='audio')
    writeToJson(report_store_path, 'One_audio', result_json)

def option3():
    download_Functions(playlist_ID=input_multiple_download(), type='playlist')

def option4(report_store_path):
    # Prepare API requests
    # Default Variables
    API_key = input_API_key()
    print('Distinguish the duration ? (yes/no): ', end='')
    duration = input()
    type_audio = ask_for_which_task()
    request_video_ID_in_playlist(API_key, input_multiple_download(), duration)
    if duration == 'yes':
        if type_audio=='short':
            download_Functions(type='filter_short')
        elif type_audio=='long':
            download_Functions(type='filter_long')
        writeToJson(report_store_path, 'A_playlist_with_filter', result_json)
    else:
        print('Please choose the 3rd option')

def option5(report_store_path):
    API_key = input_API_key()
    print('Distinguish the duration ? (yes/no): ', end='')
    duration = input()
    type_audio = ask_for_which_task()
    request_video_ID_in_playlist(API_key, input_multiple_download(), duration)

    trace_result = track_prev_download_with_Json(duration)
    print('Is there any video to download ?', trace_result['still remain'])
    if trace_result['still remain'] == True:
        if duration == 'no':
            download_Functions(type='conti', list_video=trace_result['remain ID'])
        else:
            if (type_audio=='short'):
                download_Functions(type='conti', list_video=trace_result['downloaded_short_video_ID'])
            elif type_audio=='long':
                download_Functions(type='conti',list_video=trace_result['download_long_video_ID'])
    writeToJson(report_store_path, 'Continue_download_from_pre_playlist_from_JSON', result_json)

def option6(report_store_path,path):
    downloaded_list = find_all_songs_downloaded(path+'Download Youtube Audio/')
    print ('Songs are not in the folder:',downloaded_list)
    API_key = input_API_key()
    request_video_ID_in_playlist(API_key, input_multiple_download(), 'no')
    not_existed_in_folder = list(set(result_json['video_ID_playlist']) - set(downloaded_list))
    download_Functions(type='conti',list_video=not_existed_in_folder)
    writeToJson(report_store_path, 'Continue_download_from_pre_playlist_in_Folder', result_json)

def option7(report_store_path):
    print ('Choose a json file to look at: ',end='')
    json_file = input()
    data = open_Json_file(json_file)
    if len(data['failed_downloaded_video_ID']) > 0:
        download_Functions(type='conti',list_video=data['failed_downloaded_video_ID'])
        writeToJson(report_store_path,'Failed_download_from_list',result_json)

def main():
    start_time = time.time()

    # Default Variables
    path = os.path.join('C:/Users/pphuc/Desktop/Docs/Current Using Docs/')
    create_directory(path)
    report_store_path = 'C:/Users/pphuc/PycharmProjects/Download_List_of_Videos/'

    # Input
    option = input_variables()

    # Process
    if option == '1':
        option1(report_store_path)
    if option == '2':
        option2(report_store_path)
    if option == '3':
        option3()
    if option == '4':
        option4(report_store_path)
    if option == '5':
        option5(report_store_path)
    if option == '6':
        option6(report_store_path,path)
    if option == '7':
        option7(report_store_path)

    if len(result_json['failed_downloaded_video_ID']) > 0:
        print ('These songs are failed to download:',result_json['failed_downloaded_video_ID'])

    # Finish
    print('Done! from ', time.asctime(time.localtime(start_time)), ' to ',time.asctime(time.localtime(time.time())))

if __name__ == '__main__':
    main()