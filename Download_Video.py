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

# Global variables which connect functions
# Store short duration videos
short_video_ID_dict = {}
# Store long duration videos
long_video_ID_dict = {}
# Store the number of songs in the playlist
total_videos_global =''
# Store the video IDs which dont have the duraton even after requested. This happens when some videos are deleted by uploader or youtube
no_duration_video_ID = []
# Store the result after downloading
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

# Results of requested video ID from playlist to filter those have long or short duration
def check_requested_videoID_from_playlist(video_count,total_videos,list_id):
    print ('Feature Report: Requesting video IDs from playlist to filter long/short duration ones')
    # video_count is used to count the number of video downloaded
    # total_videos is the number of videos in the playlist
    if video_count == total_videos:
        print ('    +OK: No videos are missing')
    else:
        print ('    +Missing!!: Some videos are missing')
    print ('    +{} of short audios and {} long audios are available to download out of {} and {} are deleted'.format(len(short_video_ID_dict.keys()),len(long_video_ID_dict.keys()),total_videos,total_videos-len(short_video_ID_dict.keys())-len(long_video_ID_dict.keys())))
    print ('    +Those missing videos are',list(set(list_id)-set(list(short_video_ID_dict.keys())+list(long_video_ID_dict.keys()))))
    print ('    +{} videos do not have a duration parameter'.format(len(no_duration_video_ID)))

# Check error information for error request of each video
def check_lost_duration_video_requested_videoID(response):
    # response is the list of song data which contain video duration
    for video in response:
        if 'contentDetails' not in video:
            print (video,'has no contentDetails')
    # print (json.dumps(response,indent=4,sort_keys=True))

# Look at the json file to see result
def check_existed_ID_download(file,video_ID):
    with open(file+'.json') as json_file:
        data = json.load(json_file)
    # Video ID is the video needed to be check
    if video_ID not in data['downloaded_video_ID']:
        return 'Existed'
    return 'Not existed'

# Look at the download folder to see what songs are downloaded and shows their ID
def find_all_songs_downloaded(path):
    download_list = os.listdir(path)
    id_list = [re.search(r'.{11}',title).group() for title in download_list]
    return id_list

# Open a Json file
def open_Json_file(JSONfile):
    try:
        with open('C:/Users/pphuc/PycharmProjects/Download_List_of_Videos/'+JSONfile) as json_file:
            data = json.load(json_file)
    except Exception as err:
        print('BUG!!', err)
        data = {}
    return data

# Track the previous download by looking at Json file
def track_prev_download_with_Json(with_duration,Json_file):
    # result is used to store the checking result
    result = {
        'still remain':False,
        'short ID':[],
        'long ID': [],
        'remain ID':[],
    }
    data = open_Json_file(Json_file)
    if with_duration=='no':
        # Store the video ID of those failed without distinguishing how long those videso are
        havent_download_ID = list(set(short_video_ID_dict.keys+long_video_ID_dict.keys) - set(data['downloaded_video_ID']))
        result['still remain']=True
        result['remain ID'] = havent_download_ID
    else:
        # Store the video ID of those failed with distinguishing how long those videso are
        havent_download_short_ID = list(set(short_video_ID_dict.keys()) - set(data['downloaded_short_video_ID']))
        havent_download_long_ID = list(set(long_video_ID_dict.keys()) - set(data['download_long_video_ID']))
        result['still remain']=True
        result['downloaded_short_video_ID'] = havent_download_short_ID
        result['download_long_video_ID'] = havent_download_long_ID
    return result

# Create the initial input for process
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

# Categorize videos into seperate enities
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

def request_video_duraion(youtube,list_ids_one_request):
    try:
        request_duration = youtube.videos().list(
            part='contentDetails',
            id=list_ids_one_request
        )
        response_duration = request_duration.execute()
        response_duration_result = response_duration['items']
        return response_duration_result
    except KeyError as err:
        # print (response_page)
        print('BUG!!:', err)
    return

# Take the API to request data every single video in the list
def video_durations(youtube,list_ids_one_request):
    response_duration_result = request_video_duraion(youtube,list_ids_one_request)
    retrieve_video_ID_list(response_duration_result)
    check_lost_duration_video_requested_videoID(response_duration_result)

