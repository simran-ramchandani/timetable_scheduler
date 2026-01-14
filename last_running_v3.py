import tkinter as tk
import pandas as pd
import numpy as np
from tkinter import ttk, filedialog, messagebox, Toplevel
import csv
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class TimetableScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("College Timetable Scheduler")
        self.root.geometry("1600x900")
        self.root.configure(bg="#f5f7fa")
        
        # Data storage
        self.courses = []
        self.teachers = []
        self.teacher_availability = {}
        self.classrooms = []
        self.subject_details = {}
        self.schedule = []
        
        # Valid departments
        self.departments = ["Computer", "BSH", "EXTC", "EXTC/MTRX", "AI", "MTRX", 
                           "Data Science", "IT", "Mech"]
        
        # Time slots (8 AM to 6 PM, 1-hour slots)
        self.time_slots = self.generate_time_slots()
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        # Current view type
        self.current_view = tk.StringVar(value="master")
        self.selected_entity = tk.StringVar()
        
        self.setup_styles()
        self.setup_ui()
    
    def setup_styles(self):
        """Configure custom ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Custom.TCombobox', 
                       fieldbackground='white',
                       background='#ecf0f1',
                       borderwidth=1,
                       relief='flat')
        
        style.configure('Accent.TButton',
                       background='#402525',
                       foreground='black',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Comic Sans', 10, 'bold'))
    
    def generate_time_slots(self):
        slots = []
        start = datetime.strptime("08:00", "%H:%M")
        end = datetime.strptime("18:00", "%H:%M")
        current = start
        
        while current < end:
            next_time = current + timedelta(hours=1)
            slots.append(f"{current.strftime('%H:%M')}-{next_time.strftime('%H:%M')}")
            current = next_time
        
        return slots
    
    def expand_time_range(self, time_range):
        """Convert a time range like '08:00-10:00' to individual slots ['08:00-09:00', '09:00-10:00']"""
        try:
            start_str, end_str = time_range.split('-')
            start = datetime.strptime(start_str.strip(), "%H:%M")
            end = datetime.strptime(end_str.strip(), "%H:%M")
            
            slots = []
            current = start
            while current < end:
                next_time = current + timedelta(hours=1)
                slot = f"{current.strftime('%H:%M')}-{next_time.strftime('%H:%M')}"
                if slot in self.time_slots:
                    slots.append(slot)
                current = next_time
            
            return slots
        except:
            return []
    
    def create_modern_button(self, parent, text, command, bg_color, **kwargs):
        """Create a modern flat button with hover effects"""
        btn = tk.Button(parent, text=text, command=command, bg=bg_color, fg="black",
                       font=("Comic Sans", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                       borderwidth=0, padx=15, pady=12, **kwargs)
        
        def on_enter(e):
            btn['bg'] = self.darken_color(bg_color)
        
        def on_leave(e):
            btn['bg'] = bg_color
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def darken_color(self, hex_color, factor=0.85):
        """Darken a hex color by a factor"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'
    
    def show_csv_help(self):
        """Display CSV format help window"""
        help_window = Toplevel(self.root)
        help_window.title("CSV Format Guide")
        help_window.geometry("800x700")
        help_window.configure(bg="#f8fafc")
        help_window.resizable(True, True)
        
        # Make it stay on top
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Modern color scheme
        colors = {
            "primary": "#2c3e50",
            "secondary": "#64748b",
            "accent": "#f59e0b",
            "background": "#f8fafc",
            "card": "#ffffff",
            "text": "#1e293b",
            "border": "#e2e8f0"
        }
        
        # Header with modern styling
        header_frame = tk.Frame(help_window, bg=colors["primary"], height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        header = tk.Label(header_frame, text="CSV Format Guide", 
                        font=("Segoe UI", 20, "bold"), bg=colors["primary"], 
                        fg="white", pady=20)
        header.pack(expand=True)
        
        # Main container with padding
        main_container = tk.Frame(help_window, bg=colors["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for tabbed interface
        style = ttk.Style()
        style.configure("Modern.TNotebook", background=colors["background"], borderwidth=0)
        style.configure("Modern.TNotebook.Tab", 
                    font=("Segoe UI", 10, "bold"),
                    padding=[15, 5],
                    background=colors["card"],
                    borderwidth=1)
        style.map("Modern.TNotebook.Tab", 
                background=[("selected", colors["primary"])],
                foreground=[("selected", "white")])
        
        notebook = ttk.Notebook(main_container, style="Modern.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Define CSV formats with better organization
        csv_formats = {
            "Courses": {
                "description": "Define academic courses and their structure",
                "columns": ["name", "semester", "no_of_batches", "capacity", "courses"],
                "example": """name,semester,no_of_batches,capacity,courses
    SE Computer,4,2,60,OS | DBMS | CN | SE
    TE IT,5,1,30,AI | ML | Cloud Computing""",
                "notes": ["• Separate subjects with pipe (|) character", "• Capacity refers to maximum students per batch"]
            },
            "Subject Details": {
                "description": "Specify subject requirements and hours",
                "columns": ["subject", "department", "lecture_hours", "lab_hours", "tutorial_hours"],
                "example": """subject,department,lecture_hours,lab_hours,tutorial_hours
    OS,Computer,3,2,1
    DBMS,Computer,3,4,0
    AI,IT,4,2,1""",
                "notes": ["• Hours are per week", "• Departments must be consistent across files"]
            },
            "Teachers": {
                "description": "List teachers and their assigned subjects",
                "columns": ["teacher_name", "subjects"],
                "example": """teacher_name,subjects
    Dr. Smith,OS,DBMS
    Prof. Jones,CN,AI""",
                "notes": ["• Separate subjects with commas", "• Teacher names should be unique"]
            },
            "Teacher Availability": {
                "description": "Define teacher schedules and availability",
                "columns": ["teacher_name", "type of faculty", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "example": """teacher_name,type of faculty,Monday,Tuesday,Wednesday,Thursday,Friday,Saturday
    Dr. Smith,permanent,08:00-12:00;14:00-17:00,08:00-13:00,NA,09:00-16:00,08:00-12:00,NA
    Prof. Jones,visiting,09:00-13:00,NA,10:00-15:00,NA,09:00-12:00,NA""",
                "notes": [
                    "• Use semicolon (;) to separate multiple time ranges",
                    "• Use 'NA' for unavailable days", 
                    "• Faculty types: permanent, visiting",
                    "• Time format: HH:MM-HH:MM (24-hour)"
                ]
            },
            "Classrooms": {
                "description": "Define classroom types and capacities",
                "columns": ["class_type", "room", "department", "capacity"],
                "example": """class_type,room,department,capacity
    CR,Room 101,Computer,60
    CL,Lab A1,Computer,30
    TR,Tutorial Room 1,IT,25
    LH,Lecture Hall 1,BSH,120""",
                "notes": [
                    "• Class types: CR (Classroom), CL (Computer Lab), TR (Tutorial Room), LH (Lecture Hall)",
                    "• Departments must match subject details"
                ]
            }
        }
        
        # Create tabs for each CSV type
        for tab_name, tab_data in csv_formats.items():
            tab_frame = tk.Frame(notebook, bg=colors["card"], padx=20, pady=20)
            notebook.add(tab_frame, text=f"  {tab_name}  ")
            
            # Description
            desc_label = tk.Label(tab_frame, text=tab_data["description"], 
                                font=("Segoe UI", 11, "bold"), bg=colors["card"], 
                                fg=colors["text"], wraplength=700, justify=tk.LEFT)
            desc_label.pack(anchor=tk.W, pady=(0, 15))
            
            # Required columns
            cols_frame = tk.LabelFrame(tab_frame, text="Required Columns ", 
                                    font=("Segoe UI", 10, "bold"), bg=colors["card"],
                                    fg=colors["primary"], padx=15, pady=10)
            cols_frame.pack(fill=tk.X, pady=(0, 15))
            
            columns_text = ", ".join(tab_data["columns"])
            cols_label = tk.Label(cols_frame, text=columns_text, font=("Consolas", 9),
                                bg=colors["card"], fg=colors["secondary"], justify=tk.LEFT)
            cols_label.pack(anchor=tk.W)
            
            # Example section
            example_frame = tk.LabelFrame(tab_frame, text="Example ", 
                                        font=("Segoe UI", 10, "bold"), bg=colors["card"],
                                        fg=colors["accent"], padx=15, pady=10)
            example_frame.pack(fill=tk.X, pady=(0, 15))
            
            # CHANGED: Use WORD wrap instead of NONE and remove horizontal scrollbar
            example_text = tk.Text(example_frame, wrap=tk.WORD, font=("Consolas", 9), 
                                bg="#f8fafc", fg=colors["text"], height=6,
                                relief=tk.FLAT, borderwidth=1, padx=10, pady=10)
            example_text.insert(1.0, tab_data["example"])
            example_text.config(state=tk.DISABLED)
            example_text.pack(fill=tk.BOTH, expand=True)
            
            # Notes section
            if tab_data["notes"]:
                notes_frame = tk.LabelFrame(tab_frame, text="Important Notes ", 
                                        font=("Segoe UI", 10, "bold"), bg=colors["card"],
                                        fg="#10b981", padx=15, pady=10)
                notes_frame.pack(fill=tk.X, pady=(0, 10))
                
                for note in tab_data["notes"]:
                    note_label = tk.Label(notes_frame, text=note, font=("Segoe UI", 9),
                                        bg=colors["card"], fg=colors["secondary"], 
                                        justify=tk.LEFT, anchor=tk.W)
                    note_label.pack(anchor=tk.W, pady=2)
        
        # Footer with close button
        footer_frame = tk.Frame(main_container, bg=colors["background"])
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_btn = self.create_modern_button(footer_frame, "✓ Got It! Close Guide", 
                                            help_window.destroy, colors["primary"])
        close_btn.pack(pady=10, ipadx=20, ipady=8)
        
        # Add some helpful tips at the bottom
        tips_frame = tk.Frame(footer_frame, bg=colors["background"])
        tips_frame.pack(fill=tk.X, pady=(10, 0))
        
        tips_label = tk.Label(tips_frame, 
                            text="Tip: All CSV files should be saved with UTF-8 encoding and use comma separators",
                            font=("Segoe UI", 9, "italic"), bg=colors["background"], 
                            fg=colors["secondary"])
        tips_label.pack()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=90)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        accent_bar = tk.Frame(header_frame, bg="#402525", height=4)
        accent_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Title with help button
        title_container = tk.Frame(header_frame, bg="#2c3e50")
        title_container.pack(pady=25)
        
        title_label = tk.Label(title_container, text="College Timetable Scheduler",
                              font=("Comic Sans", 24, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(side=tk.LEFT)
        
        help_btn = tk.Button(title_container, text="?", command=self.show_csv_help,
                           bg="#3445db", fg="#000000", font=("Comic Sans", 12, "bold"),
                           relief=tk.FLAT, cursor="hand2", width=1, height=1,
                           borderwidth=0)
        help_btn.pack(side=tk.LEFT, padx=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg="#f5f7fa")
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Left panel
        left_panel = tk.Frame(main_container, bg="white", relief=tk.FLAT, bd=0, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 15), pady=0)
        left_panel.pack_propagate(False)
        
        shadow_frame = tk.Frame(main_container, bg="#d0d3d8", width=302)
        shadow_frame.place(x=-2, y=2, relheight=0.97)
        shadow_frame.lower()
        
        input_title = tk.Label(left_panel, text="Data Input", font=("Comic Sans", 17, "bold"),
                              bg="white", fg="#2c3e50", anchor="w")
        input_title.pack(pady=20, padx=20, fill=tk.X)
        
        self.create_file_input(left_panel, "Courses CSV", self.load_courses)
        self.create_file_input(left_panel, "Subject Details CSV", self.load_subject_details)
        self.create_file_input(left_panel, "Teachers CSV", self.load_teachers)
        self.create_file_input(left_panel, "Teacher Availability CSV", self.load_availability)
        self.create_file_input(left_panel, "Classrooms CSV", self.load_classrooms)
        
        # Status display
        status_frame = tk.Frame(left_panel, bg="#f8f9fa", relief=tk.FLAT, bd=0)
        status_frame.pack(fill=tk.BOTH, padx=20, pady=20)
        
        status_header = tk.Label(status_frame, text="Loaded Data", 
                                font=("Comic Sans", 11, "bold"), bg="#f8f9fa", fg="#2c3e50", anchor="w")
        status_header.pack(pady=(10, 5), padx=10, fill=tk.X)
        
        self.status_text = tk.Text(status_frame, height=6, width=30, font=("Comic Sans", 9),
                                  bg="white", fg="#2c3e50", relief=tk.FLAT, borderwidth=1,
                                  highlightthickness=1, highlightbackground="#e0e0e0")
        self.status_text.pack(padx=10, pady=(0, 10))
        
        # Generate button
        generate_frame = tk.Frame(left_panel, bg="white")
        generate_frame.pack(pady=15, padx=20, fill=tk.X)
        
        generate_btn = self.create_modern_button(generate_frame, "Generate Timetable",
                                                 self.generate_schedule, "#402525")
        generate_btn.pack(fill=tk.X)
        
        self.progress_label = tk.Label(generate_frame, text="", font=("Comic Sans", 9, "italic"),
                                      bg="white", fg="#7f8c8d")
        self.progress_label.pack(pady=(8, 0))
        
        # View selector
        view_frame = tk.Frame(left_panel, bg="#f8f9fa", relief=tk.FLAT, bd=0)
        view_frame.pack(fill=tk.BOTH, padx=20, pady=(0, 15))
        
        view_header = tk.Label(view_frame, text="View Timetable", 
                              font=("Comic Sans", 11, "bold"), bg="#f8f9fa", fg="#2c3e50", anchor="w")
        view_header.pack(pady=(10, 8), padx=10, fill=tk.X)
        
        radio_options = [
            ("Master Schedule", "master"),
            ("By Course", "course"),
            ("By Teacher", "teacher"),
            ("By Classroom", "classroom")
        ]
        
        for text, value in radio_options:
            rb = tk.Radiobutton(view_frame, text=text, variable=self.current_view,
                              value=value, bg="#f8f9fa", fg="#2c3e50", font=("Comic Sans", 10),
                              selectcolor="#402525", activebackground="#f8f9fa",
                              activeforeground="#2c3e50", cursor="hand2",
                              command=self.on_view_change)
            rb.pack(anchor=tk.W, padx=(10, 15), pady=2)
        
        # Entity selector
        self.entity_frame = tk.Frame(view_frame, bg="#f8f9fa")
        self.entity_frame.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        tk.Label(self.entity_frame, text="Select:", bg="#f8f9fa", fg="#5d6d7e",
                font=("Comic Sans", 9)).pack(anchor=tk.W, pady=(0, 5))
        
        self.entity_dropdown = ttk.Combobox(self.entity_frame, textvariable=self.selected_entity,
                                           state="readonly", width=25, font=("Comic Sans", 9),
                                           style='Custom.TCombobox')
        self.entity_dropdown.pack(fill=tk.X)
        self.entity_dropdown.bind("<<ComboboxSelected>>", lambda e: self.display_schedule())
        
        # Export buttons frame
        export_frame = tk.Frame(left_panel, bg="white")
        export_frame.pack(pady=(5, 10), padx=20, fill=tk.X)
        
        export_csv_btn = self.create_modern_button(export_frame, "Export as CSV",
                                                   self.export_csv, "#3498db")
        export_csv_btn.pack(fill=tk.X, pady=(0, 5))
        
        export_pdf_btn = self.create_modern_button(export_frame, "Export as PDF",
                                                   self.export_pdf, "#e74c3c")
        export_pdf_btn.pack(fill=tk.X)
        
        # Middle panel - Tools
        middle_panel = tk.Frame(main_container, bg="white", relief=tk.FLAT, bd=0, width=300)
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 15))
        middle_panel.pack_propagate(False)
        
        tools_title = tk.Label(middle_panel, text="Tools", font=("Comic Sans", 17, "bold"),
                              bg="white", fg="#2c3e50", anchor="w")
        tools_title.pack(pady=20, padx=20, fill=tk.X)
        
        # Find Empty Classrooms
        find_frame = tk.Frame(middle_panel, bg="#f8f9fa", relief=tk.FLAT, bd=0)
        find_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        find_header = tk.Label(find_frame, text="Find Empty Classrooms", 
                              font=("Comic Sans", 11, "bold"), bg="#f8f9fa", fg="#2c3e50", anchor="w")
        find_header.pack(pady=(10, 10), padx=10, fill=tk.X)
        
        tk.Label(find_frame, text="Day:", bg="#f8f9fa", fg="#5d6d7e",
                font=("Comic Sans", 9)).pack(anchor=tk.W, pady=(5, 3), padx=10)
        self.find_day = ttk.Combobox(find_frame, values=self.days, state="readonly", 
                                     width=25, font=("Comic Sans", 9), style='Custom.TCombobox')
        self.find_day.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        tk.Label(find_frame, text="Time:", bg="#f8f9fa", fg="#5d6d7e",
                font=("Comic Sans", 9)).pack(anchor=tk.W, pady=(0, 3), padx=10)
        self.find_time = ttk.Combobox(find_frame, values=self.time_slots, state="readonly", 
                                      width=25, font=("Comic Sans", 9), style='Custom.TCombobox')
        self.find_time.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        find_btn = self.create_modern_button(find_frame, "Search", self.find_empty_classrooms,
                                            "#9b59b6")
        find_btn.pack(fill=tk.X, pady=(5, 10), padx=10)
        
        self.empty_rooms_text = tk.Text(find_frame, height=4, fg="#2c3e50", font=("Comic Sans", 9),
                                       bg="white", relief=tk.FLAT, borderwidth=1,
                                       highlightthickness=1, highlightbackground="#e0e0e0")
        self.empty_rooms_text.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Add Extra Lecture
        add_frame = tk.Frame(middle_panel, bg="#f8f9fa", relief=tk.FLAT, bd=0)
        add_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        add_header = tk.Label(add_frame, text="Add Extra Lecture", 
                             font=("Comic Sans", 11, "bold"), bg="#f8f9fa", fg="#2c3e50", anchor="w")
        add_header.pack(pady=(10, 10), padx=10, fill=tk.X)
        
        fields = [
            ("Course:", "add_course", True),
            ("Subject:", "add_subject", False),
            ("Teacher:", "add_teacher", True),
            ("Day:", "add_day", True),
            ("Time:", "add_time", True),
            ("Classroom:", "add_classroom", True)
        ]
        
        for label_text, attr_name, is_combo in fields:
            tk.Label(add_frame, text=label_text, bg="#f8f9fa", fg="#5d6d7e",
                    font=("Comic Sans", 9)).pack(anchor=tk.W, pady=(5, 3), padx=10)
            if is_combo:
                widget = ttk.Combobox(add_frame, state="readonly", width=25, 
                                     font=("Comic Sans", 9), style='Custom.TCombobox')
                if attr_name == "add_day":
                    widget['values'] = self.days
                elif attr_name == "add_time":
                    widget['values'] = self.time_slots
            else:
                widget = tk.Entry(add_frame, width=27, font=("Comic Sans", 9), 
                                 bg="white", fg="#2c3e50", relief=tk.FLAT,
                                 borderwidth=1, highlightthickness=1, 
                                 highlightbackground="#e0e0e0")
            widget.pack(fill=tk.X, pady=(0, 8), padx=10)
            setattr(self, attr_name, widget)
        
        add_btn = self.create_modern_button(add_frame, "Add Lecture", self.add_extra_lecture,
                                           "#e67e22")
        add_btn.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # Right panel - Timetable display
        right_panel = tk.Frame(main_container, bg="white", relief=tk.FLAT, bd=0)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.display_title_label = tk.Label(right_panel, text="Generated Timetable",
                                font=("Comic Sans", 18, "bold"), bg="white", fg="#2c3e50")
        self.display_title_label.pack(pady=20)
        
        # Timetable display with scrollbar
        table_container = tk.Frame(right_panel, bg="white")
        table_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        canvas = tk.Canvas(table_container, bg="white", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=canvas.xview)
        
        self.timetable_frame = tk.Frame(canvas, bg="white")
        
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas.create_window((0, 0), window=self.timetable_frame, anchor=tk.NW)
        
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.timetable_frame.bind("<Configure>", configure_scroll_region)
        
        self.canvas = canvas
        
        self.update_status()
        self.entity_frame.pack_forget()
    
    def create_file_input(self, parent, label_text, command):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.X, padx=20, pady=8)
        
        label = tk.Label(frame, text=label_text, font=("Comic Sans", 10),
                        bg="white", fg="#34495e", anchor="w")
        label.pack(fill=tk.X, pady=(0, 5))
        
        btn = self.create_modern_button(frame, "Choose File", command, "#ecf0f1")
        btn.pack(fill=tk.X)
    
    def load_courses(self):
        """Load courses CSV: name, semester, no_of_batches, capacity, courses"""
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.courses = list(reader)
                    
                for course in self.courses:
                    course['no_of_batches'] = int(course.get('no_of_batches', 1))
                    course['capacity'] = int(course.get('capacity', 60))
                    
                self.add_course['values'] = [c['name'] for c in self.courses]
                messagebox.showinfo("Success", f"Loaded {len(self.courses)} courses")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load courses: {str(e)}")
    
    def load_subject_details(self):
        """Load subject details CSV: subject, department, lecture_hours, lab_hours, tutorial_hours"""
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        subject_name = row['subject'].strip()
                        self.subject_details[subject_name] = {
                            'department': row['department'].strip(),
                            'lecture_hours': int(row.get('lecture_hours', 0)),
                            'lab_hours': int(row.get('lab_hours', 0)),
                            'tutorial_hours': int(row.get('tutorial_hours', 0))
                        }
                messagebox.showinfo("Success", f"Loaded {len(self.subject_details)} subject details")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load subject details: {str(e)}")
    
    def load_teachers(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.teachers = list(reader)
                self.add_teacher['values'] = [t['teacher_name'] for t in self.teachers]
                messagebox.showinfo("Success", f"Loaded {len(self.teachers)} teachers")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load teachers: {str(e)}")
    
    def load_availability(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        teacher = None
                        if 'teacher_name' in row:
                            teacher = row['teacher_name']
                        elif 'Teacher Name' in row:
                            teacher = row['Teacher Name']
                        elif 'Teacher' in row:
                            teacher = row['Teacher']
                        else:
                            first_col = list(row.keys())[0] if row else None
                            teacher = row.get(first_col) if first_col else None
                        
                        if not teacher:
                            continue
                        
                        faculty_type = row.get('type of faculty', '').lower()
                        if not faculty_type:
                            faculty_type = row.get('faculty_type', 'permanent').lower()
                        
                        availability = {}
                        
                        for day in self.days:
                            day_availability = row.get(day, '').strip()
                            if day_availability and day_availability.lower() != 'na':
                                time_ranges = [t.strip() for t in day_availability.split(';')]
                                valid_slots = []
                                for time_range in time_ranges:
                                    expanded = self.expand_time_range(time_range)
                                    valid_slots.extend(expanded)
                                availability[day] = valid_slots
                            else:
                                availability[day] = []
                        
                        self.teacher_availability[teacher] = {
                            'availability': availability,
                            'faculty_type': faculty_type
                        }
                        
                messagebox.showinfo("Success", f"Loaded availability for {len(self.teacher_availability)} teachers")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load availability: {str(e)}")
    
    def load_classrooms(self):
        """Load classrooms CSV: class_type, room, department, capacity"""
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.classrooms = []
                    for row in reader:
                        classroom = {
                            'class_type': row['class_type'].strip(),
                            'room': row['room'].strip(),
                            'department': row['department'].strip(),
                            'capacity': int(row['capacity'])
                        }
                        self.classrooms.append(classroom)
                        
                self.add_classroom['values'] = [c['room'] for c in self.classrooms]
                messagebox.showinfo("Success", f"Loaded {len(self.classrooms)} classrooms")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load classrooms: {str(e)}")
    
    def update_status(self):
        self.status_text.delete(1.0, tk.END)
        status = f"Courses: {len(self.courses)}\n"
        status += f"Subjects: {len(self.subject_details)}\n"
        status += f"Teachers: {len(self.teachers)}\n"
        status += f"Availability: {len(self.teacher_availability)}\n"
        status += f"Classrooms: {len(self.classrooms)}\n"
        if self.schedule:
            status += f"\nClasses: {len(self.schedule)}"
        self.status_text.insert(1.0, status)
    
    def on_view_change(self):
        view = self.current_view.get()
        
        if view == "master":
            self.entity_frame.pack_forget()
        else:
            self.entity_frame.pack(fill=tk.X, pady=(10, 10), padx=10)
            
            if view == "course":
                entities = [c['name'] for c in self.courses]
            elif view == "teacher":
                entities = [t['teacher_name'] for t in self.teachers]
            elif view == "classroom":
                entities = [c['room'] for c in self.classrooms]
            else:
                entities = []
            
            self.entity_dropdown['values'] = entities
            if entities:
                self.entity_dropdown.current(0)
        
        if self.schedule:
            self.display_schedule()
    
    def find_empty_classrooms(self):
        if not self.schedule:
            messagebox.showwarning("Warning", "Generate schedule first")
            return
        
        day = self.find_day.get()
        time = self.find_time.get()
        
        if not day or not time:
            messagebox.showwarning("Warning", "Please select both day and time")
            return
        
        occupied = set()
        for entry in self.schedule:
            if entry['day'] == day and entry['time'] == time:
                occupied.add(entry['classroom'])
        
        empty = [c['room'] for c in self.classrooms if c['room'] not in occupied]
        
        self.empty_rooms_text.delete(1.0, tk.END)
        if empty:
            result = f"Empty on {day[:3]} {time}:\n\n"
            result += "\n".join(f"• {room}" for room in empty)
        else:
            result = "No empty classrooms."
        
        self.empty_rooms_text.insert(1.0, result)
    
    def add_extra_lecture(self):
        course = self.add_course.get()
        subject = self.add_subject.get()
        teacher = self.add_teacher.get()
        day = self.add_day.get()
        time = self.add_time.get()
        classroom = self.add_classroom.get()
        
        if not all([course, subject, teacher, day, time, classroom]):
            messagebox.showwarning("Warning", "Please fill all fields")
            return
        
        for entry in self.schedule:
            if entry['day'] == day and entry['time'] == time:
                if entry['classroom'] == classroom:
                    messagebox.showerror("Error", "Classroom occupied")
                    return
                if entry['teacher'] == teacher:
                    messagebox.showerror("Error", "Teacher busy")
                    return
                if entry['course'] == course:
                    messagebox.showerror("Error", "Course has class")
                    return
        
        self.schedule.append({
            'course': course,
            'subject': subject,
            'teacher': teacher,
            'day': day,
            'time': time,
            'classroom': classroom,
            'type': 'lecture'
        })
        
        self.display_schedule()
        self.update_status()
        messagebox.showinfo("Success", "Lecture added")
        self.add_subject.delete(0, tk.END)
    
    def generate_schedule(self):
        if not all([self.courses, self.teachers, self.classrooms, self.subject_details]):
            messagebox.showerror("Error", "Please load all required data files")
            return
        
        self.progress_label.config(text="Initializing CSP algorithm...")
        self.root.update()
        
        try:
            lecture_requirements = self.build_lecture_requirements()
            
            if not lecture_requirements:
                messagebox.showerror("Error", "No lecture requirements found. Check that courses match subject details.")
                return
            
            teacher_subjects = defaultdict(list)
            for teacher in self.teachers:
                subjects = teacher.get('subjects', '').split(',')
                for subject in subjects:
                    teacher_subjects[subject.strip()].append(teacher['teacher_name'])
            
            schedule_grid = {}
            for day in self.days:
                schedule_grid[day] = {}
                for time in self.time_slots:
                    schedule_grid[day][time] = []
            
            assignments = []
            success = self.backtrack(0, lecture_requirements, teacher_subjects, 
                                    schedule_grid, assignments, 0)
            
            if success:
                self.schedule = assignments
                self.progress_label.config(text="✓ Complete! Schedule generated successfully")
                self.on_view_change()
                self.display_schedule()
                self.update_status()
                messagebox.showinfo("Success", f"Generated {len(self.schedule)} classes!")
            else:
                self.progress_label.config(text="✗ Failed - Could not satisfy all constraints")
                messagebox.showerror("Error", "Could not generate valid schedule with current constraints.\nTry: More classrooms, fewer courses, or relaxed availability.")
        
        except Exception as e:
            self.progress_label.config(text="✗ Error occurred")
            messagebox.showerror("Error", f"Schedule generation failed: {str(e)}")
    
    def build_lecture_requirements(self):
        """Build lecture requirements from courses and subject details"""
        requirements = []
        
        for course in self.courses:
            course_name = course['name']
            subjects = [s.strip() for s in course.get('courses', '').split('|')]
            no_of_batches = int(course.get('no_of_batches', 1))
            total_capacity = int(course.get('capacity', 60))
            
            for subject in subjects:
                if subject not in self.subject_details:
                    continue
                    
                details = self.subject_details[subject]
                department = details['department']
                
                for i in range(details['lecture_hours']):
                    requirements.append({
                        'course': course_name,
                        'subject': subject,
                        'type': 'lecture',
                        'duration': 1,
                        'department': department,
                        'capacity_needed': total_capacity,
                        'batch': None
                    })
                
                lab_hours = details['lab_hours']
                if lab_hours >= 2:
                    batch_capacity = total_capacity // no_of_batches if no_of_batches > 0 else total_capacity
                    for batch_num in range(no_of_batches):
                        num_lab_sessions = lab_hours // 2
                        for session in range(num_lab_sessions):
                            requirements.append({
                                'course': course_name,
                                'subject': f"{subject} (Lab)",
                                'type': 'lab',
                                'duration': 2,
                                'department': department,
                                'capacity_needed': batch_capacity,
                                'batch': f"Batch {batch_num + 1}" if no_of_batches > 1 else None
                            })
                
                tutorial_hours = details['tutorial_hours']
                if tutorial_hours > 0:
                    batch_capacity = total_capacity // no_of_batches if no_of_batches > 0 else total_capacity
                    for batch_num in range(no_of_batches):
                        for i in range(tutorial_hours):
                            requirements.append({
                                'course': course_name,
                                'subject': f"{subject} (Tutorial)",
                                'type': 'tutorial',
                                'duration': 1,
                                'department': department,
                                'capacity_needed': batch_capacity,
                                'batch': f"Batch {batch_num + 1}" if no_of_batches > 1 else None
                            })
        
        return requirements
    
    def backtrack(self, index, requirements, teacher_subjects, grid, assignments, depth=0):
        if index >= len(requirements):
            return True
        
        if depth > 10000:
            return False
        
        lecture = requirements[index]
        
        if index % 3 == 0:
            progress = (index / len(requirements)) * 100
            self.progress_label.config(text=f"Scheduling: {progress:.0f}% ({index}/{len(requirements)})")
            self.root.update()
        
        subject_clean = lecture['subject'].replace(' (Lab)', '').replace(' (Tutorial)', '')
        
        assigned_teacher = None
        for a in assignments:
            if a['course'] == lecture['course']:
                a_subject_clean = a['subject'].replace(' (Lab)', '').replace(' (Tutorial)', '').replace(' - Batch 1', '').replace(' - Batch 2', '')
                if a_subject_clean == subject_clean:
                    assigned_teacher = a['teacher']
                    break
        
        if assigned_teacher:
            available_teachers = [assigned_teacher]
        else:
            available_teachers = teacher_subjects.get(subject_clean, [])
        
        if not available_teachers:
            return self.backtrack(index + 1, requirements, teacher_subjects, grid, assignments, depth + 1)
        
        possible_assignments = []
        for teacher in available_teachers:
            for day in self.days:
                for time_idx in range(len(self.time_slots) - lecture['duration'] + 1):
                    suitable_classrooms = self.get_suitable_classrooms(lecture)
                    
                    for classroom in suitable_classrooms:
                        classroom_name = classroom['room']
                        
                        if self.can_use_classroom(classroom_name, day, time_idx, 
                                                 lecture['duration'], grid):
                            if self.is_valid_assignment_relaxed(lecture, teacher, day, 
                                                               time_idx, grid, assignments, classroom):
                                score = self.calculate_assignment_score(lecture, teacher, day, 
                                                                       time_idx, assignments)
                                possible_assignments.append({
                                    'teacher': teacher,
                                    'day': day,
                                    'time_idx': time_idx,
                                    'classroom': classroom_name,
                                    'score': score
                                })
        
        possible_assignments.sort(key=lambda x: x['score'], reverse=True)
        
        for assign_data in possible_assignments:
            teacher = assign_data['teacher']
            day = assign_data['day']
            time_idx = assign_data['time_idx']
            classroom_name = assign_data['classroom']
            start_time = self.time_slots[time_idx]
            
            batch_info = f" - {lecture['batch']}" if lecture.get('batch') else ""
            
            assignment = {
                'course': lecture['course'],
                'subject': lecture['subject'] + batch_info,
                'teacher': teacher,
                'day': day,
                'time': start_time,
                'classroom': classroom_name,
                'type': lecture['type']
            }
            
            self.make_assignment(assignment, lecture['duration'], time_idx, grid)
            assignments.append(assignment)
            
            if self.backtrack(index + 1, requirements, teacher_subjects, 
                            grid, assignments, depth + 1):
                return True
            
            self.undo_assignment(assignment, lecture['duration'], time_idx, grid)
            assignments.pop()
        
        return False
    
    def get_suitable_classrooms(self, lecture):
        """Get classrooms suitable for the lecture based on type, department, and capacity"""
        suitable = []
        ideal = []
        fallback = []
        
        for classroom in self.classrooms:
            class_type_lower = classroom['class_type'].lower()
            
            if classroom['capacity'] < lecture['capacity_needed']:
                continue
            
            if lecture['type'] == 'lab':
                if class_type_lower in ['cl', 'lab'] and \
                   classroom['department'] == lecture['department']:
                    suitable.append(classroom)
            
            elif lecture['type'] == 'tutorial':
                if class_type_lower == 'tr' and classroom['department'] == lecture['department']:
                    ideal.append(classroom)
                elif class_type_lower == 'tr':
                    ideal.append(classroom)
                elif class_type_lower == 'cr' and classroom['department'] == lecture['department']:
                    fallback.append(classroom)
                elif class_type_lower == 'cr':
                    fallback.append(classroom)
                
                suitable = ideal + fallback
            
            else:
                if class_type_lower in ['classroom', 'lecture hall', 'room', 'cr', 'lh']:
                    if classroom['department'] == lecture['department']:
                        suitable.insert(0, classroom)
                    else:
                        suitable.append(classroom)
        
        return suitable
    
    def calculate_isolation_penalty(self, lecture, day, time_idx, assignments):
        """
        Penalize scheduling a 1-hour class with breaks on both sides.
        Only applies to single-hour lectures/tutorials, not 2-hour labs.
        """
        if lecture['duration'] != 1:
            return 0
        
        score = 0
        course = lecture['course']
        batch = lecture.get('batch')
        
        occupied_slots = set()
        for a in assignments:
            if a['course'] == course and a['day'] == day:
                a_subject = a.get('subject', '')
                
                if batch:
                    if batch in a_subject or ('Batch' not in a_subject and '(Lab)' not in a_subject and '(Tutorial)' not in a_subject):
                        existing_time_idx = self.time_slots.index(a['time'])
                        duration = a.get('duration', 1)
                        for i in range(duration):
                            occupied_slots.add(existing_time_idx + i)
                else:
                    existing_time_idx = self.time_slots.index(a['time'])
                    duration = a.get('duration', 1)
                    for i in range(duration):
                        occupied_slots.add(existing_time_idx + i)
        
        has_before = (time_idx - 1) in occupied_slots
        has_after = (time_idx + 1) in occupied_slots
        
        if not has_before and not has_after:
            score -= 40
        elif not has_before or not has_after:
            score -= 10
        
        return score
    
    def calculate_assignment_score(self, lecture, teacher, day, time_idx, assignments):
        score = 0
        
        course_days = {}
        for a in assignments:
            if a['course'] == lecture['course']:
                course_days[a['day']] = course_days.get(a['day'], 0) + a.get('duration', 1)
        
        current_day_hours = course_days.get(day, 0)
        
        if current_day_hours == 0:
            if len(course_days) > 0:
                score -= 30 
            score += 20  
        elif current_day_hours == 1:
            score += 40  
        elif current_day_hours >= 2:
            score += 15
        
        daily_count = sum(1 for a in assignments if a['course'] == lecture['course'] and a['day'] == day)
        if daily_count < 4:
            score += 20
        elif daily_count < 6:
            score += 10
        
        teacher_weekly_hours = sum(
            a.get('duration', 1) for a in assignments if a['teacher'] == teacher
        )
        if teacher_weekly_hours < 15:
            score += 25 
        elif teacher_weekly_hours < 18:
            score += 10  
        else:
            score -= 20  
        
        teacher_day_hours = sum(
            a.get('duration', 1) for a in assignments 
            if a['teacher'] == teacher and a['day'] == day
        )
        if teacher_day_hours == 0:
            score += 5
        elif teacher_day_hours == 1:
            score += 30
        elif teacher_day_hours >= 2 and teacher_day_hours < 5:
            score += 20
        elif teacher_day_hours >= 5:
            score -= 15
        
        course_days_count = len(course_days)
        if day not in course_days and course_days_count < 4:
            score += 25  
        
        if 2 <= time_idx <= 6:
            score += 10
        
        if teacher in self.teacher_availability:
            teacher_data = self.teacher_availability[teacher]
            faculty_type = teacher_data.get('faculty_type', '')
            availability = teacher_data.get('availability', {})
            
            assigned_time = self.time_slots[time_idx]
            day_availability = availability.get(day, [])
            
            if assigned_time in day_availability:
                score += 40
            elif day_availability:
                score += 10
            else:
                score -= 30
            
            if faculty_type == 'permanent':
                score += 15
            elif faculty_type == 'visiting':
                score += 5
        
        score += self.calculate_isolation_penalty(lecture, day, time_idx, assignments)
        score += self.calculate_break_quality_score(lecture, day, time_idx, assignments)
        
        return score
    
    def is_valid_assignment_relaxed(self, lecture, teacher, day, time_idx, grid, assignments, classroom):
        for i in range(lecture['duration']):
            time = self.time_slots[time_idx + i]
            
            for existing in grid[day][time]:
                if existing['teacher'] == teacher:
                    return False
                
                if existing['course'] == lecture['course']:
                    current_subject = lecture['subject'].replace(' (Lab)', '').replace(' (Tutorial)', '')
                    existing_subject = existing.get('subject', '').replace(' (Lab)', '').replace(' (Tutorial)', '')
                    
                    if lecture.get('batch'):
                        if lecture['batch'] in existing.get('subject', ''):
                            return False
                        if 'Batch' not in existing.get('subject', ''):
                            return False
                        if current_subject == existing_subject:
                            return False
                    else:
                        return False
        
        if classroom['capacity'] < lecture['capacity_needed']:
            return False
        
        class_type_lower = classroom['class_type'].lower()
        
        if lecture['type'] == 'lab':
            if class_type_lower not in ['cl', 'lab']:
                return False
            if classroom['department'] != lecture['department']:
                return False
        
        elif lecture['type'] == 'tutorial':
            if class_type_lower not in ['tr', 'cr']:
                return False
        
        teacher_weekly_hours = sum(
            a.get('duration', 1) for a in assignments if a['teacher'] == teacher
        )
        if teacher_weekly_hours + lecture['duration'] > 20:
            return False
        
        if teacher in self.teacher_availability:
            teacher_data = self.teacher_availability[teacher]
            availability_dict = teacher_data.get('availability', {})
            day_availability = availability_dict.get(day, [])
            
            for i in range(lecture['duration']):
                time_slot = self.time_slots[time_idx + i]
                if time_slot not in day_availability:
                    return False
        
        if not self.check_break_constraint(lecture, day, time_idx, assignments):
            return False
        
        batch = lecture.get('batch')
        if batch:
            daily_count = sum(1 for a in assignments 
                            if a['course'] == lecture['course'] and a['day'] == day
                            and (batch in a.get('subject', '') or 'Batch' not in a.get('subject', '')))
        else:
            daily_count = sum(1 for a in assignments 
                            if a['course'] == lecture['course'] and a['day'] == day)
        
        if daily_count >= 8:
            return False
        
        return True
    
    def check_break_constraint(self, lecture, day, time_idx, assignments):
        course = lecture['course']
        batch = lecture.get('batch')
        
        course_times_on_day = []
        for a in assignments:
            if a['course'] == course and a['day'] == day:
                a_subject = a.get('subject', '')
                
                if batch:
                    if batch in a_subject or ('Batch' not in a_subject and '(Lab)' not in a_subject and '(Tutorial)' not in a_subject):
                        existing_time_idx = self.time_slots.index(a['time'])
                        duration = a.get('duration', 1)
                        for i in range(duration):
                            course_times_on_day.append(existing_time_idx + i)
                else:
                    existing_time_idx = self.time_slots.index(a['time'])
                    duration = a.get('duration', 1)
                    for i in range(duration):
                        course_times_on_day.append(existing_time_idx + i)
        
        for i in range(lecture['duration']):
            course_times_on_day.append(time_idx + i)
        
        all_times = sorted(set(course_times_on_day))
        
        if len(all_times) <= 1:
            return True
        
        total_lecture_hours = len(all_times)
        
        min_slot = min(all_times)
        max_slot = max(all_times)
        total_break_hours = 0
        for slot in range(min_slot, max_slot + 1):
            if slot not in all_times:
                total_break_hours += 1
        
        if total_lecture_hours <= 3:
            return total_break_hours == 0
        elif total_lecture_hours <= 5:
            return total_break_hours <= 1
        else:
            return total_break_hours <= 2
   
    def calculate_break_quality_score(self, lecture, day, time_idx, assignments):
        score = 0
        course = lecture['course']
        batch = lecture.get('batch')
        
        course_times_on_day = []
        for a in assignments:
            if a['course'] == course and a['day'] == day:
                a_subject = a.get('subject', '')
                
                if batch:
                    if batch in a_subject or ('Batch' not in a_subject and '(Lab)' not in a_subject and '(Tutorial)' not in a_subject):
                        existing_time_idx = self.time_slots.index(a['time'])
                        duration = a.get('duration', 1)
                        for i in range(duration):
                            course_times_on_day.append(existing_time_idx + i)
                else:
                    existing_time_idx = self.time_slots.index(a['time'])
                    duration = a.get('duration', 1)
                    for i in range(duration):
                        course_times_on_day.append(existing_time_idx + i)
        
        for i in range(lecture['duration']):
            course_times_on_day.append(time_idx + i)
        
        all_times = sorted(set(course_times_on_day))
        
        if len(all_times) <= 1:
            return 0
        
        total_lecture_hours = len(all_times)
        if total_lecture_hours >= 7:
            score -= (total_lecture_hours * 5)
            
        break_blocks = []
        lecture_blocks = []
        current_break = 0
        current_lecture = 0
        
        min_slot = min(all_times)
        max_slot = max(all_times)
        
        for slot in range(min_slot, max_slot + 1):
            if slot in all_times:
                current_lecture += 1
                if current_break > 0:
                    break_blocks.append(current_break)
                    current_break = 0
            else:
                current_break += 1
                if current_lecture > 0:
                    lecture_blocks.append(current_lecture)
                    current_lecture = 0
        if current_break > 0:
            break_blocks.append(current_break)
        if current_lecture > 0:
            lecture_blocks.append(current_lecture)
        
        if len(break_blocks) > 0:
            score += 10
            
            if len(break_blocks) == 1 and len(lecture_blocks) == 2:
                first_block = lecture_blocks[0]
                second_block = lecture_blocks[1]
                
                ratio = min(first_block, second_block) / max(first_block, second_block)
                
                if ratio >= 0.6:
                    score += 20
                elif ratio >= 0.3:
                    score += 10
        
        max_continuous = max(lecture_blocks) if lecture_blocks else 0
        if max_continuous > 3:
            score -= (max_continuous - 3) * 10
        
        return score
    
    def is_time_available(self, lecture, teacher, day, time_idx, grid):
        for i in range(lecture['duration']):
            if time_idx + i >= len(self.time_slots):
                return False
            time = self.time_slots[time_idx + i]
            for existing in grid[day][time]:
                if existing['teacher'] == teacher or existing['course'] == lecture['course']:
                    return False
        return True
    
    def can_use_classroom(self, classroom, day, time_idx, duration, grid):
        for i in range(duration):
            time = self.time_slots[time_idx + i]
            for existing in grid[day][time]:
                if existing['classroom'] == classroom:
                    return False
        return True
    
    def make_assignment(self, assignment, duration, time_idx, grid):
        day = assignment['day']
        assignment['duration'] = duration
        for i in range(duration):
            time = self.time_slots[time_idx + i]
            grid[day][time].append({
                'course': assignment['course'],
                'subject': assignment['subject'],
                'teacher': assignment['teacher'],
                'classroom': assignment['classroom'],
                'type': assignment['type'],
                'duration': duration
            })
    
    def undo_assignment(self, assignment, duration, time_idx, grid):
        day = assignment['day']
        for i in range(duration):
            time = self.time_slots[time_idx + i]
            grid[day][time] = [
                e for e in grid[day][time]
                if not (e['course'] == assignment['course'] and 
                       e['subject'] == assignment['subject'] and
                       e['teacher'] == assignment['teacher'])
            ]
    
    def get_filtered_schedule(self):
        view = self.current_view.get()
        
        if view == "master":
            return self.schedule
        
        entity = self.selected_entity.get()
        if not entity:
            return []
        
        if view == "course":
            return [s for s in self.schedule if s['course'] == entity]
        elif view == "teacher":
            return [s for s in self.schedule if s['teacher'] == entity]
        elif view == "classroom":
            return [s for s in self.schedule if s['classroom'] == entity]
        
        return []
    
    def display_schedule(self):
        for widget in self.timetable_frame.winfo_children():
            widget.destroy()
        
        view = self.current_view.get()
        filtered_schedule = self.get_filtered_schedule()
        
        if view == "master":
            self.display_title_label.config(text="Master Timetable")
            self.display_master_schedule()
        elif view == "course":
            self.display_title_label.config(text=f"Course: {self.selected_entity.get()}")
            self.display_grid_schedule(filtered_schedule, view)
        elif view == "teacher":
            self.display_title_label.config(text=f"Teacher: {self.selected_entity.get()}")
            self.display_grid_schedule(filtered_schedule, view)
        elif view == "classroom":
            self.display_title_label.config(text=f"Classroom: {self.selected_entity.get()}")
            self.display_grid_schedule(filtered_schedule, view)
        
        self.timetable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def display_grid_schedule(self, schedule, view_type):
        if not schedule:
            tk.Label(self.timetable_frame, text="No classes scheduled",
                    font=("Comic Sans", 12), bg="white", fg="#7f8c8d",
                    padx=20, pady=20).grid(row=0, column=0)
            return
        
        tk.Label(self.timetable_frame, text="Time", font=("Comic Sans", 10, "bold"),
                bg="#34495e", fg="white", padx=10, pady=12, relief=tk.FLAT,
                width=12).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        for col_idx, day in enumerate(self.days, start=1):
            tk.Label(self.timetable_frame, text=day, font=("Comic Sans", 10, "bold"),
                    bg="#34495e", fg="white", padx=10, pady=12, relief=tk.FLAT,
                    width=18).grid(row=0, column=col_idx, sticky="nsew", padx=2, pady=2)
        
        schedule_map = defaultdict(list)
        for entry in schedule:
            key = (entry['day'], entry['time'])
            schedule_map[key].append(entry)
        
        for row_idx, time_slot in enumerate(self.time_slots, start=1):
            tk.Label(self.timetable_frame, text=time_slot, font=("Comic Sans", 9, "bold"),
                    bg="#ecf0f1", fg="#2c3e50", padx=8, pady=10, relief=tk.FLAT,
                    anchor="center").grid(row=row_idx, column=0, sticky="nsew", padx=2, pady=2)
            
            for col_idx, day in enumerate(self.days, start=1):
                key = (day, time_slot)
                
                if key in schedule_map and schedule_map[key]:
                    entries = schedule_map[key]
                    
                    if len(entries) > 1:
                        cell_text = "\n---\n".join([self.format_cell_text(e, view_type) for e in entries])
                        bg_color = "#fff3cd"
                    else:
                        entry = entries[0]
                        cell_text = self.format_cell_text(entry, view_type)
                        if entry.get('type') == 'lab':
                            bg_color = "#e8daef"
                        elif entry.get('type') == 'tutorial':
                            bg_color = "#d5f4e6"
                        elif view_type == "course":
                            bg_color = "#d6eaf8"
                        elif view_type == "teacher":
                            bg_color = "#fadbd8"
                        elif view_type == "classroom":
                            bg_color = "#fef9e7"
                        else:
                            bg_color = "white"
                    
                    cell = tk.Label(self.timetable_frame, text=cell_text,
                                  font=("Comic Sans", 8), bg=bg_color, fg="black",
                                  padx=8, pady=10, relief=tk.FLAT,
                                  anchor="center", justify="center", wraplength=140,
                                  borderwidth=1, highlightthickness=1, 
                                  highlightbackground="#e0e0e0")
                else:
                    cell = tk.Label(self.timetable_frame, text="—",
                                  font=("Comic Sans", 10), bg="white", fg="#95a5a6",
                                  padx=8, pady=10, relief=tk.FLAT,
                                  anchor="center", borderwidth=1, 
                                  highlightthickness=1, highlightbackground="#e0e0e0")
                
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
        
        for i in range(len(self.time_slots) + 1):
            self.timetable_frame.grid_rowconfigure(i, weight=1)
        for i in range(len(self.days) + 1):
            self.timetable_frame.grid_columnconfigure(i, weight=1)
    
    def format_cell_text(self, entry, view_type):
        lab_indicator = " [LAB]" if entry.get('type') == 'lab' else ""
        tutorial_indicator = " [TUT]" if entry.get('type') == 'tutorial' else ""
        
        if view_type == "course":
            return f"{entry['subject']}{lab_indicator}{tutorial_indicator}\n{entry['teacher']}\n{entry['classroom']}"
        elif view_type == "teacher":
            return f"{entry['course']}\n{entry['subject']}{lab_indicator}{tutorial_indicator}\n{entry['classroom']}"
        elif view_type == "classroom":
            return f"{entry['course']}\n{entry['subject']}{lab_indicator}{tutorial_indicator}\n{entry['teacher']}"
        return ""
    
    def display_master_schedule(self):
        headers = ['Day', 'Time', 'Course', 'Subject', 'Teacher', 'Classroom', 'Type']
        for col_idx, header in enumerate(headers):
            tk.Label(self.timetable_frame, text=header, font=("Comic Sans", 10, "bold"),
                    bg="#34495e", fg="white", padx=12, pady=12, relief=tk.FLAT,
                    width=14).grid(row=0, column=col_idx, sticky="nsew", padx=2, pady=2)
        
        sorted_schedule = sorted(self.schedule, 
                                key=lambda x: (self.days.index(x['day']), x['time']))
        
        for row_idx, entry in enumerate(sorted_schedule, start=1):
            values = [
                entry['day'], 
                entry['time'], 
                entry['course'], 
                entry['subject'], 
                entry['teacher'], 
                entry['classroom'],
                entry.get('type', 'lecture').upper()
            ]
            
            bg_color = "#f8f9fa" if row_idx % 2 == 0 else "white"
            if entry.get('type') == 'lab':
                bg_color = "#e8daef"
            elif entry.get('type') == 'tutorial':
                bg_color = "#d5f4e6"
            
            for col_idx, value in enumerate(values):
                tk.Label(self.timetable_frame, text=value, font=("Comic Sans", 9),
                        bg=bg_color, fg="black", padx=10, pady=10, relief=tk.FLAT,
                        anchor="w", wraplength=120, borderwidth=1, 
                        highlightthickness=1, highlightbackground="#e0e0e0").grid(
                        row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
        
        for i in range(len(sorted_schedule) + 1):
            self.timetable_frame.grid_rowconfigure(i, weight=0)
        for i in range(len(headers)):
            self.timetable_frame.grid_columnconfigure(i, weight=1)
    
    def export_csv(self):
        if not self.schedule:
            messagebox.showwarning("Warning", "No schedule to export")
            return
        
        view = self.current_view.get()
        filtered_schedule = self.get_filtered_schedule()
        
        if not filtered_schedule:
            messagebox.showwarning("Warning", "No data to export for current view")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                               filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['day', 'time', 'course', 'subject', 'teacher', 'classroom', 'type']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for entry in filtered_schedule:
                        writer.writerow(entry)
                
                messagebox.showinfo("Success", "Schedule exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def export_pdf(self):
        if not PDF_AVAILABLE:
            messagebox.showerror("Error", "ReportLab library not installed.\nPlease install it using: pip install reportlab")
            return
        
        if not self.schedule:
            messagebox.showwarning("Warning", "No schedule to export")
            return
        
        view = self.current_view.get()
        filtered_schedule = self.get_filtered_schedule()
        
        if not filtered_schedule:
            messagebox.showwarning("Warning", "No data to export for current view")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                               filetypes=[("PDF files", "*.pdf")])
        if not filename:
            return
        
        try:
            if view == "master":
                self.export_master_pdf(filename, filtered_schedule)
            else:
                self.export_grid_pdf(filename, filtered_schedule, view)
            
            messagebox.showinfo("Success", f"PDF exported successfully to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def export_master_pdf(self, filename, schedule):
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        title = Paragraph("Master Timetable", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        sorted_schedule = sorted(schedule, key=lambda x: (self.days.index(x['day']), x['time']))
        
        table_data = [['Day', 'Time', 'Course', 'Subject', 'Teacher', 'Classroom', 'Type']]
        
        for entry in sorted_schedule:
            table_data.append([
                entry['day'],
                entry['time'],
                entry['course'],
                entry['subject'],
                entry['teacher'],
                entry['classroom'],
                entry.get('type', 'lecture').upper()
            ])
        
        table = Table(table_data, colWidths=[1*inch, 1.2*inch, 1.5*inch, 1.8*inch, 1.5*inch, 1.2*inch, 0.8*inch])
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ])
        
        for row_idx, entry in enumerate(sorted_schedule, start=1):
            if entry.get('type') == 'lab':
                style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#e8daef'))
            elif entry.get('type') == 'tutorial':
                style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#d5f4e6'))
        
        table.setStyle(style)
        elements.append(table)
        
        doc.build(elements)
    
    def export_grid_pdf(self, filename, schedule, view_type):
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        entity_name = self.selected_entity.get()
        title_text = f"{view_type.capitalize()}: {entity_name}"
        title = Paragraph(title_text, title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        schedule_map = defaultdict(list)
        for entry in schedule:
            key = (entry['day'], entry['time'])
            schedule_map[key].append(entry)
        
        table_data = [['Time'] + self.days]
        
        for time_slot in self.time_slots:
            row = [time_slot]
            for day in self.days:
                key = (day, time_slot)
                if key in schedule_map and schedule_map[key]:
                    entries = schedule_map[key]
                    if len(entries) > 1:
                        cell_text = "\n---\n".join([self.format_cell_text_simple(e, view_type) for e in entries])
                    else:
                        cell_text = self.format_cell_text_simple(entries[0], view_type)
                    row.append(cell_text)
                else:
                    row.append("—")
            table_data.append(row)
        
        col_width = 1.3*inch
        table = Table(table_data, colWidths=[1*inch] + [col_width]*6)
        
        style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
        ]
        
        for row_idx, time_slot in enumerate(self.time_slots, start=1):
            for col_idx, day in enumerate(self.days, start=1):
                key = (day, time_slot)
                if key in schedule_map and schedule_map[key]:
                    entries = schedule_map[key]
                    if len(entries) > 1:
                        bg_color = colors.HexColor('#fff3cd')
                    else:
                        entry = entries[0]
                        if entry.get('type') == 'lab':
                            bg_color = colors.HexColor('#e8daef')
                        elif entry.get('type') == 'tutorial':
                            bg_color = colors.HexColor('#d5f4e6')
                        elif view_type == "course":
                            bg_color = colors.HexColor('#d6eaf8')
                        elif view_type == "teacher":
                            bg_color = colors.HexColor('#fadbd8')
                        elif view_type == "classroom":
                            bg_color = colors.HexColor('#fef9e7')
                        else:
                            bg_color = colors.white
                    
                    style_list.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), bg_color))
        
        table.setStyle(TableStyle(style_list))
        elements.append(table)
        
        doc.build(elements)
    
    def format_cell_text_simple(self, entry, view_type):
        lab_indicator = " [LAB]" if entry.get('type') == 'lab' else ""
        tutorial_indicator = " [TUT]" if entry.get('type') == 'tutorial' else ""
        
        if view_type == "course":
            return f"{entry['subject']}{lab_indicator}{tutorial_indicator}\n{entry['teacher']}\n{entry['classroom']}"
        elif view_type == "teacher":
            return f"{entry['course']}\n{entry['subject']}{lab_indicator}{tutorial_indicator}\n{entry['classroom']}"
        elif view_type == "classroom":
            return f"{entry['course']}\n{entry['subject']}{lab_indicator}{tutorial_indicator}\n{entry['teacher']}"
        return ""

if __name__ == "__main__":
    root = tk.Tk()
    app = TimetableScheduler(root)
    root.mainloop()
