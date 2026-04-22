
# CustomTkinter GUI wrapper for yt-dlp
import customtkinter as ctk
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")  # We'll override colors manually


class YTDLPDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader (yt-dlp Wrapper)")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg="#000000")

        # Color scheme
        self.red = "#1AABFF"  
        self.black = "#000000"
        self.font = ("Segoe UI", 13)
        self.font_bold = ("Segoe UI", 15, "bold")

        # Variables
        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.resolution_var = tk.StringVar(value="1080p")
        self.audio_var = tk.StringVar(value="None")
        self.video_format_var = tk.StringVar(value="mp4")

        # Widgets
        self.create_widgets()

    def create_widgets(self):
        # URL input
        self.url_label = ctk.CTkLabel(self, text="YouTube URL:", font=self.font_bold, text_color=self.red)
        self.url_label.pack(pady=(20, 5))
        self.url_entry = ctk.CTkEntry(self, textvariable=self.url_var, width=400, font=self.font, fg_color=self.black, text_color=self.red, border_color=self.red)
        self.url_entry.pack(pady=5)

        # Folder selection
        self.folder_frame = ctk.CTkFrame(self, fg_color=self.black)
        self.folder_frame.pack(pady=10, fill="x", padx=40)
        self.folder_label = ctk.CTkLabel(self.folder_frame, text="Save Folder:", font=self.font, text_color=self.red)
        self.folder_label.pack(side="left", padx=(10, 5))
        self.folder_entry = ctk.CTkEntry(self.folder_frame, textvariable=self.folder_var, width=250, font=self.font, fg_color=self.black, text_color=self.red, border_color=self.red)
        self.folder_entry.pack(side="left", padx=5)
        self.browse_btn = ctk.CTkButton(self.folder_frame, text="Browse", command=self.browse_folder, fg_color=self.red, text_color=self.black, font=self.font_bold)
        self.browse_btn.pack(side="left", padx=5)

        # Dropdowns
        self.options_frame = ctk.CTkFrame(self, fg_color=self.black)
        self.options_frame.pack(pady=10, fill="x", padx=40)
        self.res_label = ctk.CTkLabel(self.options_frame, text="Video Resolution:", font=self.font, text_color=self.red)
        self.res_label.pack(side="left", padx=(10, 5))
        self.res_dropdown = ctk.CTkOptionMenu(self.options_frame, variable=self.resolution_var, values=["1440p", "1080p", "720p", "480p"], fg_color=self.red, button_color=self.red, button_hover_color="#B20000", text_color=self.black, font=self.font)
        self.res_dropdown.pack(side="left", padx=5)
        self.audio_label = ctk.CTkLabel(self.options_frame, text="Audio Format:", font=self.font, text_color=self.red)
        self.audio_label.pack(side="left", padx=(20, 5))
        self.audio_dropdown = ctk.CTkOptionMenu(self.options_frame, variable=self.audio_var, values=["None", "mp3", "m4a", "wav"], fg_color=self.red, button_color=self.red, button_hover_color="#B20000", text_color=self.black, font=self.font)
        self.audio_dropdown.pack(side="left", padx=5)

        # Video format dropdown
        self.video_format_label = ctk.CTkLabel(self.options_frame, text="Video Format:", font=self.font, text_color=self.red)
        self.video_format_label.pack(side="left", padx=(20, 5))
        self.video_format_dropdown = ctk.CTkOptionMenu(self.options_frame, variable=self.video_format_var, values=["mp4", "mkv", "webm", "mov", "avi", "flv"], fg_color=self.red, button_color=self.red, button_hover_color="#B20000", text_color=self.black, font=self.font)
        self.video_format_dropdown.pack(side="left", padx=5)

        # Start Download button
        self.download_btn = ctk.CTkButton(self, text="Start Download", command=self.start_download, width=400, height=40, fg_color=self.red, text_color=self.black, font=self.font_bold)
        self.download_btn.pack(pady=(20, 10))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, width=400, height=20, fg_color=self.black, progress_color=self.red)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 5))

        # Status label below progress bar
        self.status_label = ctk.CTkLabel(self, text="Ready", wraplength=400, font=self.font, text_color=self.red)
        self.status_label.pack(pady=(0, 10))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)

    def start_download(self):
        url = self.url_var.get().strip()
        folder = self.folder_var.get().strip()
        resolution = self.resolution_var.get()
        audio_format = self.audio_var.get()
        video_format = self.video_format_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        if not folder:
            messagebox.showerror("Error", "Please select a folder to save the video.")
            return

        self.status_label.configure(text="Downloading...")
        self.download_btn.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Run download in a separate thread to prevent GUI freezing
        threading.Thread(target=self.run_download, args=(url, folder, resolution, audio_format, video_format), daemon=True).start()

    def run_download(self, url, folder, resolution, audio_format, video_format):
        height = resolution.replace("p", "")

        ydl_opts = {
            'outtmpl': f'{folder}/%(title)s.%(ext)s',
            'noplaylist': True,
            'progress_hooks': [self.my_hook],
            'no_warnings': True,
            'quiet': True,
            'retries': 3,
            'fragment_retries': 3,
        }

        if audio_format and audio_format != "None":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = (
                f'bestvideo[height<={height}][ext={video_format}]+bestaudio/'
                f'bestvideo[height<={height}]+bestaudio/best'
            )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self.status_label.configure(text="Download complete!"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"Error: {e}"))
        finally:
            self.after(0, lambda: self.download_btn.configure(state="normal"))

    def my_hook(self, d):
        if d['status'] == 'downloading':
            percent = 0.0
            if d.get('_percent_str'):
                try:
                    percent = float(d['_percent_str'].replace('%','').strip()) / 100.0
                except Exception:
                    percent = 0.0
            # Update UI in main thread
            self.after(0, lambda: self.progress_bar.set(percent))
            self.after(0, lambda: self.status_label.configure(text=f"Downloading... {d.get('_percent_str', '0%')} (ETA: {d.get('_eta_str','?')})"))
        elif d['status'] == 'finished':
            self.after(0, lambda: self.progress_bar.set(1))
            self.after(0, lambda: self.status_label.configure(text="Processing..."))
        elif d['status'] == 'error':
            self.after(0, lambda: self.status_label.configure(text="Error during download"))

if __name__ == "__main__":
    app = YTDLPDownloader()
    app.mainloop()