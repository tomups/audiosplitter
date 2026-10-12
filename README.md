# Audio Splitter

Simple audio splitter: split any audio file into same-length chunks.

![image](https://github.com/user-attachments/assets/3607e176-f0f6-4069-9941-a21e82ad0ad8)

Uses ffmpeg under the hood, so make sure you have it installed and it's available in your path. 

To run from source on Windows or Linux, install Python with Tkinter support and
make sure both FFmpeg commands are in PATH (`ffmpeg.exe` and `ffprobe.exe` on
Windows; `ffmpeg` and `ffprobe` on Linux). In your Python virtual environment, run:

```sh
python -m pip install -r requirements.txt
python audiosplitter.py
```

The pinned `tkinterdnd2` version supports Tcl/Tk 8 and 9. Reinstall requirements
if upgrading an existing checkout. The packaged Windows executable includes
FFmpeg and FFprobe.

It can also normalize audio volume using the `speechnorm` filter.

I mostly use this to split audiobooks into chunks for listening while swimming. You can read more about it here: https://www.tomups.com/posts/swimming-and-audiobooks/
