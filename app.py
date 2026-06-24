# pyrefly: ignore [missing-import]
import customtkinter as ctk
from tkinter import filedialog, messagebox
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk
import os
import webbrowser
import threading
import pyperclip
# pyrefly: ignore [missing-import]
import pygame
import time
# pyrefly: ignore [missing-import]
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt

from database import init_db, add_scan, get_all_scans, export_to_csv, get_scan_stats_by_type, get_scan_stats_by_date
from scanner import scan_image, draw_scan_results, parse_scanned_data
from generator import generate_qr

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart QR Code & Barcode Scanner Pro")
        self.geometry("1000x750")
        
        # Initialize Database
        init_db()
        
        # Initialize Audio
        try:
            pygame.mixer.init()
        except (NotImplementedError, Exception) as e:
            print(f"Warning: Audio mixer unavailable ({e}). Falling back to alternate methods.")

        self.cap = None
        self.is_streaming = False
        self.is_paused = False
        self.last_parsed_data = None
        self.recent_scans = {} # For debounce in batch mode

        self.create_widgets()

    def create_widgets(self):
        # Top-level tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_scanner = self.tabview.add("Scanner")
        self.tab_generator = self.tabview.add("Generator")
        self.tab_analytics = self.tabview.add("Analytics")
        
        self.setup_scanner_tab()
        self.setup_generator_tab()
        self.setup_analytics_tab()

    def setup_scanner_tab(self):
        # Layout for Scanner Tab
        self.left_frame = ctk.CTkFrame(self.tab_scanner, width=250)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self.tab_scanner)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Controls (Left Frame)
        ctk.CTkLabel(self.left_frame, text="Controls", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        self.btn_start = ctk.CTkButton(self.left_frame, text="Start Webcam", command=self.start_webcam)
        self.btn_start.pack(fill="x", padx=10, pady=5)

        self.btn_stop = ctk.CTkButton(self.left_frame, text="Stop Webcam", command=self.stop_webcam, state="disabled")
        self.btn_stop.pack(fill="x", padx=10, pady=5)

        self.btn_upload = ctk.CTkButton(self.left_frame, text="Upload Image", command=self.upload_image)
        self.btn_upload.pack(fill="x", padx=10, pady=5)
        
        self.btn_resume = ctk.CTkButton(self.left_frame, text="Resume Scan", command=self.resume_scan, fg_color="#c87f0a", hover_color="#a06507", state="disabled")
        self.btn_resume.pack(fill="x", padx=10, pady=5)

        # Options
        self.enhance_var = ctk.BooleanVar(value=False)
        self.chk_enhance = ctk.CTkCheckBox(self.left_frame, text="Low-Light Enhance", variable=self.enhance_var)
        self.chk_enhance.pack(fill="x", padx=10, pady=15)
        
        self.batch_var = ctk.BooleanVar(value=False)
        self.chk_batch = ctk.CTkCheckBox(self.left_frame, text="Batch Mode (Continuous)", variable=self.batch_var)
        self.chk_batch.pack(fill="x", padx=10, pady=5)

        # Current Batch Session
        ctk.CTkLabel(self.left_frame, text="Current Session", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 0))
        self.batch_listbox = ctk.CTkTextbox(self.left_frame, height=80, wrap="none")
        self.batch_listbox.pack(fill="x", padx=10, pady=5)
        self.batch_listbox.configure(state="disabled")

        # Smart Actions Section
        ctk.CTkLabel(self.left_frame, text="Smart Action", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        
        self.btn_smart_action = ctk.CTkButton(self.left_frame, text="No Action", command=self.do_smart_action, state="disabled")
        self.btn_smart_action.pack(fill="x", padx=10, pady=5)
        
        self.btn_copy = ctk.CTkButton(self.left_frame, text="Copy to Clipboard", command=self.copy_data, state="disabled")
        self.btn_copy.pack(fill="x", padx=10, pady=5)

        # Database Section
        ctk.CTkLabel(self.left_frame, text="Database", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))

        self.btn_history = ctk.CTkButton(self.left_frame, text="View History", command=self.view_history)
        self.btn_history.pack(fill="x", padx=10, pady=5)

        self.btn_export = ctk.CTkButton(self.left_frame, text="Export to CSV", command=self.export_csv)
        self.btn_export.pack(fill="x", padx=10, pady=5)

        # Display (Right Frame)
        self.lbl_status = ctk.CTkLabel(self.right_frame, text="Status: Ready", font=ctk.CTkFont(size=14), text_color="#28a745")
        self.lbl_status.pack(side="bottom", fill="x", pady=10)

        self.video_label = ctk.CTkLabel(self.right_frame, text="No Image/Video Feed", fg_color="black")
        self.video_label.pack(fill="both", expand=True)
        
    def setup_generator_tab(self):
        # Generator Layout
        self.gen_left = ctk.CTkFrame(self.tab_generator, width=300)
        self.gen_left.pack(side="left", fill="y", padx=10, pady=10)
        
        self.gen_right = ctk.CTkFrame(self.tab_generator)
        self.gen_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.gen_left, text="Enter Data", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.gen_textbox = ctk.CTkTextbox(self.gen_left, height=150)
        self.gen_textbox.pack(fill="x", padx=10, pady=10)
        
        self.btn_generate = ctk.CTkButton(self.gen_left, text="Generate QR Code", command=self.handle_generate)
        self.btn_generate.pack(fill="x", padx=10, pady=10)
        
        self.btn_save_qr = ctk.CTkButton(self.gen_left, text="Save QR Image", command=self.save_generated_qr, state="disabled")
        self.btn_save_qr.pack(fill="x", padx=10, pady=5)
        
        self.gen_preview_label = ctk.CTkLabel(self.gen_right, text="Preview will appear here")
        self.gen_preview_label.pack(expand=True)
        
        self.current_generated_img = None

    def play_beep(self):
        try:
            pygame.mixer.Sound("beep.wav").play()
        except Exception:
            os.system("aplay -q beep.wav 2>/dev/null")

    def start_webcam(self):
        if not self.is_streaming:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open webcam.")
                return
            
            self.is_streaming = True
            self.is_paused = False
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.btn_upload.configure(state="disabled")
            self.btn_resume.configure(state="disabled")
            self.lbl_status.configure(text="Status: Webcam Started", text_color="#17a2b8")
            self.update_frame()

    def stop_webcam(self):
        if self.is_streaming:
            self.is_streaming = False
            self.is_paused = False
            if self.cap:
                self.cap.release()
                self.cap = None
            self.video_label.configure(image='', text="Webcam Stopped", fg_color="black")
            
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.btn_upload.configure(state="normal")
            self.btn_resume.configure(state="disabled")
            self.lbl_status.configure(text="Status: Ready", text_color="#28a745")
            
    def resume_scan(self):
        if self.is_streaming and self.is_paused:
            self.is_paused = False
            self.btn_resume.configure(state="disabled")
            self.lbl_status.configure(text="Status: Resumed scanning...", text_color="#17a2b8")

    def update_frame(self):
        if self.is_streaming and self.cap:
            if not self.is_paused:
                ret, frame = self.cap.read()
                if ret:
                    # Scan the frame
                    results = scan_image(frame, enhance=self.enhance_var.get())
                    
                    # Draw results
                    frame = draw_scan_results(frame, results)
                    
                    # Handle database saving & actions
                    if len(results) > 0:
                        self.process_results(results)
                        if not self.batch_var.get():
                            self.is_paused = True
                            self.btn_resume.configure(state="normal")

                    # Convert to Tkinter format
                    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    img = Image.fromarray(cv2image)
                    img.thumbnail((640, 480), Image.Resampling.LANCZOS)
                    imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    
                    self.video_label.configure(image=imgtk, text='')
                    self.video_label.image = imgtk
                    
            # Schedule next frame
            self.after(30, self.update_frame)

    def upload_image(self):
        filepath = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*"))
        )
        if filepath:
            self.lbl_status.configure(text=f"Status: Scanning {os.path.basename(filepath)}...", text_color="#17a2b8")
            
            # Read image using cv2
            image = cv2.imread(filepath)
            if image is None:
                messagebox.showerror("Error", "Could not read the selected image.")
                self.lbl_status.configure(text="Status: Error loading image", text_color="red")
                return

            results = scan_image(image, enhance=self.enhance_var.get())
            image = draw_scan_results(image, results)
            
            if len(results) > 0:
                self.process_results(results)
                self.lbl_status.configure(text=f"Status: Found {len(results)} barcode(s).", text_color="#28a745")
            else:
                self.lbl_status.configure(text="Status: No barcodes found.", text_color="orange")

            # Display image
            cv2image = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            img.thumbnail((640, 480), Image.Resampling.LANCZOS)
            imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            
            self.video_label.configure(image=imgtk, text='')
            self.video_label.image = imgtk

    def process_results(self, results):
        current_time = time.time()
        for res in results:
            data = res['data']
            btype = res['type']
            
            # Debounce check
            if data in self.recent_scans:
                if current_time - self.recent_scans[data] < 3.0:
                    continue # Skip if scanned in last 3 seconds
            self.recent_scans[data] = current_time
            
            # Try adding to database
            added = add_scan(data, btype)
            
            if added or self.batch_var.get():
                if added:
                    print(f"New Scan Saved: {btype} - {data}")
                    self.lbl_status.configure(text=f"Status: Saved new {btype} code!", text_color="#28a745")
                else:
                    self.lbl_status.configure(text=f"Status: Scanned {btype} code (Duplicate)", text_color="#17a2b8")
                
                self.play_beep()
                
                # Update Batch Listbox
                if self.batch_var.get():
                    self.batch_listbox.configure(state="normal")
                    # Format for listbox: Time - Type - Data (truncated)
                    t_str = time.strftime("%H:%M:%S")
                    display_data = data if len(data) < 30 else data[:27] + "..."
                    self.batch_listbox.insert("end", f"[{t_str}] {btype}: {display_data}\n")
                    self.batch_listbox.see("end")
                    self.batch_listbox.configure(state="disabled")
            
            # Parse for smart actions
            parsed = parse_scanned_data(data)
            self.last_parsed_data = parsed
            
            # Enable copy
            self.btn_copy.configure(state="normal")
            
            # Setup Smart Action Button
            t = parsed['type']
            if t == 'URL':
                self.btn_smart_action.configure(text="Open URL in Browser", state="normal")
            elif t == 'WIFI':
                self.btn_smart_action.configure(text=f"Connect to {parsed.get('ssid','WiFi')}", state="normal")
            elif t == 'EMAIL':
                self.btn_smart_action.configure(text="Send Email", state="normal")
            elif t == 'PHONE':
                self.btn_smart_action.configure(text="Copy Phone Number", state="normal")
            else:
                self.btn_smart_action.configure(text="No Specific Action", state="disabled")

    def copy_data(self):
        if self.last_parsed_data:
            pyperclip.copy(self.last_parsed_data['action_data'])
            self.lbl_status.configure(text="Copied to clipboard!", text_color="#28a745")

    def do_smart_action(self):
        if not self.last_parsed_data: return
        
        parsed = self.last_parsed_data
        t = parsed['type']
        
        if t == 'URL':
            webbrowser.open(parsed['action_data'])
        elif t == 'WIFI':
            # Use nmcli to connect (Linux specific)
            ssid = parsed.get('ssid', '')
            pw = parsed.get('password', '')
            if ssid:
                cmd = f'nmcli device wifi connect "{ssid}" password "{pw}"'
                # run in background
                os.system(f"{cmd} &")
                self.lbl_status.configure(text=f"Attempting to connect to {ssid}...", text_color="#17a2b8")
            else:
                messagebox.showerror("Error", "No SSID found in WiFi QR.")
        elif t == 'EMAIL':
            webbrowser.open(f"mailto:{parsed['action_data']}")
        elif t == 'PHONE':
            pyperclip.copy(parsed['action_data'])
            self.lbl_status.configure(text="Phone copied to clipboard!", text_color="#28a745")

    def handle_generate(self):
        data = self.gen_textbox.get("1.0", "end-1c").strip()
        if not data:
            messagebox.showwarning("Empty", "Please enter some data to generate.")
            return
            
        img = generate_qr(data)
        self.current_generated_img = img
        
        # Display
        preview_img = img.copy()
        preview_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        imgtk = ctk.CTkImage(light_image=preview_img, dark_image=preview_img, size=preview_img.size)
        self.gen_preview_label.configure(image=imgtk, text="")
        self.gen_preview_label.image = imgtk
        
        self.btn_save_qr.configure(state="normal")
        
    def save_generated_qr(self):
        if self.current_generated_img:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")],
                title="Save QR Code"
            )
            if filepath:
                self.current_generated_img.save(filepath)
                messagebox.showinfo("Success", f"Saved QR code to {os.path.basename(filepath)}")

    def view_history(self):
        import tkinter.ttk as ttk
        history_window = ctk.CTkToplevel(self)
        history_window.title("Scan History")
        history_window.geometry("700x400")

        # Treeview (using standard ttk as ctk doesn't have a Treeview yet)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        
        columns = ('id', 'type', 'data', 'timestamp')
        tree = ttk.Treeview(history_window, columns=columns, show='headings')
        
        tree.heading('id', text='ID')
        tree.heading('type', text='Type')
        tree.heading('data', text='Data')
        tree.heading('timestamp', text='Timestamp')

        tree.column('id', width=50)
        tree.column('type', width=100)
        tree.column('data', width=350)
        tree.column('timestamp', width=150)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def on_double_click(event):
            selection = tree.selection()
            if not selection: return
            item_id = selection[0]
            item = tree.item(item_id)
            data = str(item['values'][2])
            if data.startswith("http://") or data.startswith("https://"):
                webbrowser.open(data)
            else:
                pyperclip.copy(data)
                messagebox.showinfo("Copied", "Data copied to clipboard!")

        tree.bind("<Double-1>", on_double_click)

        # Load data
        scans = get_all_scans()
        for scan in scans:
            tree.insert('', 'end', values=(scan['id'], scan['scan_type'], scan['scan_data'], scan['timestamp']))

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Save CSV Report"
        )
        if filepath:
            try:
                export_to_csv(filepath)
                messagebox.showinfo("Success", f"History exported to {os.path.basename(filepath)}")
                self.lbl_status.configure(text=f"Status: Exported to {os.path.basename(filepath)}", text_color="#28a745")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    def setup_analytics_tab(self):
        self.analytics_frame = ctk.CTkFrame(self.tab_analytics)
        self.analytics_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.btn_refresh_analytics = ctk.CTkButton(self.analytics_frame, text="Refresh Analytics", command=self.refresh_analytics)
        self.btn_refresh_analytics.pack(pady=10)
        
        self.charts_frame = ctk.CTkFrame(self.analytics_frame, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True)
        
        self.canvas = None
        self.refresh_analytics()

    def refresh_analytics(self):
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
            
        stats_type = get_scan_stats_by_type()
        stats_date = get_scan_stats_by_date()
        
        if not stats_type and not stats_date:
            ctk.CTkLabel(self.charts_frame, text="No scan data available yet.", font=ctk.CTkFont(size=16)).pack(expand=True)
            return

        plt.style.use('dark_background')
        fig = plt.figure(figsize=(10, 4), facecolor='#2b2b2b')
        
        ax1 = fig.add_subplot(121, facecolor='#2b2b2b')
        if stats_type:
            labels = [row[0] for row in stats_type]
            sizes = [row[1] for row in stats_type]
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'color':"w"})
            ax1.set_title('Scans by Type', color='white')
            
        ax2 = fig.add_subplot(122, facecolor='#2b2b2b')
        if stats_date:
            dates = [row[0] for row in stats_date]
            counts = [row[1] for row in stats_date]
            ax2.bar(dates, counts, color='#1f538d')
            ax2.set_title('Scans over Time', color='white')
            ax2.tick_params(axis='x', rotation=45, colors='white')
            ax2.tick_params(axis='y', colors='white')
            for spine in ax2.spines.values():
                spine.set_color('white')
            
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def on_closing(self):
        self.stop_webcam()
        self.destroy()

if __name__ == "__main__":
    app = ScannerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