# Take the API to request data of a playlist
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
                video_durations(youtube,list_ids_one_request)
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
    total_videos_global = total_videos
    # Display response
    # General Information (from the last page of playlist)
    print('General information from last page of playlist is {}. Each page contains {}'.format(response_playlist['pageInfo'], list(response_playlist.keys())))
    if 'nextPageToken' in response_playlist:
        print('Next page token:', response_playlist['nextPageToken'])
    elif 'prevPageToken' in response_playlist:
        print ('Previous page token:', response_playlist['prevPageToken'])
    #display_Information(response_playlist)

# Display information of a page in the play list
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

# Create a download folder
def create_directory(path):
    if not os.path.exists(path + 'Download Youtube Audio/'):
        os.makedirs(path+'Download Youtube Audio/')
    else:
        os.chdir(path+'Download Youtube Audio/')

# Download a video
def download_one_Youtube_video(video_link):
    # Download a Youtube video
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    download_video_options = {}
    with youtube_dl.YoutubeDL(download_video_options) as ydl:
        ydl.download([video_link])

# Download an audio
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

# Download an audio in the playlist
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

# Download an audio playlist
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

# Download a list of audio. This list is not a playlist
def download_a_list_audio(video_ID_list):
    # Download a playlist without long duration videos
    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>
    default_link = 'https://www.youtube.com/watch?v='
    # Download short audio
    for videoID in tqdm(video_ID_list):
        download_one_Youtube_audio_for_playlist(videoID, default_link)

# Contain all download functions
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

# Write result of download
def writeToJson(path,filename,data):
    result_json['long_video_ID'] = list(long_video_ID_dict.keys())
    result_json['short_video_ID'] = list(short_video_ID_dict.keys())
    filePathName = path+filename+'.json'
    with open(filePathName,'w') as fp:
        json.dump(data,fp)

# Create task option inputs
def input_variables():
    print ('1. Download a video')
    print ('2. Download an audio')
    print ('3. Download a playlist of audios')
    print ('4. Download a playlist of audios with a filter of duration')
    print ('5. Download songs from a playlist which are not available in the JSON file')
    print ('6. Download songs from a playlist which are not available in the download folder')
    print ('7. Download songs which are failed from the playlist')
    print ('8. Download a list of songs made by users')
    print ('Choose action service from Youtube (by selecting number)): ',end='')
    option = input()
    return option

# Create input for download option
def input_single_download():
    print('Video ID: ', end='')
    videoID = input()
    return videoID

# Create input for download option
def input_multiple_download():
    print('Playlist ID: ', end='')
    playlist_ID = input()
    return playlist_ID

# Create input for download option
def input_API_key():
    print ('Your API key: ',end='')
#    api = input()
    path = re.sub(r'\\','/','C:\\Users\\pphuc\\PycharmProjects\\Download_List_of_Videos')+'/passwords.txt'
    try:
        with open(path,'r') as  f:
          api = f.readline()
          return api
    except Exception as err:
        print ('Error with accessing password file: ',err)
    return

# Create input for download option
def ask_for_which_task():
    print ('Get type of songs (short/long): ',end='')
    return input()

# Search for video on Youtube
def search_video(youtube,data,api_key):
    try:
        search_video = youtube.search().list(
            part='snippet',
            q = data,
            type='video',
            maxResults=3,
        )
        search_execution = search_video.execute()
        response_result = search_execution['items']
        return response_result
    except Exception as err:
        print ('Error with searching video: ',err)
    return

# Extract duration and calcaulate to measure with second parameter
def extract_duration(youtube,dict_video):
    string_list_video_id = ','.join(list(dict_video.keys()))
    list_duration_result = [info['contentDetails']['duration'][2:] for info in request_video_duraion(youtube,string_list_video_id)]
    for key in dict_video:
        key_index = list(dict_video.keys()).index(key)
        duration = list_duration_result[key_index]
        temp_variable = 0
        if re.search(r'H', duration):
            temp_variable += int(re.search(r'\d+H', duration).group()[:-1]) * 3600
        if re.search(r'M', duration):
            temp_variable += int(re.search(r'\d+M', duration).group()[:-1]) * 60
        if re.search(r'S', duration):
            temp_variable += int(re.search(r'\d+S', duration).group()[:-1])
        dict_video[key].append(temp_variable)
        dict_video[key].append(duration)
    return dict_video

# Pick the most qualified video
def find_desired_video(data,dict_video):
    min_duration = min([v[1] for v in dict_video.values()])
    for k,v in dict_video.items():
        if (re.search(r'[L|l]yrics]',v[0]) or re.search(r'[O|o]fficial',v[0])) and  v[1]==min_duration:
            return [k,v]
        else:
            if v[1] == min_duration:
                return [k,v]

