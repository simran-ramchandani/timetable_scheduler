import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from datetime import datetime, timedelta
from collections import defaultdict

class TimetableScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("College Timetable Scheduler (CSP)")
        self.root.geometry("1600x900")
        self.root.configure(bg="#f0f0f0")
        
        # Data storage
        self.courses = []
        self.teachers = []
        self.teacher_availability = {}
        self.classrooms = []
        self.schedule = []
        
        # Time slots (8 AM to 6 PM, 1-hour slots)
        self.time_slots = self.generate_time_slots()
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        # Current view type
        self.current_view = tk.StringVar(value="master")
        self.selected_entity = tk.StringVar()
        
        self.setup_ui()
    
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
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="College Timetable Scheduler (CSP Algorithm)",
                              font=("Arial", 22, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(pady=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Input section
        left_panel = tk.Frame(main_container, bg="white", relief=tk.RAISED, bd=2, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), pady=0)
        left_panel.pack_propagate(False)
        
        input_title = tk.Label(left_panel, text="Data Input", font=("Arial", 16, "bold"),
                              bg="white", fg="#2c3e50")
        input_title.pack(pady=15)
        
        # File upload buttons
        self.create_file_input(left_panel, "Courses CSV", self.load_courses)
        self.create_file_input(left_panel, "Teachers CSV", self.load_teachers)
        self.create_file_input(left_panel, "Teacher Availability CSV", self.load_availability)
        self.create_file_input(left_panel, "Classrooms CSV", self.load_classrooms)
        
        # Status display
        status_frame = tk.LabelFrame(left_panel, text="Loaded Data", font=("Arial", 10, "bold"),
                                    bg="white", fg="#2c3e50", padx=8, pady=8)
        status_frame.pack(fill=tk.BOTH, padx=15, pady=15)
        
        self.status_text = tk.Text(status_frame, height=5, width=30, font=("Arial", 8),
                                  bg="#f8f9fa",fg="#2c3e50", relief=tk.FLAT)
        self.status_text.pack()
        
        # Generate button with progress
        generate_frame = tk.Frame(left_panel, bg="white")
        generate_frame.pack(pady=10, padx=15, fill=tk.X)
        
        generate_btn = tk.Button(generate_frame, text="Generate Timetable (CSP)",
                                font=("Arial", 12, "bold"), bg="#402525", fg="black",
                                relief=tk.FLAT, cursor="hand2", padx=15, pady=10,
                                command=self.generate_schedule)
        generate_btn.pack(fill=tk.X)
        
        self.progress_label = tk.Label(generate_frame, text="", font=("Arial", 8),
                                      bg="white", fg="#2c3e50")
        self.progress_label.pack(pady=(5, 0))
        
        # View selector
        view_frame = tk.LabelFrame(left_panel, text="View Timetable", font=("Arial", 10, "bold"),
                                  bg="white", fg="#2c3e50", padx=8, pady=8)
        view_frame.pack(fill=tk.BOTH, padx=15, pady=(0, 10))
        
        tk.Radiobutton(view_frame, text="Master Schedule", variable=self.current_view,
                      value="master", bg="white", fg="#2c3e50",font=("Arial", 9),
                      command=self.on_view_change).pack(anchor=tk.W, pady=2)
        tk.Radiobutton(view_frame, text="By Course", variable=self.current_view,
                      value="course", bg="white",fg="#2c3e50", font=("Arial", 9),
                      command=self.on_view_change).pack(anchor=tk.W, pady=2)
        tk.Radiobutton(view_frame, text="By Teacher", variable=self.current_view,
                      value="teacher", bg="white", fg="#2c3e50",font=("Arial", 9),
                      command=self.on_view_change).pack(anchor=tk.W, pady=2)
        tk.Radiobutton(view_frame, text="By Classroom", variable=self.current_view,
                      value="classroom", bg="white", fg="#2c3e50",font=("Arial", 9),
                      command=self.on_view_change).pack(anchor=tk.W, pady=2)
        
        # Entity selector
        self.entity_frame = tk.Frame(view_frame, bg="white")
        self.entity_frame.pack(fill=tk.X, pady=(8, 0))
        
        tk.Label(self.entity_frame, text="Select:", bg="white", 
                font=("Arial", 8)).pack(anchor=tk.W)
        
        self.entity_dropdown = ttk.Combobox(self.entity_frame, textvariable=self.selected_entity,
                                           state="readonly", width=22, font=("Arial", 8))
        self.entity_dropdown.pack(fill=tk.X)
        self.entity_dropdown.bind("<<ComboboxSelected>>", lambda e: self.display_schedule())
        
        # Export button
        export_btn = tk.Button(left_panel, text="Export Current View",
                              font=("Arial", 10), bg="#3498db", fg="black",
                              relief=tk.FLAT, cursor="hand2", padx=10, pady=8,
                              command=self.export_schedule)
        export_btn.pack(pady=5, padx=15, fill=tk.X)
        
        # Middle panel - Tools
        middle_panel = tk.Frame(main_container, bg="white", relief=tk.RAISED, bd=2, width=280)
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        middle_panel.pack_propagate(False)
        
        tools_title = tk.Label(middle_panel, text="Tools", font=("Arial", 16, "bold"),
                              bg="white", fg="#2c3e50")
        tools_title.pack(pady=15)
        
        # Find Empty Classrooms
        find_frame = tk.LabelFrame(middle_panel, text="Find Empty Classrooms", 
                                  font=("Arial", 10, "bold"),
                                  bg="white", fg="#2c3e50", padx=8, pady=8)
        find_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(find_frame, text="Day:", bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
        self.find_day = ttk.Combobox(find_frame, values=self.days, state="readonly", 
                                     width=22, font=("Arial", 8))
        self.find_day.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(find_frame, text="Time:", bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
        self.find_time = ttk.Combobox(find_frame, values=self.time_slots, state="readonly", 
                                      width=22, font=("Arial", 8))
        self.find_time.pack(fill=tk.X, pady=(0, 8))
        
        find_btn = tk.Button(find_frame, text="Find Empty Rooms",
                           font=("Arial", 9, "bold"), bg="#9b59b6", fg="black",
                           relief=tk.FLAT, cursor="hand2", padx=8, pady=6,
                           command=self.find_empty_classrooms)
        find_btn.pack(fill=tk.X, pady=5)
        
        self.empty_rooms_text = tk.Text(find_frame, height=4, font=("Arial", 8),
                                       bg="#f8f9fa", relief=tk.FLAT)
        self.empty_rooms_text.pack(fill=tk.X, pady=(5, 0))
        
        # Add Extra Lecture
        add_frame = tk.LabelFrame(middle_panel, text="Add Extra Lecture", 
                                 font=("Arial", 10, "bold"),
                                 bg="white", fg="#2c3e50", padx=8, pady=8)
        add_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        fields = [
            ("Course:", "add_course", True),
            ("Subject:", "add_subject", False),
            ("Teacher:", "add_teacher", True),
            ("Day:", "add_day", True),
            ("Time:", "add_time", True),
            ("Classroom:", "add_classroom", True)
        ]
        
        for label_text, attr_name, is_combo in fields:
            tk.Label(add_frame, text=label_text, bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
            if is_combo:
                widget = ttk.Combobox(add_frame, state="readonly", width=22, font=("Arial", 8))
                if attr_name == "add_day":
                    widget['values'] = self.days
                elif attr_name == "add_time":
                    widget['values'] = self.time_slots
            else:
                widget = ttk.Entry(add_frame, width=24, font=("Arial", 8))
            widget.pack(fill=tk.X, pady=(0, 6))
            setattr(self, attr_name, widget)
        
        add_btn = tk.Button(add_frame, text="Add Lecture",
                          font=("Arial", 9, "bold"), bg="#e67e22", fg="black",
                          relief=tk.FLAT, cursor="hand2", padx=8, pady=6,
                          command=self.add_extra_lecture)
        add_btn.pack(fill=tk.X, pady=5)
        
        # Right panel - Timetable display
        right_panel = tk.Frame(main_container, bg="white", relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.display_title_label = tk.Label(right_panel, text="Generated Timetable",
                                font=("Arial", 16, "bold"), bg="white", fg="#2c3e50")
        self.display_title_label.pack(pady=15)
        
        # Timetable display with scrollbar
        table_container = tk.Frame(right_panel, bg="white")
        table_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Canvas for scrolling
        canvas = tk.Canvas(table_container, bg="white")
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
        frame.pack(fill=tk.X, padx=15, pady=6)
        
        label = tk.Label(frame, text=label_text, font=("Arial", 9),
                        bg="white", fg="#34495e", anchor="w")
        label.pack(fill=tk.X)
        
        btn = tk.Button(frame, text="Choose File", font=("Arial", 8),
                       bg="#ecf0f1", fg="#2c3e50", relief=tk.FLAT,
                       cursor="hand2", command=command, padx=8, pady=4)
        btn.pack(fill=tk.X, pady=(3, 0))
    
    def load_courses(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    reader = csv.DictReader(f)
                    self.courses = list(reader)
                self.add_course['values'] = [c['course_name'] for c in self.courses]
                messagebox.showinfo("Success", f"Loaded {len(self.courses)} courses")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load courses: {str(e)}")
    
    def load_teachers(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r') as f:
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
                with open(filename, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        teacher = row['teacher_name']
                        self.teacher_availability[teacher] = {
                            'days': row.get('available_days', '').split(','),
                            'times': row.get('available_times', '').split(',')
                        }
                messagebox.showinfo("Success", "Loaded teacher availability")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load availability: {str(e)}")
    
    def load_classrooms(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    reader = csv.DictReader(f)
                    self.classrooms = list(reader)
                self.add_classroom['values'] = [c['classroom_name'] for c in self.classrooms]
                messagebox.showinfo("Success", f"Loaded {len(self.classrooms)} classrooms")
                self.update_status()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load classrooms: {str(e)}")
    
    def update_status(self):
        self.status_text.delete(1.0, tk.END)
        status = f"Courses: {len(self.courses)}\n"
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
            self.entity_frame.pack(fill=tk.X, pady=(8, 0))
            
            if view == "course":
                entities = [c['course_name'] for c in self.courses]
            elif view == "teacher":
                entities = [t['teacher_name'] for t in self.teachers]
            elif view == "classroom":
                entities = [c['classroom_name'] for c in self.classrooms]
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
        
        empty = [c['classroom_name'] for c in self.classrooms if c['classroom_name'] not in occupied]
        
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
    
    # ==================== CSP ALGORITHM ====================
    
    def generate_schedule(self):
        if not all([self.courses, self.teachers, self.classrooms]):
            messagebox.showerror("Error", "Please load all required data files")
            return
        
        self.progress_label.config(text="Initializing CSP algorithm...")
        self.root.update()
        
        try:
            # Build lecture requirements
            lecture_requirements = self.build_lecture_requirements()
            
            # Build teacher-subject mapping
            teacher_subjects = defaultdict(list)
            for teacher in self.teachers:
                subjects = teacher.get('subjects', '').split(',')
                for subject in subjects:
                    teacher_subjects[subject.strip()].append(teacher['teacher_name'])
            
            # Initialize schedule grid
            schedule_grid = {}
            for day in self.days:
                schedule_grid[day] = {}
                for time in self.time_slots:
                    schedule_grid[day][time] = []
            
            # Start CSP backtracking
            assignments = []
            success = self.backtrack(0, lecture_requirements, teacher_subjects, 
                                    schedule_grid, assignments, 0)
            
            if success:
                self.schedule = assignments
                self.progress_label.config(text="Complete! Schedule generated successfully")
                self.on_view_change()
                self.display_schedule()
                self.update_status()
                messagebox.showinfo("Success", f"Generated {len(self.schedule)} classes using CSP")
            else:
                self.progress_label.config(text="Failed - Could not satisfy all constraints")
                messagebox.showerror("Error", "Could not generate valid schedule with current constraints.\nTry: More classrooms, fewer courses, or relaxed availability.")
        
        except Exception as e:
            self.progress_label.config(text="Error occurred")
            messagebox.showerror("Error", f"Schedule generation failed: {str(e)}")
    
    def build_lecture_requirements(self):
        """Build list of all required lectures"""
        requirements = []
        
        for course in self.courses:
            course_name = course['course_name']
            subjects = [s.strip() for s in course.get('subjects', '').split(',')]
            
            for subject in subjects:
                is_lab = 'lab' in subject.lower()
                
                if is_lab:
                    # Add 2-hour lab (2 consecutive slots)
                    requirements.append({
                        'course': course_name,
                        'subject': f"{subject} (Lab)",
                        'type': 'lab',
                        'duration': 2
                    })
                    # Add 2 regular lectures
                    for i in range(2):
                        requirements.append({
                            'course': course_name,
                            'subject': subject,
                            'type': 'lecture',
                            'duration': 1
                        })
                else:
                    # Add 3 regular lectures
                    for i in range(3):
                        requirements.append({
                            'course': course_name,
                            'subject': subject,
                            'type': 'lecture',
                            'duration': 1
                        })
        
        return requirements
    
    def backtrack(self, index, requirements, teacher_subjects, grid, assignments, depth=0):
        """CSP backtracking algorithm with better heuristics"""
        
        # Base case: all lectures scheduled
        if index >= len(requirements):
            return True
        
        # Timeout protection - if stuck too long, try relaxing constraints
        if depth > 10000:
            return False
        
        lecture = requirements[index]
        
        # Update progress
        if index % 3 == 0:
            progress = (index / len(requirements)) * 100
            self.progress_label.config(text=f"Scheduling: {progress:.0f}% ({index}/{len(requirements)})")
            self.root.update()
        
        # Get subject without (Lab) suffix
        subject_clean = lecture['subject'].replace(' (Lab)', '')
        available_teachers = teacher_subjects.get(subject_clean, [])
        
        if not available_teachers:
            # Skip if no teacher available for this subject
            return self.backtrack(index + 1, requirements, teacher_subjects, grid, assignments, depth + 1)
        
        # Get possible assignments sorted by preference (MRV - Most Constrained First)
        possible_assignments = []
        for teacher in available_teachers:
            for day in self.days:
                for time_idx in range(len(self.time_slots) - lecture['duration'] + 1):
                    for classroom in self.classrooms:
                        classroom_name = classroom['classroom_name']
                        
                        if self.can_use_classroom(classroom_name, day, time_idx, 
                                                 lecture['duration'], grid):
                            if self.is_valid_assignment_relaxed(lecture, teacher, day, 
                                                               time_idx, grid, assignments):
                                # Calculate preference score (higher is better)
                                score = self.calculate_assignment_score(lecture, teacher, day, 
                                                                       time_idx, assignments)
                                possible_assignments.append({
                                    'teacher': teacher,
                                    'day': day,
                                    'time_idx': time_idx,
                                    'classroom': classroom_name,
                                    'score': score
                                })
        
        # Sort by score (try best options first)
        possible_assignments.sort(key=lambda x: x['score'], reverse=True)
        
        # Try assignments in order of preference
        for assign_data in possible_assignments:
            teacher = assign_data['teacher']
            day = assign_data['day']
            time_idx = assign_data['time_idx']
            classroom_name = assign_data['classroom']
            start_time = self.time_slots[time_idx]
            
            # Make assignment
            assignment = {
                'course': lecture['course'],
                'subject': lecture['subject'],
                'teacher': teacher,
                'day': day,
                'time': start_time,
                'classroom': classroom_name,
                'type': lecture['type']
            }
            
            self.make_assignment(assignment, lecture['duration'], time_idx, grid)
            assignments.append(assignment)
            
            # Recurse
            if self.backtrack(index + 1, requirements, teacher_subjects, 
                            grid, assignments, depth + 1):
                return True
            
            # Backtrack
            self.undo_assignment(assignment, lecture['duration'], time_idx, grid)
            assignments.pop()
        
        return False
    
    def calculate_assignment_score(self, lecture, teacher, day, time_idx, assignments):
        """Calculate preference score for an assignment (higher is better)"""
        score = 0
        
        # Calculate current course day distribution
        course_days = {}
        for a in assignments:
            if a['course'] == lecture['course']:
                course_days[a['day']] = course_days.get(a['day'], 0) + a.get('duration', 1)
        
        current_day_hours = course_days.get(day, 0)
        
        # IMPORTANT: Discourage days with less than 2 hours total
        if current_day_hours == 0:
            # Starting a new day
            if len(course_days) > 0:
                # Already have classes on other days - be careful about starting new days
                score -= 30  # Penalty for spreading too thin
            score += 20  # But still prefer spreading across days
        elif current_day_hours == 1:
            # Only 1 hour on this day so far - adding more is GOOD
            score += 40  # Strong bonus to reach 2+ hours
        elif current_day_hours >= 2:
            # Already have 2+ hours - adding more is acceptable
            score += 15
        
        # Prefer reasonable daily counts (in terms of number of classes)
        daily_count = sum(1 for a in assignments if a['course'] == lecture['course'] and a['day'] == day)
        if daily_count < 4:
            score += 20
        elif daily_count < 6:
            score += 10
        
        # Check teacher weekly hours and discourage overloading
        teacher_weekly_hours = sum(
            a.get('duration', 1) for a in assignments if a['teacher'] == teacher
        )
        if teacher_weekly_hours < 15:
            score += 25  # Good - teacher not overloaded
        elif teacher_weekly_hours < 18:
            score += 10  # Acceptable
        else:
            score -= 20  # Getting close to limit
        
        # Check teacher daily hours - avoid days with just 1 hour
        teacher_day_hours = sum(
            a.get('duration', 1) for a in assignments 
            if a['teacher'] == teacher and a['day'] == day
        )
        if teacher_day_hours == 0:
            # Starting new day for teacher
            score += 5
        elif teacher_day_hours == 1:
            # Teacher has 1 hour on this day - adding more is good
            score += 30
        elif teacher_day_hours >= 2 and teacher_day_hours < 5:
            # Good range for teacher
            score += 20
        elif teacher_day_hours >= 5:
            # Too many hours in one day for teacher
            score -= 15
        
        # Prefer spreading across days
        course_days_count = len(course_days)
        if day not in course_days and course_days_count < 4:
            score += 25  # New day is good (up to 4 days)
        
        # Prefer middle time slots over very early or very late
        if 2 <= time_idx <= 6:
            score += 10
        
        # Prefer teacher availability if specified
        if teacher in self.teacher_availability:
            avail = self.teacher_availability[teacher]
            start_time = self.time_slots[time_idx]
            if (not avail['days'] or day in avail['days']) and \
               (not avail['times'] or start_time in avail['times']):
                score += 30
        
        return score
    
    def is_valid_assignment_relaxed(self, lecture, teacher, day, time_idx, grid, assignments):
        """Check if assignment satisfies HARD constraints only (more flexible)"""
        
        # Check for conflicts in all time slots this lecture would occupy
        for i in range(lecture['duration']):
            time = self.time_slots[time_idx + i]
            
            # HARD: Check teacher conflict
            for existing in grid[day][time]:
                if existing['teacher'] == teacher:
                    return False
                
                # HARD: Check course conflict
                if existing['course'] == lecture['course']:
                    return False
        
        # HARD: Check teacher weekly hour limit (20 hours max)
        teacher_weekly_hours = sum(
            a.get('duration', 1) for a in assignments if a['teacher'] == teacher
        )
        if teacher_weekly_hours + lecture['duration'] > 20:
            return False
        
        # HARD: Check break requirement (>4 hours needs at least 1 break)
        if not self.check_break_constraint(lecture, day, time_idx, assignments):
            return False
        
        # SOFT: Check daily lecture limit (allow up to 8, prefer 6)
        daily_count = sum(1 for a in assignments 
                         if a['course'] == lecture['course'] and a['day'] == day)
        if daily_count >= 8:  # Hard limit
            return False
        
        # SOFT: Avoid scheduling single day with less than 2 hours for a course
        # Only apply this check if course already has classes on other days
        course_days = {}
        for a in assignments:
            if a['course'] == lecture['course']:
                course_days[a['day']] = course_days.get(a['day'], 0) + a.get('duration', 1)
        
        # If this day already has some classes, check if adding this would help
        current_day_hours = course_days.get(day, 0)
        if current_day_hours == 0 and len(course_days) > 0:
            # Starting a new day - only allow if we'll get at least 2 hours
            # But we need to be flexible during backtracking
            pass
        
        return True
    
    def check_break_constraint(self, lecture, day, time_idx, assignments):
        """
        HARD CONSTRAINT: If a course has more than 4 hours on a day, must have at least 1 break.
        Returns True if constraint is satisfied, False otherwise.
        """
        course = lecture['course']
        
        # Get all time indices for this course on this day
        course_times_on_day = []
        for a in assignments:
            if a['course'] == course and a['day'] == day:
                existing_time_idx = self.time_slots.index(a['time'])
                duration = a.get('duration', 1)
                for i in range(duration):
                    course_times_on_day.append(existing_time_idx + i)
        
        # Add the new lecture's time indices
        new_times = []
        for i in range(lecture['duration']):
            new_times.append(time_idx + i)
        
        all_times = sorted(set(course_times_on_day + new_times))
        
        # If 4 or fewer hours, no break needed
        if len(all_times) <= 4:
            return True
        
        # More than 4 hours - need at least one break
        # Check if there's at least one gap (break) in the schedule
        has_break = False
        for i in range(len(all_times) - 1):
            if all_times[i + 1] - all_times[i] > 1:
                # There's a gap (break)
                has_break = True
                break
        
        return has_break
    
    def calculate_break_quality_score(self, lecture, day, time_idx, assignments):
        """
        Calculate score for break placement quality.
        Prefers breaks in the middle, not with only 1 lecture before/after.
        """
        score = 0
        course = lecture['course']
        
        # Get all time indices for this course on this day (including new one)
        course_times_on_day = []
        for a in assignments:
            if a['course'] == course and a['day'] == day:
                existing_time_idx = self.time_slots.index(a['time'])
                duration = a.get('duration', 1)
                for i in range(duration):
                    course_times_on_day.append(existing_time_idx + i)
        
        for i in range(lecture['duration']):
            course_times_on_day.append(time_idx + i)
        
        all_times = sorted(set(course_times_on_day))
        
        if len(all_times) <= 4:
            # No break needed, perfect
            return 20
        
        # Find breaks (gaps in schedule)
        breaks = []
        for i in range(len(all_times) - 1):
            gap = all_times[i + 1] - all_times[i]
            if gap > 1:
                break_position = i  # Position after which break occurs
                lectures_before = i + 1
                lectures_after = len(all_times) - (i + 1)
                breaks.append({
                    'position': break_position,
                    'before': lectures_before,
                    'after': lectures_after,
                    'gap_size': gap - 1
                })
        
        if not breaks:
            # More than 4 hours but no break - this should be caught by hard constraint
            return -100
        
        # Evaluate break quality
        for brk in breaks:
            lectures_before = brk['before']
            lectures_after = brk['after']
            
            # IDEAL: Break in the middle with 2+ lectures on each side
            if lectures_before >= 2 and lectures_after >= 2:
                # Calculate how balanced it is
                balance = min(lectures_before, lectures_after) / max(lectures_before, lectures_after)
                score += 50 * balance  # Up to +50 for perfectly balanced
            
            # GOOD: At least 2 on one side, any amount on other
            elif lectures_before >= 2 or lectures_after >= 2:
                score += 20
            
            # BAD: Only 1 lecture before or after break
            elif lectures_before == 1 or lectures_after == 1:
                score -= 100  # Penalty for poor break placement
            
            # Prefer single longer break over multiple small breaks
            if len(breaks) == 1:
                score += 15
        
        return score
    
    def is_time_available(self, lecture, teacher, day, time_idx, grid):
        """Helper to check if a time slot is available"""
        for i in range(lecture['duration']):
            if time_idx + i >= len(self.time_slots):
                return False
            time = self.time_slots[time_idx + i]
            for existing in grid[day][time]:
                if existing['teacher'] == teacher or existing['course'] == lecture['course']:
                    return False
        return True
    
    def can_use_classroom(self, classroom, day, time_idx, duration, grid):
        """Check if classroom is available for duration"""
        for i in range(duration):
            time = self.time_slots[time_idx + i]
            for existing in grid[day][time]:
                if existing['classroom'] == classroom:
                    return False
        return True
    
    def make_assignment(self, assignment, duration, time_idx, grid):
        """Add assignment to grid"""
        day = assignment['day']
        # Store duration in assignment for tracking
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
        """Remove assignment from grid"""
        day = assignment['day']
        for i in range(duration):
            time = self.time_slots[time_idx + i]
            grid[day][time] = [
                e for e in grid[day][time]
                if not (e['course'] == assignment['course'] and 
                       e['subject'] == assignment['subject'] and
                       e['teacher'] == assignment['teacher'])
            ]
    
    # ==================== END CSP ALGORITHM ====================
    
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
                    font=("Arial", 12), bg="white", fg="#7f8c8d",
                    padx=20, pady=20).grid(row=0, column=0)
            return
        
        tk.Label(self.timetable_frame, text="Time", font=("Arial", 10, "bold"),
                bg="#34495e", fg="white", padx=8, pady=8, relief=tk.RAISED, bd=2,
                width=12).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        
        for col_idx, day in enumerate(self.days, start=1):
            tk.Label(self.timetable_frame, text=day, font=("Arial", 10, "bold"),
                    bg="#34495e", fg="white", padx=8, pady=8, relief=tk.RAISED, bd=2,
                    width=18).grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
        
        # Build schedule map - handle multiple entries in same slot
        schedule_map = defaultdict(list)
        for entry in schedule:
            key = (entry['day'], entry['time'])
            schedule_map[key].append(entry)
        
        for row_idx, time_slot in enumerate(self.time_slots, start=1):
            tk.Label(self.timetable_frame, text=time_slot, font=("Arial", 9, "bold"),
                    bg="#ecf0f1", fg="#2c3e50", padx=5, pady=5, relief=tk.RAISED, bd=2,
                    anchor="center").grid(row=row_idx, column=0, sticky="nsew", padx=1, pady=1)
            
            for col_idx, day in enumerate(self.days, start=1):
                key = (day, time_slot)
                
                if key in schedule_map and schedule_map[key]:
                    entries = schedule_map[key]
                    
                    if len(entries) > 1:
                        # Multiple entries in same slot
                        cell_text = "\n---\n".join([self.format_cell_text(e, view_type) for e in entries])
                        bg_color = "#fff3cd"  # Yellow for conflicts
                    else:
                        entry = entries[0]
                        cell_text = self.format_cell_text(entry, view_type)
                        if entry.get('type') == 'lab':
                            bg_color = "#e8daef"  # Purple for labs
                        elif view_type == "course":
                            bg_color = "#d5f4e6"
                        elif view_type == "teacher":
                            bg_color = "#d6eaf8"
                        elif view_type == "classroom":
                            bg_color = "#fadbd8"
                        else:
                            bg_color = "white"
                    
                    cell = tk.Label(self.timetable_frame, text=cell_text,
                                  font=("Arial", 8), bg=bg_color, fg="black",
                                  padx=5, pady=8, relief=tk.RAISED, bd=2,
                                  anchor="center", justify="center", wraplength=140)
                else:
                    cell = tk.Label(self.timetable_frame, text="—",
                                  font=("Arial", 10), bg="white", fg="#95a5a6",
                                  padx=5, pady=8, relief=tk.SUNKEN, bd=1,
                                  anchor="center")
                
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
        
        for i in range(len(self.time_slots) + 1):
            self.timetable_frame.grid_rowconfigure(i, weight=1)
        for i in range(len(self.days) + 1):
            self.timetable_frame.grid_columnconfigure(i, weight=1)
    
    def format_cell_text(self, entry, view_type):
        """Format cell text based on view type"""
        lab_indicator = " [LAB]" if entry.get('type') == 'lab' else ""
        
        if view_type == "course":
            return f"{entry['subject']}{lab_indicator}\n{entry['teacher']}\n{entry['classroom']}"
        elif view_type == "teacher":
            return f"{entry['course']}\n{entry['subject']}{lab_indicator}\n{entry['classroom']}"
        elif view_type == "classroom":
            return f"{entry['course']}\n{entry['subject']}{lab_indicator}\n{entry['teacher']}"
        return ""
    
    def display_master_schedule(self):
        headers = ['Day', 'Time', 'Course', 'Subject', 'Teacher', 'Classroom', 'Type']
        for col_idx, header in enumerate(headers):
            tk.Label(self.timetable_frame, text=header, font=("Arial", 10, "bold"),
                    bg="#34495e", fg="white", padx=10, pady=10, relief=tk.RAISED, bd=2,
                    width=14).grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
        
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
            
            for col_idx, value in enumerate(values):
                tk.Label(self.timetable_frame, text=value, font=("Arial", 9),
                        bg=bg_color, fg="black", padx=8, pady=8, relief=tk.FLAT,
                        anchor="w", wraplength=120).grid(row=row_idx, column=col_idx, 
                                                         sticky="nsew", padx=1, pady=1)
        
        for i in range(len(sorted_schedule) + 1):
            self.timetable_frame.grid_rowconfigure(i, weight=0)
        for i in range(len(headers)):
            self.timetable_frame.grid_columnconfigure(i, weight=1)
    
    def export_schedule(self):
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
                with open(filename, 'w', newline='') as f:
                    fieldnames = ['day', 'time', 'course', 'subject', 'teacher', 'classroom', 'type']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for entry in filtered_schedule:
                        writer.writerow(entry)
                
                messagebox.showinfo("Success", "Schedule exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TimetableScheduler(root)
    root.mainloop()