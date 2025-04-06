#conding = utf-8

import os
import re
import json
import mutagen
import requests
from pprint import pprint
from urllib.parse import quote, urljoin

class Clawer:

    def __init__(self) -> None:
        '''初始化'''

        self.path = ""
        self.search_result_list = []
        self.update_config_info()

    def update_config_info(self) -> None:
        '''导入配置信息'''

        with open("config.json", "r+") as config_file:
            self.path = eval(config_file.read())["path"]

    def search_song(self, song_name:str = "青花瓷") -> None:
        '''搜索音乐'''

        search_url = f"https://kuwo.cn/search/searchMusicBykeyWord?vipver=1&client=kt&ft=music&cluster=0&strategy=2012&encoding=utf8&rformat=json&mobi=1&issubtitle=1&show_copyright_off=1&pn=0&rn=20&all={quote(song_name)}"
        search_response = requests.get(search_url).json()
        info_dict_list = search_response["abslist"]
        self.search_result_list = []
        for d_index, info_dict in enumerate(info_dict_list):
            songName = info_dict["SONGNAME"]
            singer = info_dict["ARTIST"]
            album = info_dict["ALBUM"]
            dc_targetid = info_dict["DC_TARGETID"]
            albumcover_url = urljoin("https://img4.kuwo.cn/star/albumcover/", 
                                     re.sub("120/{1}", "500/", info_dict["web_albumpic_short"], 1))
            search_result_dict = {"song_index":d_index,
                                  "song_name":songName,
                                  "singer":singer,
                                  "album":album,
                                  "dc_targetid":dc_targetid,
                                  "albumcover_url":albumcover_url}
            self.search_result_list.append(search_result_dict)

    def download_music(self, id:int, path:str, quality:int, albumcover_url:str) -> None:
        '''下载音乐'''

        api_url = "https://api.leafone.cn/api/kuwo"
        params = {"id":id, 
                  "type":quality
                  }
        info_dict = requests.get(url=api_url, params=params).json()

        song_data_url = info_dict["data"]["url"]
        song_data = requests.get(song_data_url, verify=False).content
        song_name = info_dict["data"]["title"]
        song_singer = info_dict["data"]["singer"]
        song_album = info_dict["data"]["album"]
        song_file_type = song_data_url.split(".")[-1]
        song_file_name = os.path.join(path, f"{song_name}-{song_singer}.{song_file_type}")
        song_lrc_file_name = os.path.join(path, f"{song_name}-{song_singer}.lrc")
        
        exist_content = albumcover_url[-3:]
        if (exist_content != 'er/'):
            song_albumcover_file_name = os.path.join(path, f"{song_name}-{song_singer}.{albumcover_url[-3:]}") # 注意，得做无效网址判断，不然因请求不到图片数据导致图片后缀错误，直接影响后文
            song_albumcover_data = requests.get(albumcover_url).content # 注意，得做无效网址判断，不然请求不到图片数据
            with open(song_albumcover_file_name, "wb") as sbf: # 注意，得做无效网址判断，不然因请求不到图片数据而报错
                sbf.write(song_albumcover_data)
        song_lrc = info_dict["data"]["lrc"]
        song_data = requests.get(song_data_url).content

        if not os.path.exists(path):
            os.mkdir(path)
        with open(song_lrc_file_name, "w", encoding="utf-8") as mlf:
            mlf.write(song_lrc)
        with open(song_file_name + "_raw", "wb") as mf:
            mf.write(song_data)
        if (exist_content != 'er/'):
            tagging_command = "ffmpeg -i " + "\"" + song_file_name + "_raw" + "\"" + " -i " + "\"" + song_albumcover_file_name + "\"" + \
                            " -map 0 -map 1 -c copy" + \
                            " -metadata title=" + "\"" + song_name + "\"" + \
                            " -metadata artist=" + "\"" + song_singer + "\"" + \
                            " -metadata album=" + "\"" + song_album + "\"" + \
                            " -metadata:s:v comment=\"Cover\"" + \
                            " -id3v2_version 3" + \
                            " -disposition:v attached_pic " + \
                            "\"" + song_file_name + "\"" + " -y" # 打标签命令，有封面图片
        else:
            tagging_command = "ffmpeg -i " + "\"" + song_file_name + "_raw" + "\"" + \
                            " -map 0 -c copy" + \
                            " -metadata title=" + "\"" + song_name + "\"" + \
                            " -metadata artist=" + "\"" + song_singer + "\"" + \
                            " -metadata album=" + "\"" + song_album + "\"" + \
                            " -id3v2_version 3 " + \
                            "\"" + song_file_name + "\"" + " -y" # 打标签命令，无封面图片
        print("line91: ", tagging_command)
        os.system(tagging_command) # 打标签
        os.system("del \"" + song_file_name + "\"_raw") # 删除缓存文件
        # music_file = mutagen.File(song_file_name) # 给歌曲打标签，但是不建议用mutagen这个库，对音乐文件是适配不是很好，会出现打不上的问题，建议用ffmpeg
        
        print("\n下载完成！\n歌名：{:}\n作者：{:}\n专辑：{:}\n文件保存位置：{:}\n".format(song_name, song_singer, song_album, os.path.abspath(song_file_name)))

    def download_albumcover(self, albumcover_url:str) -> None:
        '''下载歌曲封面'''

    def print_search_result_list(self) -> None:
        '''输出搜索结果'''

        for info_dict in self.search_result_list:
            song_index = info_dict["song_index"]
            song_name = info_dict["song_name"]
            song_singer = info_dict["singer"][0:20]+"..." if len(info_dict["singer"])>20 else info_dict["singer"]
            song_album = info_dict["album"]
            if not song_album:
                song_album = "未知"
            else:
                pass
            
            print("\n({:0>2d})歌名：{: <30s}\t\t\t歌手：{: <50s}\t\t\t专辑：{:}".format(
                song_index, 
                song_name, 
                song_singer, 
                song_album.strip("")))

    def input_song_index(self) -> int|bool:
        '''获取用户输入序号'''

        while True:
            song_index = input("\n>>> 输入歌曲序号（直接回车则重新搜索歌曲）：")
            if song_index:
                try:
                    song_index=int(song_index)
                except:
                    continue
                if song_index<0 or song_index>19:
                    print("超出范围")
                    continue
                else:
                    return song_index
            else:
                return False
    
    def input_quality(self) -> int|bool:
        '''获取用户输入音质序号'''
    
        while True:
            song_quality = input(">>> 输入音质（音质选项1-6，数字越高音质越高，直接回车则重新选择歌曲序号）：")
            if song_quality:
                try:
                    song_quality=int(song_quality)
                except:
                    continue
                if song_quality<1 or song_quality>6:
                    print("超出范围")
                    continue
                else:
                    return song_quality
            else:
                return False
            
    def update_config(self, **kvargs) -> None:
        '''更新配置文件'''

        config_dict = {}
        for key,value in kvargs.items():
            config_dict[key] = value
        with open("config.json", "w") as config_file:
            config_file.write(json.dumps(config_dict))
            
    def input_save_path(self) -> str:
        '''获取用户输入路径'''

        path = input(">>> 输入保存路径（直接回车则使用默认路径，输入reset则设置默认路径）：")
        if not path:
            print("文件保存路径:{:}\n".format(os.path.abspath(self.path)))
            return self.path
        else:
            if path == "reset":
                while True:
                    path = input(">>> 输入默认保存路径：")
                    if not path:
                        continue
                    else:
                        pattern = r"[\/:*?<>|]*"
                        self.path = re.sub(pattern=pattern, repl="", string = path)
                        config_dict = {
                            "path":self.path
                        }
                        self.update_config(**config_dict)
                        print(self.path)
                        return self.path
            else:
                pattern = r"[\/:*?<>|]*"
                path = re.sub(pattern=pattern, repl="", string = path)
                print(path)
                return path

    def run(self) -> None:
        '''运行下载逻辑'''

        print(
        """
         _  __                        __  __              _         _____                          _                    _             
        | |/ /                       |  \/  |            (_)       |  __ \                        | |                  | |            
        | ' / _   _ __      __ ___   | \  / | _   _  ___  _   ___  | |  | |  ___ __      __ _ __  | |  ___    __ _   __| |  ___  _ __ 
        |  < | | | |\ \ /\ / // _ \  | |\/| || | | |/ __|| | / __| | |  | | / _ \\ \ /\ / /| '_ \ | | / _ \  / _` | / _` | / _ \| '__|
        | . \| |_| | \ V  V /| (_) | | |  | || |_| |\__ \| || (__  | |__| || (_) |\ V  V / | | | || || (_) || (_| || (_| ||  __/| |   
        |_|\_\\__,_|  \_/\_/  \___/  |_|  |_| \__,_||___/|_| \___| |_____/  \___/  \_/\_/  |_| |_||_| \___/  \__,_| \__,_| \___||_|   
                                                                                                                                    
                                                                                                                                    
        Made by g2c2 DJ, 有问题请联系
        """)

        while True:
            song_name = input(">>> 输入歌曲名字：")
            if song_name:
                self.search_song(song_name=song_name)
                self.print_search_result_list()
                while True:
                    song_index = self.input_song_index()
                    if type(song_index) != int:
                        break
                    else:
                        song_quality = self.input_quality()
                        if not song_quality:
                            continue
                        else:
                            break
                if type(song_index) != int:
                    continue
                else:
                    path = self.input_save_path()
                    for items in self.search_result_list:
                        if items["song_index"] == song_index:
                            id = items["dc_targetid"]
                            albumcover_url = items["albumcover_url"]
                            self.download_music(id=id, path=path, quality=song_quality, albumcover_url=albumcover_url)
                            break
                        else:
                            pass
            else:
                continue
                
if __name__ == "__main__":
    clawer = Clawer()
    # clawer.download_music(337298328, r"D:\User\Kechuangbu\Desktop\dist\music", 6, r"https://img3.kuwo.cn/star/albumcover/500/s3s36/63/1182680406.jpg")
    clawer.run()