import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD

AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma', '.aiff', '.alac', '.ape', '.opus', '.ra', '.rm', '.wv', '.tta', '.dts', '.ac3', '.amr', '.gsm', '.voc', '.mpc')

def split_audio(input_file, chunk_length_minutes, output_format='mp3', progress_callback=None, cancel_event=None, normalize=False, output_folder=None):
    """Splits an audio file into equal-length chunks.

    Args:
        input_file (str): Path to the input audio file.
        chunk_length_minutes (int): Desired length of each chunk in minutes.
        output_format (str, optional): Output format (default: 'mp3').
        progress_callback (function, optional): Callback function to update progress.
        cancel_event (threading.Event, optional): Event to signal cancellation.
        normalize (bool, optional): Whether to normalize audio volume (default: False).
        output_folder (str, optional): Path to the output folder (default: None, uses current directory).

    Returns:
        bool: True if successful, False if an error occurred.
    """

    try:        
        chunk_length_seconds = chunk_length_minutes * 60

        # Get audio duration using FFprobe
        duration_cmd = ['ffprobe', '-i', input_file, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
        duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
        
        num_chunks = int(duration / chunk_length_seconds) + 1
        
        original_filename = os.path.splitext(os.path.basename(input_file))[0]

        # Split audio using FFmpeg
        for i in range(num_chunks):
            if cancel_event and cancel_event.is_set():
                return True

            start_time = i * chunk_length_seconds
            end_time = min((i + 1) * chunk_length_seconds, duration)
            output_file = f"{i+1:03d}_{original_filename}.{output_format}"
            if output_folder:
                output_file = os.path.join(output_folder, output_file)

            ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_file, '-ss', str(start_time), '-to', str(end_time)]
            
            if normalize:
                ffmpeg_cmd.extend(['-filter:a', 'speechnorm=e=12.5:r=0.0001:l=1'])
            
            ffmpeg_cmd.extend(['-c:a', 'libmp3lame', output_file])
            
            subprocess.run(ffmpeg_cmd, check=True)

            if progress_callback:
                progress = (i + 1) / num_chunks * 100
                progress_callback(progress)

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg execution: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

class DragDropGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Audio Splitter")
        self.master.geometry("400x420")
        self.master.configure(bg="#f0f0f0")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TButton", font=("Arial", 12), padding=10)
        self.style.configure("TEntry", font=("Arial", 12))
        self.style.configure("TCheckbutton",font=("Arial", 12))

        self.frame = ttk.Frame(self.master, padding="20 20 20 20", style="TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.label = ttk.Label(self.frame, text="Drag and drop audio file here\nor click 'Choose File'", anchor="center", justify="center")
        self.label.pack(pady=(20, 10))

        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", length=400, mode="determinate", style="TProgressbar")
        self.style.configure("TProgressbar", thickness=20)
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.pack_forget()  # Hide progress bar initially

        self.choose_file_button = ttk.Button(self.frame, text="Choose File", command=self.choose_file)
        self.choose_file_button.pack(pady=10)

        self.chunk_length_frame = ttk.Frame(self.frame)
        self.chunk_length_frame.pack(pady=10)

        self.chunk_length_label = ttk.Label(self.chunk_length_frame, text="Chunk length (minutes):")
        self.chunk_length_label.pack(side=tk.LEFT, padx=(0, 10))

        self.chunk_length_var = tk.StringVar()
        self.chunk_length_var.set("10")  # Default to 10 minutes
        self.chunk_length_entry = ttk.Entry(self.chunk_length_frame, width=10, textvariable=self.chunk_length_var, validate="key", validatecommand=(self.master.register(self.validate_number), '%P'))
        self.chunk_length_entry.pack(side=tk.LEFT)

        self.normalize_var = tk.BooleanVar()
        self.normalize_checkbox = ttk.Checkbutton(self.frame, text="Normalize audio", variable=self.normalize_var)
        self.normalize_checkbox.pack(pady=10)

        self.output_folder_frame = ttk.Frame(self.frame)
        self.output_folder_frame.pack(pady=10)

        self.output_folder_label = ttk.Label(self.output_folder_frame, text="Output folder:")
        self.output_folder_label.pack(side=tk.LEFT, padx=(0, 10))

        self.output_folder_var = tk.StringVar()
        self.output_folder_var.set(os.getcwd())  # Default to current directory
        self.output_folder_entry = ttk.Entry(self.output_folder_frame, width=30, textvariable=self.output_folder_var)
        self.output_folder_entry.pack(side=tk.LEFT)

        self.choose_output_folder_button = ttk.Button(self.output_folder_frame, text="...", command=self.choose_output_folder, width=3)
        self.choose_output_folder_button.pack(side=tk.LEFT, padx=(5, 0))

        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(pady=20)

        self.start_button = ttk.Button(self.button_frame, text="Split!", command=self.start_processing, state="disabled")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.cancel_processing)
        self.cancel_button.pack(side=tk.LEFT)
        self.cancel_button.pack_forget()  # Hide cancel button initially

        self.master.drop_target_register(DND_FILES)
        self.master.dnd_bind('<<Drop>>', self.drop)

        self.file_path = None
        self.cancel_event = None

    def validate_number(self, value):
        return value.isdigit() or value == ""

    def drop(self, event):
        self.file_path = event.data
        if self.file_path.startswith('{'):
            self.file_path = self.file_path[1:-1]        
        
        if not self.file_path.lower().endswith(AUDIO_EXTENSIONS):
            messagebox.showerror("Error", "The dropped file is not a supported audio file.")
            self.file_path = None
            return

        self.update_file_label()

    def choose_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Audio Files", " ".join(f"*{ext}" for ext in AUDIO_EXTENSIONS))])
        if self.file_path:
            self.update_file_label()

    def choose_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_var.set(folder)

    def update_file_label(self):
        self.label.config(text=f"File ready: {os.path.basename(self.file_path)}")
        self.start_button.config(state="normal")

    def start_processing(self):
        if not self.file_path:
            return
        chunk_length_minutes = int(self.chunk_length_entry.get())
        normalize = self.normalize_var.get()
        output_folder = self.output_folder_var.get()
        self.progress_bar["value"] = 0
        self.label.config(text="Processing...", foreground="black")
        self.start_button.pack_forget()
        self.cancel_button.pack(side=tk.LEFT)
        self.progress_bar.pack()  # Show progress bar
        self.master.update()
        
        import threading
        self.cancel_event = threading.Event()
        
        def process_thread():
            try:
                success = split_audio(self.file_path, chunk_length_minutes, progress_callback=self.update_progress, cancel_event=self.cancel_event, normalize=normalize, output_folder=output_folder)
                if not self.cancel_event.is_set():
                    if success:
                        self.label.config(text=f"Processing complete:\n{os.path.basename(self.file_path)}", foreground="green")
            except Exception as e:
                self.label.config(text="Error occurred during processing", foreground="red")
                messagebox.showerror("Error", f"An error occurred while processing the audio file: {str(e)}")
            finally:
                self.cancel_button.pack_forget()
                self.start_button.pack(side=tk.LEFT, padx=(0, 10))
                self.progress_bar.pack_forget()  
        
        threading.Thread(target=process_thread).start()

    def cancel_processing(self):
        if self.cancel_event:
            self.cancel_event.set()
            self.label.config(text="Processing cancelled")
            self.progress_bar["value"] = 0
            self.progress_bar.pack_forget()

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.master.update()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    gui = DragDropGUI(root)
    root.mainloop()