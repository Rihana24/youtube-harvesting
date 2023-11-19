from googleapiclient.discovery import build
import pymongo
import psycopg2
import pandas as pd
import streamlit as st

#API_CONNECTION

def Api_connect():
    Api_Id = "AIzaSyDoEI7xI2SEOF9jHvAQFp5mUK8F6VMwNsU"

    api_service_name = "youtube"
    api_version = "v3" 

    youtube = build(api_service_name,api_version,developerKey=Api_Id)

    return youtube

youtube=Api_connect()

# get channels information

def get_channel_info(channel_id):
    request= youtube.channels().list(
                    part="snippet,ContentDetails,statistics",
                    id=channel_id
    )

    response=request.execute()

    for i in response['items']:
        data=dict(Channel_Name=i["snippet"]["title"],
                Channel_Id=i["id"],
                Subscribers=i["statistics"]["subscriberCount"],
                views=i["statistics"]["viewCount"],
                Total_Videos=i["statistics"]["videoCount"],
                Channel_Description=i["snippet"]["description"],
                Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
        return data
    
# get video ids


def get_videos_ids(channel_id):
    video_ids = []
    response = youtube.channels().list(id= channel_id,
                                    part='contentDetails').execute()
    Playlist_Id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None;


    while True:
        response1 = youtube.playlistItems().list(
                                        part = 'snippet',
                                        playlistId = Playlist_Id,
                                        maxResults = 50,
                                        pageToken=next_page_token).execute()


        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])


        next_page_token = response1.get('next_page_token')

        if next_page_token is None:
            break
    return video_ids

# get video information

def get_video_info(video_ids):
    video_data = []
    for video_id in video_ids:
        request = youtube.videos().list(
            part = "snippet,ContentDetails,statistics",
            id = video_id
        )

        response = request.execute()

        for item in response['items']:
            data = dict(Channel_Name = item['snippet']['channelTitle'],
                        Channel_Id = item['snippet']['channelId'],
                        Video_Id = item['id'],
                        Title = item['snippet']['title'],
                        Tags = item['snippet'].get('tags'),
                        Thumbnail = item['snippet']['thumbnails']['default']['url'],
                        Description = item['snippet'].get('description'),
                        Published_Date = item['snippet']['publishedAt'],
                        Duration = item['contentDetails']['duration'],
                        Views = item['statistics'].get('viewCount'),
                        Likes = item['statistics'].get('likeCount'),
                        Comments = item['statistics'].get('commentCount'),
                        Favorite_Count = item['statistics']['favoriteCount'],
                        Definition = item['contentDetails']['definition'],
                        Caption_Status = item['contentDetails']['caption']
                        )
            


            video_data.append(data)

    return video_data

#get comment information

def get_comment_info(video_ids):
    Comment_data = []
    try: 
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                        part = "snippet",
                        videoId = video_id,
                        maxResults = 50)
            
            response = request.execute()

            for item in response['items']:
                data = dict(Comment_Id = item['snippet']['topLevelComment']['id'],
                            Video_Id = item['snippet']['topLevelComment']['snippet']['videoId'],
                            Comment_Text = item['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_Author = item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_Published = item['snippet']['topLevelComment']['snippet']['publishedAt']
                            )
                
                Comment_data.append(data)
            
    except:
        pass

    return Comment_data

# get playlist details 

def get_playlist_details(channel_id):
    next_page_token = None
    All_data = []
    while True:
        request = youtube.playlists().list(
                                part = 'snippet,contentDetails',
                                channelId = channel_id,
                                maxResults = 50,
                                pageToken = next_page_token
                                )

        response = request.execute()

        for item in response['items']:
                        data = dict(Playlist_Id = item['id'],
                                    Channel_Id = item['snippet']['channelId'],
                                    Channel_Name = item['snippet']['channelTitle'],
                                    PublishedAt =item['snippet']['publishedAt'],
                                    Video_count = item['contentDetails']['itemCount'])
                        All_data.append(data)
                        
        

        next_page_token = response.get('nextPageToken')
        if next_page_token is None:
            break
            
        return All_data
    
#configuration error solved

from pymongo import MongoClient
import dns.resolver

dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

# upload to mongoDB


client = pymongo.MongoClient("mongodb+srv://rihanaparveen:rihanaj@cluster0.yy5gqa1.mongodb.net/?retryWrites=true&w=majority")
db = client["Youtube_project"]

def channel_details(channel_id):
    ch_details = get_channel_info(channel_id)
    pl_details = get_playlist_details(channel_id)
    vi_ids = get_videos_ids(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comment_info(vi_ids)


    col1=db["channel_details"]
    col1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,
                     "video_information":vi_details,"comment_information":com_details})
    
    return "upload completed successfully"
    

