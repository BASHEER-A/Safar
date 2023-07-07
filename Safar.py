import sys
import os
import tkinter as tk
import urllib.request
import urllib.error
import time
import multiprocessing.dummy as multiprocessing
import string
from random import choice
import socket
from ctypes import c_int
import tempfile
from sys import argv
import threading
import requests
import keyboard
from tqdm import tqdm
import random
from tkinter.ttk import Progressbar
from multiprocessing.pool import ThreadPool
import math
from tkinter import messagebox
from tkinter import *
from tkinter import filedialog
from multiprocessing import Pool




# Create the main window
root = Tk()
root.geometry("400x200")

# Create the URL label and field
url_label = Label(root, text="URL:")
url_label.pack()
url_field = Entry(root, width=50)
url_field.pack()

# Create the threads label and field
threads_label = Label(root, text="Threads:")
threads_label.pack()
threads_field = Entry(root, width=50)
threads_field.pack()

# Create the path label and field
path_label = Label(root, text="Path:")
path_label.pack()
path_field = Entry(root, width=50)
path_field.pack()


def download_file(DownloadFile_Parall):
    # Get the values of the URL, threads, and path fields
    url = url_field.get()
    threads = int(threads_field.get())
    path = path_field.get()

    # If the path is empty, ask the user to select a path to save the file to
    if path == "":
        path = filedialog.asksaveasfilename()

    # Download the file using multiple processes
    DownloadFile_Parall(url, path=path, processes=threads)


# Create the download button
download_button = Button(root, text="Download", command=download_file)
download_button.pack()

# Run the main loop
root.mainloop()




random_value = random.randint(0, 10)

lock = threading.Lock()

url = 'https://example.com/api'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.8',
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
}
response = requests.get(url, headers=headers)


timeout = 30



def Is_ServerSupportHTTPRange(url, timeout=timeout):

    url = url.replace(' ', '%20')

    fullsize = get_filesize(url)
    if not fullsize:
        return False

    headers['Range'] = 'bytes=0-3'

    req = urllib.request.Request(url, headers=headers)
    urlObj = urllib.request.urlopen(req, timeout=timeout)

    meta = urlObj.info()
    filesize = int(meta.get_all("Content-Length")[0])

    urlObj.close()
    return (filesize != fullsize)


def get_filesize(url, timeout=timeout):

    url = url.replace(' ', '%20')
    try:

        u = urllib.request.urlopen(url)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(str(e))
        return 0
    meta = u.info()
    try:
        file_size = int(meta.get_all("Content-Length")[0])
    except IndexError:
        return 0

    return file_size


shared_bytes_var = multiprocessing.Value(c_int, 0)


def DownloadFile(url, path, startByte=0, endByte=None, ShowProgress=True):
    global shared_bytes_var, timeout
    url = url.replace(' ', '%20')
    headers = {}
    if endByte is not None:
        headers['Range'] = 'bytes=%d-%d' % (startByte,endByte)
    req = urllib.request.Request(url, headers=headers)

    try:
        urlObj = urllib.request.urlopen(req, timeout=timeout)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        if "HTTP Error 416" in str(e):

            print("Thread didn't got the file it was expecting. Retrying...")
            time.sleep(5)
            return DownloadFile(url, path, startByte, endByte, ShowProgress)
        else:
            raise e

#
    f = open(path, 'wb')
    meta = urlObj.info()
    try:
        filesize = int(meta.get_all("Content-Length")[0])
    except IndexError:
        print("Server did not send Content-Length.")
        ShowProgress=True

    filesize_dl = 0
    block_sz = 8192
    while True:
        try:
            buff = urlObj.read(block_sz)
        except (socket.timeout, socket.error, urllib.error.HTTPError) as e:
            shared_bytes_var.value -= filesize_dl
            raise e

        if not buff:
            break

        filesize_dl += len(buff)
        try:
            shared_bytes_var.value += len(buff)
        except AttributeError:
            pass
        f.write(buff)

        if ShowProgress:
            status = r"%.2f MB / %.2f MB %s [%3.2f%%]" % (filesize_dl / 1024.0 / 1024.0,
                    filesize / 1024.0 / 1024.0, progress_bar(1.0*filesize_dl/filesize),
                    filesize_dl * 100.0 / filesize)
            status += chr(8)*(len(status)+1)
            print(status, end="")
    if ShowProgress:
        print("\n", end="")

    f.close()
    return path

