import googleapiclient.discovery
import os
import json

def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production
    os.environ['OAUTHLIB_INSECURE_TRANSPORT']='1'

    # Initialize parameters for request
    api_service_name='youtube'
    api_version = 'v3'
    dev_api_key = '**REMOVED**'

    # Execute the request
    youtube = googleapiclient.discovery.build(api_service_name,api_version,developerKey=dev_api_key)
    request = youtube.playlistItems().list(
        part = 'snippet',
        maxResults=20,
        playlistId='PL0an7prpX1ERTY4ohSEP2ZzQVkViY91ql'
    )
    response = request.execute()

    # Display response
    # General Information
    print('General information is {}. Each page contains {}'.format(response['pageInfo'],list(response.keys())))

    # Information for each page
    page = response['items']
    # for each_video in page:
    #     #print (each_page['snippet']['title'])
    #     print (list(each_video.keys()))

    # Information for each video
    first_vid = page[0]
    first_vid_info = page[0]['snippet']
    print ('The first video ID is {}.\nIt contains {}'.format(first_vid['id'],first_vid_info.keys()))
    print ('Playlist ID:',first_vid_info['playlistId'])
    print ('Channel Titile:',first_vid_info['channelTitle'])
    print ('Channel ID:',first_vid_info['channelId'])
    print ('Song title:',first_vid_info['title'])
    print ('Position:',first_vid_info['position'])
    print ('Video ID:',first_vid_info['resourceId']['videoId'])

    # To access to each video then just need its ID. The link to access is https://www.youtube.com/watch?v=<VIDEO ID>

if __name__ == '__main__':
    main()