# Find match video by passing down to smaller functions


def find_match(youtube,inputted_song,list_searching_result):
    dict_video = {}
    for video in list_searching_result:
        video_id = video['id']['videoId']
        video_title = video['snippet']['title']
        dict_video[video_id]=[video_title]
    dict_video = extract_duration(youtube,dict_video)
    matched_video = find_desired_video(inputted_song,dict_video)
    return matched_video

# Download a song
def download_song_from_list(video):
    download_Functions(video_link='https://www.youtube.com/watch?v=' + video[0], type='audio')
    load_to_rewrite_Json(video)

def load_to_rewrite_Json(video):
    file_name = '/'.join(os.path.abspath('Download_Video.py').split('\\')[:-1])+'/Downloaded_songs_from_a_user_list.json'
    if not os.path.isfile(file_name):
        data = {video[0]: video[1]}
        with open(file_name, 'w') as fp:
            json.dump(data, fp)
    else:
        with open(file_name, 'r') as feedsjson:
            feeds = json.load(feedsjson)
        feeds[video[0]]=video[1]
        with open(file_name, 'w') as fp:
            json.dump(feeds, fp)

# Task 1: Download a video
def option1(report_store_path):
    download_Functions(video_link='https://www.youtube.com/watch?v=' + input_single_download(), type='video')
    writeToJson(report_store_path, 'One_video', result_json)

# Task 2: Download an audio
def option2(report_store_path):
    download_Functions(video_link='https://www.youtube.com/watch?v=' + input_single_download(), type='audio')
    writeToJson(report_store_path, 'One_audio', result_json)

# Task 3: Download a playlist of audio
def option3():
    download_Functions(playlist_ID=input_multiple_download(), type='playlist')

# Task 4: Download a playlist of audios with a filter of duration
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

# Task 5: Download songs from a playlist which are not available in the JSON file
def option5(report_store_path):
    API_key = input_API_key()
    print('Distinguish the duration ? (yes/no): ', end='')
    duration = input()
    type_audio = ask_for_which_task()
    request_video_ID_in_playlist(API_key, input_multiple_download(), duration)

    trace_result = track_prev_download_with_Json(duration,'A_playlist_with_filter.json')
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

# Task 6: Download songs from a playlist which are not available in the download folder
def option6(report_store_path,path):
    downloaded_list = find_all_songs_downloaded(path+'Download Youtube Audio/')
    print ('Songs are not in the folder:',downloaded_list)
    API_key = input_API_key()
    request_video_ID_in_playlist(API_key, input_multiple_download(), 'no')
    not_existed_in_folder = list(set(result_json['video_ID_playlist']) - set(downloaded_list))
    download_Functions(type='conti',list_video=not_existed_in_folder)
    writeToJson(report_store_path, 'Continue_download_from_pre_playlist_in_Folder', result_json)

# Task 7: Download songs which are failed from the playlist
def option7(report_store_path):
    print ('Choose a json file to look at: ',end='')
    json_file = input()
    data = open_Json_file(json_file)
    if len(data['failed_downloaded_video_ID']) > 0:
        download_Functions(type='conti',list_video=data['failed_downloaded_video_ID'])
        writeToJson(report_store_path,'Failed_download_from_list',result_json)

# Task 8: Download a list of songs passed by users
def option8(restore_store_path):
    print ('Pass the input text file: ',end='')
    input_file = input()
    api_key = input_API_key()
    if re.search(r'\\',input_file):
        input_file = re.sub(r"\\",'/',input_file)
    try:
        youtube = initialize_API(api_key)
        with open(input_file,'r') as inp_file:
            inputted_songs = inp_file.readlines()
            for line_song in inputted_songs:
                list_resulst= search_video(youtube,line_song[:-1],api_key)
                found_video = find_match(youtube,line_song[:-1],list_resulst)
                download_song_from_list(found_video)
    except Exception as err:
        print ('Error with reading from input file: ',err)

# Control the flow of the program
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
    if option == '8':
        option8(report_store_path)


    if len(result_json['failed_downloaded_video_ID']) > 0:
        print ('These songs are failed to download:',result_json['failed_downloaded_video_ID'])

    # Finish
    print('Done! from ', time.asctime(time.localtime(start_time)), ' to ',time.asctime(time.localtime(time.time())))

if __name__ == '__main__':
    main()

#C:\Users\pphuc\PycharmProjects\Download_List_of_Videos/list_of_songs.txt