#######
shared_bytes_var = multiprocessing.Value(c_int, 0)


def DownloadFile_Parall(url, path=None, processes=16, minChunkFile=1024**2, nonBlocking=False):
    global shared_bytes_var
    shared_bytes_var.value = 0
    url = url.replace(' ', '%20')


    if not path:
        path = get_rand_filename(os.environ['temp'])
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
    if os.path.isdir(path):
        filename = url.split('/')[-1]
        path = os.path.join(path, filename)
    print(" [+] Downloading to "+ path+"...")

    try:
        global response
        response = requests.get(url, headers=headers, stream=True)
        meta = response.headers
        filesize = int(meta.get('content-length'))
    except:
        print(" [-] Connection error!!! Please check your network or firewall block.")
        return 2

    if filesize//processes > minChunkFile and Is_ServerSupportHTTPRange(url):
        args = []
        pos = 0
        chunk = filesize//processes
        for i in range(processes):
            startByte = pos
            endByte = pos + chunk
            if endByte > filesize-1:
                endByte = filesize-1
            args.append([url, path+".%.3d" % i, startByte, endByte, False])
            pos += chunk+1
    else:
        args = [[url, path+".000", None, None, False]]

    print(" [+] Running "+str(processes)+" processes...")
    pool = multiprocessing.Pool(processes, initializer=_initProcess, initargs=(shared_bytes_var,))
    mapObj = pool.map_async(lambda x: DownloadFile(*x) , args)
    if nonBlocking:
        return mapObj, pool

    # create the progress bar
    with tqdm(total=filesize, unit='B', unit_scale=True, unit_divisor=1024) as progress_bar:
        while not mapObj.ready():
            progress_bar.update(shared_bytes_var.value - progress_bar.n)
            status = r"%.2f MB / %.2f MB %s [%3.2f%%]" % (shared_bytes_var.value / 1024.0 / 1024.0,
                    filesize / 1024.0 / 1024.0, progress_bar,
                    shared_bytes_var.value * 100.0 / filesize)
            status = status + chr(8)*(len(status)+1)
            tqdm.write(status, end="")
            time.sleep(0.1)


    file_parts = mapObj.get()
    pool.terminate()
    pool.join()
    print(" [+] Combining file..."+" "*30)
    combine_files(file_parts, path)
    # check sum
    if filesize == int(os.path.getsize(path)):
        print("[+] File is OK. Have fun!")
    else:
        print("[-] File is missing some byte...")

def combine_files(parts, path):
    with open(path,'wb') as output:
        for part in parts:
            with open(part,'rb') as f:
                output.writelines(f.readlines())
            os.remove(part)




#def progress_bar(progress, length=20):
  #  length -= 2 #
   # return "[" + "#"*int(progress*length) + "-"*(length-int(progress*length)) + "]"


def get_rand_filename(dir_=os.getcwd()):
    "Function returns a non-existent random filename."
    return tempfile.mkstemp('.tmp', '', dir_)[1]

def _initProcess(x):
    global shared_bytes_var
    shared_bytes_var = x


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-u", "--url",help="download link")
    parser.add_argument("-f", "--file",help="download links in a file")
    parser.add_argument("-s", "--timeout",metavar='n', type=int, default=30, help="set timeout (default is 30s)")
    parser.add_argument("-t", "--thread",metavar='n' ,type=int, default=16,help="set threads [8,16,32,64...](default is 16)")
    parser.add_argument("-p", "--path", help="set download path")  # هنا يتم إضافة الخيار الجديد
    args = parser.parse_args()
    global timeout
    timeout = args.timeout
    print ("\n [+] Set timeout to",timeout,'seconds')
    if args.url:
        DownloadFile_Parall(args.url, args.path, args.thread)
    elif args.file:
        with open(args.file, 'r') as f:
            links = f.readlines()
        for link in links:
            DownloadFile_Parall(link.strip(), args.path, args.thread)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()