# Table creation for channels, playlists,videos,comments

#channel table creation

def channels_table():
    mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="rihana",
                            database="Youtube_project",
                            port = 5432)

    mycursor = mydb.cursor()

    drop_query = '''drop table if exists channel'''
    mycursor.execute(drop_query)
    mydb.commit()

    try:
        create_query = '''create table if not exists Channel(Channel_Name varchar(100),
                                                    Channel_Id varchar(80) primary key,
                                                    Subscribers bigint,
                                                    views bigint,
                                                    Total_Videos int,
                                                    Channel_Description text,
                                                    Playlist_Id varchar(80))'''     

        mycursor.execute(create_query)  
        mydb.commit()   

    except:
        print("channels table already created")


    ch_list =[]
    db=client["Youtube_project"]
    col1=db["channel_details"]
    for ch_data in col1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df = pd.DataFrame(ch_list)


    for index,row in df.iterrows():
        insert_query='''insert into Channel(Channel_Name,
                                            Channel_Id,
                                            Subscribers,
                                            views,
                                            Total_Videos,
                                            Channel_Description,
                                            Playlist_Id)
                                            
                                            values(%s,%s,%s,%s,%s,%s,%s)'''
        
        values=(row['Channel_Name'],
                row['Channel_Id'],
                row['Subscribers'],
                row['views'],
                row['Total_Videos'],
                row['Channel_Description'],
                row['Playlist_Id']
                )
        try:
            mycursor.execute(insert_query,values)
            mydb.commit()

        except:
            print("channel values already inserted")


# playlist table creation

def playlists_table():

    mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="rihana",
                            database="Youtube_project",
                            port = 5432)

    mycursor = mydb.cursor()

    drop_query = '''drop table if exists playlists'''
    mycursor.execute(drop_query)
    mydb.commit()


    create_query = '''create table if not exists playlists(Playlist_Id varchar(100) primary key,
                                                Title varchar(80),
                                                Channel_Id varchar(100),
                                                Channel_Name varchar(100),
                                                PublishedAt timestamp,
                                                Video_count int
                                                )'''     

    mycursor.execute(create_query)  
    mydb.commit()   

    pl_list =[]
    db=client["Youtube_project"]
    col1=db["channel_details"]
    for pl_data in col1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data['playlist_information'])):
            pl_list.append(pl_data['playlist_information'][i])       

    df1=pd.DataFrame(pl_list)

    for index,row in df1.iterrows():
        insert_query='''insert into playlists(Playlist_Id,
                                            Title,
                                            Channel_Id,
                                            Channel_Name,
                                            PublishedAt,
                                            Video_Count
                                            )
                                            
                                            values(%s,%s,%s,%s,%s,%s)'''
        
        values=(row['Playlist_Id'],
                row['Title'],
                row['Channel_Id'],
                row['Channel_Name'],
                row['PublishedAt'],
                row['Video_Count']
                )
        try:
            mycursor.execute(insert_query,values)
            mydb.commit()

        except:
            print("playlist values already inserted")

# video table creation

def videos_table():
        mydb = psycopg2.connect(host="localhost",
                                user="postgres",
                                password="rihana",
                                database="Youtube_project",
                                port = 5432)

        mycursor = mydb.cursor()

        drop_query = '''drop table if exists videos'''
        mycursor.execute(drop_query)
        mydb.commit()


        create_query = '''create table if not exists videos(Channel_Name varchar(100),
                                Channel_Id varchar(100),
                                Video_Id varchar(30) primary key,
                                Title varchar(150),
                                Tags text,
                                Thumbnail varchar(200),
                                Description text,
                                Published_Date timestamp,
                                Duration interval,
                                Views bigint,
                                Likes bigint,
                                Comments int,
                                Favorite_Count int,
                                Definition varchar(20),
                                Caption_Status varchar(50)
                                )'''     

        mycursor.execute(create_query)  
        mydb.commit()   

        vid_list =[]
        db=client["Youtube_project"]
        col1=db["channel_details"]
        for vid_data in col1.find({},{"_id":0,"video_information":1}):
                for i in range(len(vid_data['video_information'])):
                        vid_list.append(vid_data['video_information'][i])       

        df2=pd.DataFrame(vid_list)


        for index,row in df2.iterrows():
                insert_query='''insert into videos(Channel_Name,
                                Channel_Id,
                                Video_Id,
                                Title,
                                Tags,
                                Thumbnail,
                                Description,
                                Published_Date,
                                Duration,
                                Views,
                                Likes,
                                Comments,
                                Favorite_Count,
                                Definition,
                                Caption_Status
                                )
                                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                
                values=(row['Channel_Name'],
                        row['Channel_Id'],
                        row['Video_Id'],
                        row['Title'],
                        row['Tags'],
                        row['Thumbnail'],
                        row['Description'],
                        row['Published_Date'],
                        row['Duration'],
                        row['Views'],
                        row['Likes'],
                        row['Comments'],
                        row['Favorite_Count'],
                        row['Definition'],
                        row['Caption_Status']
                        )
                
        
                mycursor.execute(insert_query,values)
                mydb.commit()
        
# comment table creation

def comments_table():

        mydb = psycopg2.connect(host="localhost",
                                user="postgres",
                                password="rihana",
                                database="Youtube_project",
                                port = 5432)

        mycursor = mydb.cursor()

        drop_query = '''drop table if exists comments'''
        mycursor.execute(drop_query)
        mydb.commit()


        create_query = '''create table if not exists comments(Comment_Id varchar(100) primary key,
                                Video_Id varchar(50),
                                Comment_Text text,
                                Comment_Author varchar(50),
                                Comment_Published timestamp
                                )'''     

        mycursor.execute(create_query)  
        mydb.commit()   



        com_list =[]
        db=client["Youtube_project"]
        col1=db["channel_details"]
        for com_data in col1.find({},{"_id":0,"comment_information":1}):
                for i in range(len(com_data['comment_information'])):
                        com_list.append(com_data['comment_information'][i])       

        df3=pd.DataFrame(com_list)


        for index,row in df3.iterrows():
                insert_query='''insert into comments(Comment_Id,
                                Video_Id,
                                Comment_Text,
                                Comment_Author,
                                Comment_Published
                                )
                                                
                                values(%s,%s,%s,%s,%s)'''
                
                values=(row['Comment_Id'],
                        row['Video_Id'],
                        row['Comment_Text'],
                        row['Comment_Author'],
                        row['Comment_Published']
                        )
                try:        
                        mycursor.execute(insert_query,values)
                        mydb.commit()

                except:
                        print("channel values already inserted")

# comment table creation

def comments_table():

        mydb = psycopg2.connect(host="localhost",
                                user="postgres",
                                password="rihana",
                                database="Youtube_project",
                                port = 5432)

        mycursor = mydb.cursor()

        drop_query = '''drop table if exists comments'''
        mycursor.execute(drop_query)
        mydb.commit()


        create_query = '''create table if not exists comments(Comment_Id varchar(100) primary key,
                                Video_Id varchar(50),
                                Comment_Text text,
                                Comment_Author varchar(50),
                                Comment_Published timestamp
                                )'''     

        mycursor.execute(create_query)  
        mydb.commit()   



        com_list =[]
        db=client["Youtube_project"]
        col1=db["channel_details"]
        for com_data in col1.find({},{"_id":0,"comment_information":1}):
                for i in range(len(com_data['comment_information'])):
                        com_list.append(com_data['comment_information'][i])       

        df3=pd.DataFrame(com_list)


        for index,row in df3.iterrows():
                insert_query='''insert into comments(Comment_Id,
                                Video_Id,
                                Comment_Text,
                                Comment_Author,
                                Comment_Published
                                )
                                                
                                values(%s,%s,%s,%s,%s)'''
                
                values=(row['Comment_Id'],
                        row['Video_Id'],
                        row['Comment_Text'],
                        row['Comment_Author'],
                        row['Comment_Published']
                        )
                try:        
                        mycursor.execute(insert_query,values)
                        mydb.commit()

                except:
                        print("channel values already inserted")



def tables():
    channels_table()
    playlists_table()
    videos_table()
    comments_table()

    return "tables created successfully"


def show_channels_table():

    ch_list =[]
    db=client["Youtube_project"]
    col1=db["channel_details"]
    for ch_data in col1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df = st.dataframe(ch_list)

    return df

def show_playlists_table():
    pl_list =[]
    db=client["Youtube_project"]
    col1=db["channel_details"]
    for pl_data in col1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data['playlist_information'])):
            pl_list.append(pl_data['playlist_information'][i])       

    df1=st.dataframe(pl_list)

    return df1

def show_videos_table():
        vid_list =[]
        db=client["Youtube_project"]
        col1=db["channel_details"]
        for vid_data in col1.find({},{"_id":0,"video_information":1}):
                for i in range(len(vid_data['video_information'])):
                        vid_list.append(vid_data['video_information'][i])       

        df2=st.dataframe(vid_list)

        return df2

def show_comments_table():
    com_list =[]
    db=client["Youtube_project"]
    col1=db["channel_details"]
    for com_data in col1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data['comment_information'])):
                com_list.append(com_data['comment_information'][i])       

    df3=st.dataframe(com_list)

    return df3

# streamlit code

with st.sidebar:
    st.title(":pink[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("skills take away")
    st.caption("python")
    st.caption("Data collection")
    st.caption("Mongo db")
    st.caption("API")
    st.caption("Postgre SQL")

channel_id = st.text_input("Enter the channel id")

if st.button("collect and store data"):
        ch_ids = []
        db=client["Youtube_project"]
        col1=db["channel_details"]
        for ch_data in col1.find({},{"_id":0,"channel_information":1}):
            ch_ids.append(ch_data["channel_information"]["Channel_Id"])
        
        if channel_id in ch_ids:
                st.success("Already exists")
        else:
                insert = channel_details

if st.button("Migrate to sql"):
        Table = tables()
        st.success(Table)
                

show_table = st.radio("select the table to view",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS"))

if show_table=="CHANNELS":
        show_channels_table()

elif show_table=="PLAYLISTS":
        show_playlists_table()

elif show_table=="VIDEOS":
        show_videos_table()

elif show_table=="COMMENTS":
        show_comments_table()


#SQL CONNECTION

mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="rihana",
                            database="Youtube_project",
                            port = 5432)
mycursor = mydb.cursor()


question = st.selectbox("select your question",("1. All the channels and videos name",
                                                "2. channels with most number of videos",
                                                "3. 10 most viwed videos",
                                                "4. comments in each videos",
                                                "5. videos with highest likes",
                                                "6. likes of all videos",
                                                "7. views of each channel",
                                                "8. videos published in the year of 2022",
                                                "9. average duration of all videos in each channel",
                                                "10. videos with highest number of comments"))

if question=="1. All the channels and videos name":
    query1 = '''select title as videos,channel_name as channelname from videos '''
    mycursor.execute(query1)
    mydb.commit()
    t1 = mycursor.fetchall()
    df = pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)


elif question=="2. channels with most number of videos":
    query2 = '''select channel_name as channelname,total_videos as no_videos from channel
                    order by total_videos desc'''
    mycursor.execute(query2)
    mydb.commit()
    t2 = mycursor.fetchall()
    df2 = pd.DataFrame(t2,columns=["channel name","No of videos"])
    st.write(df2)

elif question=="3. 10 most viwed videos":
    query3 = '''select views as views,channel_name as channel name,title as videotitle from videos
                    where views is not null order by views desc limit 10'''
    mycursor.execute(query3)
    mydb.commit()
    t3 = mycursor.fetchall()
    df3 = pd.DataFrame(t3,columns=["views","channel name","videotitle"])
    st.write(df3)

elif question=="4. comments in each videos":
    query4 = '''select comments as no_comments,title as videotitle from videos where comments is not null'''
    mycursor.execute(query4)
    mydb.commit()
    t4 = mycursor.fetchall()
    df4 = pd.DataFrame(t4,columns=["no of comments","videotitle"])
    st.write(df4)

elif question=="5. videos with highest likes":
    query5 = '''select title as videotitle,channel_name as channelname,likes as likecount
                    from videos where likes is not null order by likes desc'''
    mycursor.execute(query5)
    mydb.commit()
    t5 = mycursor.fetchall()
    df5 = pd.DataFrame(t5,columns=["videotitle","channelname","likescount"])
    st.write(df5)

elif question=="6. likes of all videos":
    query6 = '''select likes as likecount,title as videotitle from videos'''
    mycursor.execute(query6)
    mydb.commit()
    t6 = mycursor.fetchall()
    df6 = pd.DataFrame(t6,columns=["likecount","videotitle"])
    st.write(df6)

elif question=="7. views of each channel":
    query7 = '''select channel_name as channelname,views as totalviews from channel'''
    mycursor.execute(query7)
    mydb.commit()
    t7 = mycursor.fetchall()
    df7 = pd.DataFrame(t7,columns=["channel name","totalviews"])
    st.write(df7)

elif question=="8. videos published in the year of 2022":
    query8 = '''select title as video_title,published_date as videorelease,
                    channel_name as channelname from videos where extract(year from published_date)=2022'''
    mycursor.execute(query8)
    mydb.commit()
    t8 = mycursor.fetchall()
    df8 = pd.DataFrame(t8,columns=["videotitle","published_date","channelname"])
    st.write(df8)


elif question=="9. average duration of all videos in each channel":
    query9 = '''select channel_name as channelname,AVG(duration) as averageduration from videos 
                    group by channel_name'''
    mycursor.execute(query9)
    mydb.commit()
    t9 = mycursor.fetchall()
    df9 = pd.DataFrame(t9,columns=["channelname","averageduration"])
   
    T9=[]
    for index,row in df9.iterrows():
        channel_title = row["channelname"],
        average_duration = row["averageduration"]
        average_duration_str = str(average_duration)
        T9.append(dict(channeltitle=channel_title,avgduration=average_duration_str))
    df1 = pd.DataFrame(T9)
    st.write(df1)

elif question=="10. videos with highest number of comments":
    query10 = '''select title as videotitle,channel_name as channelname,comments as comments
                    from videos where comments is not null order by comments desc'''
    mycursor.execute(query10)
    mydb.commit()
    t10 = mycursor.fetchall()
    df10 = pd.DataFrame(t10,columns=["video title","channel name","comments"])
    st.write(df10)





