import sys
import math
import os
import glob
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List

                     
USE_TTKB = False
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    USE_TTKB = True
except Exception:
    USE_TTKB = False

HAVE_MPL = True
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    HAVE_MPL = False

from models import GradeBook, Assessment
from calculations import compute_stats

                     
# Creates the main window, using ttkbootstrap if available
def create_root():
    if USE_TTKB:
        root = tb.Window(themename="flatly")
    else:
        root = tk.Tk()
    return root

                             
# Main application class handling UI and logic
class App:
    # Initializes the application UI and state
    def __init__(self, root):
        self.root = root
        self.gb = GradeBook()
        self.pass_mark = tk.DoubleVar(value=50.0)
        self.current_filename = None

                                                    
        # Define paths for saves and resources
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle (PyInstaller)
            # The executable is the path to the .exe file
            base_dir = os.path.dirname(sys.executable)
            # Resources are in the temp folder _MEIPASS
            resource_dir = getattr(sys, '_MEIPASS', base_dir)
        else:
            # Normal python execution
            base_dir = os.path.dirname(os.path.abspath(__file__))
            resource_dir = base_dir

        # Determine where to save data
        # If we are in a read-only directory (common in Program Files), fallback to AppData
        try:
            test_file = os.path.join(base_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            # If successful, we can write here
            self.saves_path = os.path.join(base_dir, "saves")
        except OSError:
            # Fallback to AppData
            app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            self.saves_path = os.path.join(app_data, "GradeCalculator", "saves")
        
        if not os.path.exists(self.saves_path):
            try:
                os.makedirs(self.saves_path)
            except OSError:
                pass

        if USE_TTKB:
                                           
            self.root.title("Uni Grade Calculator")
        else:
            style = ttk.Style()
                                                    
            if "clam" in style.theme_names():
                style.theme_use("clam")
            self.root.title("Uni Grade Calculator")
        
                              
                  
        try:
            # Icons might be bundled, so look in resource_dir
            icon_path_png = os.path.join(resource_dir, "icon.png")
            icon_path_ico = os.path.join(resource_dir, "icon.ico")
            
                                                                                             
            if os.path.exists(icon_path_ico):
                self.root.iconbitmap(icon_path_ico)
            
                                                                   
            if os.path.exists(icon_path_png):
                self.app_icon = tk.PhotoImage(file=icon_path_png)
                self.root.wm_iconphoto(True, self.app_icon)
            elif not os.path.exists(icon_path_ico):
                           
                self.blank_icon = tk.PhotoImage(width=1, height=1)
                self.root.wm_iconphoto(True, self.blank_icon)
        except Exception:
            pass

                              
        self.pad = {"padx": 8, "pady": 6}

                          
        if USE_TTKB:
            paned = tb.Panedwindow(self.root, orient="horizontal")
        else:
            paned = ttk.Panedwindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True)

                                   
        left = ttk.Frame(paned)
        paned.add(left, weight=1)

                               
        right = ttk.Frame(paned)
        paned.add(right, weight=3)

                                    
        hdr = ttk.Frame(left)
        hdr.pack(fill="x", **self.pad)

                                                             
        self.file_var = tk.StringVar()
        self.rename_var = tk.StringVar()
        
                                                                
        self.file_ctl_frame = ttk.Frame(hdr)
        
                                                          
                                             
                                 
                                 

        if USE_TTKB:
            self.file_combo = tb.Combobox(self.file_ctl_frame, textvariable=self.file_var, state="readonly", width=1)
            self.file_entry = tb.Entry(self.file_ctl_frame, textvariable=self.rename_var, width=1)
                                            
            self.new_file_btn = tb.Button(hdr, text="+", bootstyle=PRIMARY, command=self.new_file, width=3)
            self.edit_file_btn = tb.Button(hdr, text="Edit", bootstyle=SECONDARY, command=self.toggle_rename_mode)
            self.del_file_btn = tb.Button(hdr, text="Delete", bootstyle=DANGER, command=self.delete_current_file)
        else:
            self.file_combo = ttk.Combobox(self.file_ctl_frame, textvariable=self.file_var, state="readonly", width=1)
            self.file_entry = ttk.Entry(self.file_ctl_frame, textvariable=self.rename_var, width=1)
            self.new_file_btn = ttk.Button(hdr, text="+", command=self.new_file, width=3)
            self.edit_file_btn = ttk.Button(hdr, text="Edit", command=self.toggle_rename_mode)
            self.del_file_btn = ttk.Button(hdr, text="Delete", command=self.delete_current_file)

                              
                                                                      
        self.new_file_btn.pack(side="left", padx=2)
        self.del_file_btn.pack(side="right", padx=2)             
        self.edit_file_btn.pack(side="right", padx=2)             
        
                                                         
        self.file_ctl_frame.pack(side="left", fill="x", expand=True)
                       
        self.file_combo.pack(side="left", fill="x", expand=True)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)
        self.file_entry.bind("<Return>", lambda e: self.confirm_rename())
        
        self.rename_mode = False
        
                                        
        self.file_delete_confirm_pending = False
        self.file_delete_timer = None
        
                               
        self.refresh_file_list()

                                                                
        subj_ctl = ttk.Frame(left)
        subj_ctl.pack(fill="x", **self.pad)

        if USE_TTKB:
                           
            ttk.Label(subj_ctl, text="Subjects", font=("", 10, "bold")).pack(side="top", anchor="w", padx=4, pady=(0, 4))
            
            btn_frame = ttk.Frame(subj_ctl)
            btn_frame.pack(fill="x")
            self.add_subj_btn = tb.Button(btn_frame, text="Add", bootstyle=SUCCESS, command=self.add_subject)
            self.ren_subj_btn = tb.Button(btn_frame, text="Rename", bootstyle=SECONDARY, command=self.start_inline_rename)
            self.del_subj_btn = tb.Button(btn_frame, text="Delete", bootstyle=DANGER, command=self.delete_subject)
        else:
                           
            ttk.Label(subj_ctl, text="Subjects", font=("", 10, "bold")).pack(side="top", anchor="w", padx=4, pady=(0, 4))
            
            btn_frame = ttk.Frame(subj_ctl)
            btn_frame.pack(fill="x")
            self.add_subj_btn = ttk.Button(btn_frame, text="Add", command=self.add_subject)
            self.ren_subj_btn = ttk.Button(btn_frame, text="Rename", command=self.start_inline_rename)
            self.del_subj_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_subject)

                                                                                           
                                                                         
                                                                           
        self.add_subj_btn.pack(side="left", padx=4, expand=True, fill="x")
        self.ren_subj_btn.pack(side="left", padx=4, expand=True, fill="x")
        self.del_subj_btn.pack(side="left", padx=4, expand=True, fill="x")
        
                                   
        self.delete_confirm_pending = False
        self.delete_timer = None
        
                           
        self.inline_entry = None

                         
        self.subject_list = tk.Listbox(left, height=12, exportselection=False)
        self.subject_list.pack(fill="both", expand=True, **self.pad)
        self.subject_list.bind("<<ListboxSelect>>", self.on_subject_select)

                                                      
                                  
                                           
                               

                                     
        topbar = ttk.Frame(right)
        topbar.pack(fill="x", **self.pad)

        self.sel_subject_var = tk.StringVar(value="—")
        ttk.Label(topbar, text="Subject:", font=("", 11)).pack(side="left")
        self.sel_subject_lbl = ttk.Label(topbar, textvariable=self.sel_subject_var, font=("", 11, "bold"))
        self.sel_subject_lbl.pack(side="left", padx=6)

        ttk.Label(topbar, text="Pass ≥").pack(side="left", padx=(20, 4))
        pass_spin = ttk.Spinbox(topbar, from_=0, to=100, textvariable=self.pass_mark, width=5, increment=1)
        pass_spin.pack(side="left")
        ttk.Label(topbar, text="%").pack(side="left")

                             
        columns = ("name", "kind", "weight", "mark")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=12)
        self.tree.heading("name", text="Name")
        self.tree.heading("kind", text="Type")
        self.tree.heading("weight", text="Weight %")
        self.tree.heading("mark", text="Mark %")

        self.tree.column("name", width=220, anchor="w")
        self.tree.column("kind", width=130, anchor="w")
        self.tree.column("weight", width=90, anchor="center")
        self.tree.column("mark", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True, **self.pad)

                            
        ab = ttk.Frame(right)
        ab.pack(fill="x", **self.pad)

        if USE_TTKB:
            add_btn = tb.Button(ab, text="Add Assessment", bootstyle=SUCCESS, command=self.add_assessment_dialog)
            edit_btn = tb.Button(ab, text="Edit", bootstyle=SECONDARY, command=self.edit_assessment_dialog)
            del_btn = tb.Button(ab, text="Delete", bootstyle=DANGER, command=self.delete_assessment)
        else:
            add_btn = ttk.Button(ab, text="Add Assessment", command=self.add_assessment_dialog)
            edit_btn = ttk.Button(ab, text="Edit", command=self.edit_assessment_dialog)
            del_btn = ttk.Button(ab, text="Delete", command=self.delete_assessment)
        add_btn.pack(side="left")
        edit_btn.pack(side="left", padx=6)
        del_btn.pack(side="left")

                     
        stats = ttk.LabelFrame(right, text="Subject Stats")
        stats.pack(fill="x", **self.pad)

        self.var_completed_weight = tk.StringVar(value="0%")
        self.var_planned_weight = tk.StringVar(value="0%")
        self.var_contribution = tk.StringVar(value="0.00%")
        self.var_current_avg = tk.StringVar(value="—")
        self.var_needed = tk.StringVar(value="—")
        self.var_remaining_weight = tk.StringVar(value="100%")

        def small(lbl, valvar):
            row = ttk.Frame(stats); row.pack(fill="x", padx=8, pady=3)
            ttk.Label(row, text=lbl, width=28, anchor="w").pack(side="left")
            ttk.Label(row, textvariable=valvar, font=("", 10, "bold")).pack(side="left")

        small("Completed weight:", self.var_completed_weight)
        small("Planned weight (sum of weights):", self.var_planned_weight)
        small("Contribution to final so far:", self.var_contribution)
        small("Current avg on completed items:", self.var_current_avg)
        small("Required avg on remaining to pass:", self.var_needed)
        small("Remaining planned weight:", self.var_remaining_weight)



                       
        self.graph_frame = ttk.LabelFrame(right, text="Progress Overview")
        self.graph_frame.pack(fill="both", expand=False, padx=8, pady=(0,10))

        if HAVE_MPL:
            self.graph_fig = Figure(figsize=(6.0, 1.8), dpi=100)
            self.graph_ax = self.graph_fig.add_subplot(111)
            self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=self.graph_frame)
            self.graph_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        else:
            self.graph_placeholder = ttk.Label(self.graph_frame, text="Install matplotlib to see the progress graph (pip install matplotlib)")
            self.graph_placeholder.pack(fill="x", padx=8, pady=8)

                             
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

                                                                      
        self.handle_startup_load()

                                  
    # Handles initial data loading on startup
    def handle_startup_load(self):
                                        
        self.root.withdraw()

        try:
            json_files = glob.glob(os.path.join(self.saves_path, "*.json"))
            
            if not json_files:
                                                        
                self.load_dummy_data()
            else:
                                                              
                                                               
                json_files.sort(key=os.path.getmtime, reverse=True)
                last_file = json_files[0]
                self.load_custom_file(last_file)
        finally:
                                                                    
            self.root.deiconify()

                         
    # Loads a specific JSON file into the gradebook
    def load_custom_file(self, filepath):
        try:
            content = ""
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            if not content:
                                              
                self.gb.subjects.clear()
            else:
                self.gb.load_json(content)
                
            self.current_filename = filepath
            self.refresh_subject_list()
                                                             
            self.file_var.set(os.path.basename(filepath).replace(".json", ""))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file '{os.path.basename(filepath)}':\n{e}\nLoading default data.")
            self.load_dummy_data()

                        
    # Creates example data for first-time users
    def load_dummy_data(self):
        if not self.gb.subjects:
            try:
                self.gb.add_subject("Example: Programming 101")
                self.gb.add_assessment("Example: Programming 101", Assessment("Assignment 1", "Assignment", 20, 75))
                self.gb.add_assessment("Example: Programming 101", Assessment("Midterm", "Exam", 30, None))
                self.gb.add_assessment("Example: Programming 101", Assessment("Final", "Exam", 50, None))
                self.refresh_subject_list(select="Example: Programming 101")
            except Exception:
                pass

    # Shows dialog to choose from multiple save files
    def ask_user_for_save_file(self, files: List[str]):
                                                                                      
                                                                                  
                                                                                        
        
                                           
        file_map = {os.path.basename(f): f for f in files}
        
        dlg = FileSelectionDialog(self.root, list(file_map.keys()))
        self.root.wait_window(dlg.top)
        
        if dlg.selected_filename and dlg.selected_filename in file_map:
            self.load_custom_file(file_map[dlg.selected_filename])
        else:
                       
            self.load_dummy_data()

                             
    # Updates the list of subjects in the UI
    def refresh_subject_list(self, select: Optional[str] = None):
        self.subject_list.delete(0, tk.END)
        sorted_titles = sorted(self.gb.subjects.keys(), key=lambda s: s.lower())
        for title in sorted_titles:
            self.subject_list.insert(tk.END, title)

        idx_to_select = 0
        if select and select in self.gb.subjects:
            idx_to_select = sorted_titles.index(select)

        if self.subject_list.size() > 0:
            self.subject_list.select_clear(0, tk.END)
            self.subject_list.select_set(idx_to_select)
            self.subject_list.activate(idx_to_select)
                                                                                  
            self.on_subject_select()
        else:
            self.sel_subject_var.set("—")
            for i in self.tree.get_children():
                self.tree.delete(i)
            self.update_stats_panel(None)

                                           
    # adds a new subject with a unique name
    def add_subject(self):
                                     
        base = "New Subject"
        name = base
        count = 1
        while name in self.gb.subjects:
            name = f"{base} ({count})"
            count += 1
            
        try:
            self.gb.add_subject(name)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
            
        self.refresh_subject_list(select=name)
        self.save_file(silent=True)
                                  
        self.start_inline_rename()

    # Starts the inline renaming process for a subject
    def start_inline_rename(self):
        subj = self.current_subject_title()
        if not subj:
            messagebox.showwarning("No subject", "Select a subject first.")
            return

                                               
        sel = self.subject_list.curselection()
        if not sel: return
        idx = sel[0]
        
        try:
            bbox = self.subject_list.bbox(idx)                      
            if not bbox: return
        except Exception:
            return

        x, y, w, h = bbox
        
                                  
        if self.inline_entry:
            self.inline_entry.destroy()
            
                                                                                
                                                              
        try:
            cur_font = self.subject_list.cget("font")
        except:
            cur_font = ("TkDefaultFont",)
            
        self.inline_entry = tk.Entry(self.subject_list, relief="flat", borderwidth=0, highlightthickness=1, font=cur_font)
            
                                                                                   
        list_width = self.subject_list.winfo_width()
        
        req_h = h                    
        req_y = y                 
        
                                    
        req_w = max(list_width - x - 4, 100)
        
        self.inline_entry.place(x=x, y=req_y, width=req_w, height=req_h)
        self.inline_entry.lift() 
        self.inline_entry.insert(0, subj)
        self.inline_entry.select_range(0, tk.END)
        self.inline_entry.focus_set()
        
        self.inline_entry.bind("<Return>", lambda e: self.commit_inline_rename(subj))
        self.inline_entry.bind("<Escape>", lambda e: self.cancel_inline_rename())
        self.inline_entry.bind("<FocusOut>", lambda e: self.cancel_inline_rename())

    # Saves the new name after renaming a subject
    def commit_inline_rename(self, old_name):
        new_name = self.inline_entry.get().strip()
        self.inline_entry.destroy()
        self.inline_entry = None
        
        if not new_name or new_name == old_name:
            return

        try:
            self.gb.rename_subject(old_name, new_name)
        except ValueError as e:
                                                                  
            messagebox.showerror("Error", str(e))
            self.refresh_subject_list(select=old_name)
            return

        self.refresh_subject_list(select=new_name)
        self.save_file(silent=True)

    # Cancels the inline renaming process
    def cancel_inline_rename(self):
        if self.inline_entry:
            self.inline_entry.destroy()
            self.inline_entry = None

                              
    # Deletes the currently selected subject
    def delete_subject(self):
        subj = self.current_subject_title()
        if not subj:
            messagebox.showwarning("No subject", "Select a subject to delete.")
            return
            
        if not self.delete_confirm_pending:
                                                  
            self.delete_confirm_pending = True
            self.del_subj_btn.configure(text="Confirm")
                                        
            self.delete_timer = self.root.after(2000, self.reset_delete_btn)
        else:
                                          
            self.gb.remove_subject(subj)
            self.refresh_subject_list()
            self.save_file(silent=True)
            self.reset_delete_btn()
    
    # Resets the delete button state
    def reset_delete_btn(self):
        self.delete_confirm_pending = False
        if self.delete_timer:
            self.root.after_cancel(self.delete_timer)
            self.delete_timer = None
        self.del_subj_btn.configure(text="Delete")

    # Gets the title of the currently selected subject
    def current_subject_title(self) -> Optional[str]:
        sel = self.subject_list.curselection()
        if not sel:
            return None
        return self.subject_list.get(sel[0])

                             
    # Handles subject selection change
    def on_subject_select(self, _evt=None):
        subj = self.current_subject_title()
        if not subj:
            return
        if subj:                                                                      
            self.reset_delete_btn()
                                                
            self.cancel_inline_rename()
        
        self.sel_subject_var.set(subj if subj else "—")
        for i in self.tree.get_children():
            self.tree.delete(i)
        if subj:
            for a in self.gb.subjects[subj].assessments:
                mark_txt = "—" if a.mark is None else f"{a.mark:.2f}"
                self.tree.insert("", tk.END, values=(a.name, a.kind, f"{a.weight:.2f}", mark_txt))
        self.update_stats_panel(subj)
        self.render_subject_graph()

                                 
    # Opens dialog to add a new assessment
    def add_assessment_dialog(self):
        subj = self.current_subject_title()
        if not subj:
            messagebox.showwarning("No subject", "Select a subject first.")
            return
        dlg = AssessmentDialog(self.root, title="Add Assessment")
        self.root.wait_window(dlg.top)
        if dlg.result:
            a = dlg.result
            try:
                self.gb.add_assessment(subj, a)
                self.on_subject_select()
                self.save_file(silent=True)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # Gets index of selected assessment in the treeview
    def selected_assessment_index(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.index(sel[0])

    # Opens dialog to edit selected assessment
    def edit_assessment_dialog(self):
        subj = self.current_subject_title()
        idx = self.selected_assessment_index()
        if not subj or idx is None:
            messagebox.showwarning("No selection", "Select an assessment to edit.")
            return
        a = self.gb.subjects[subj].assessments[idx]
        dlg = AssessmentDialog(self.root, title="Edit Assessment", initial=a)
        self.root.wait_window(dlg.top)
        if dlg.result:
            self.gb.subjects[subj].assessments[idx] = dlg.result
            self.on_subject_select()
            self.save_file(silent=True)

    # Deletes the selected assessment
    def delete_assessment(self):
        subj = self.current_subject_title()
        idx = self.selected_assessment_index()
        if not subj or idx is None:
            messagebox.showwarning("No selection", "Select an assessment to delete.")
            return
        if messagebox.askyesno("Delete", "Delete selected assessment?"):
            self.gb.delete_assessment(subj, idx)
            self.on_subject_select()
            self.save_file(silent=True)

                                
    # Updates the statistics panel for a subject
    def update_stats_panel(self, subj_title: Optional[str]):
        if not subj_title:
            self.var_completed_weight.set("0%")
            self.var_planned_weight.set("0%")
            self.var_contribution.set("0.00%")
            self.var_current_avg.set("—")
            self.var_needed.set("—")
            self.var_remaining_weight.set("100%")
            if HAVE_MPL:
                if hasattr(self, 'graph_ax'): self.graph_ax.clear()
                if hasattr(self, 'graph_canvas'): self.graph_canvas.draw()
            return

        subj = self.gb.subjects[subj_title]
        stats = compute_stats(subj.assessments, pass_mark=self.pass_mark.get())

        self.var_completed_weight.set(f"{stats['completed_weight']:.2f}%")
        self.var_planned_weight.set(f"{stats['planned_weight']:.2f}%")
        self.var_contribution.set(f"{stats['contributed']:.2f}%")

        if stats["current_avg_completed"] is None:
            self.var_current_avg.set("—")
        else:
            self.var_current_avg.set(f"{stats['current_avg_completed']:.2f}%")

        if stats["needed_avg_remaining"] == math.inf:
            self.var_needed.set("Impossible (no remaining weight)")
        else:
            self.var_needed.set(f"{stats['needed_avg_remaining']:.2f}%")

        self.var_remaining_weight.set(f"{stats['remaining_planned_weight']:.2f}%")
        self.render_subject_graph()

                          
    # Draws the progress bar graph
    def render_subject_graph(self):
        subj_title = self.current_subject_title()
        if not subj_title or not HAVE_MPL:
            return

        subj = self.gb.subjects[subj_title]
        stats = compute_stats(subj.assessments, pass_mark=self.pass_mark.get())

        planned = max(0.0, min(stats["planned_weight"], 100.0))
        completed = max(0.0, min(stats["completed_weight"], 100.0))
        contribution = max(0.0, min(stats["contributed"], 100.0))

        seg_contrib = max(0.0, min(contribution, 100.0))
        seg_completed_loss = max(0.0, min(completed - contribution, 100.0 - seg_contrib))
        seg_planned_remaining = max(0.0, min(planned - completed, 100.0 - seg_contrib - seg_completed_loss))

        col_contrib = "#B6E51C"
        col_completed_loss = "#00A8E8"
        col_planned_remaining = "#3F51B5"
        border_color = "#000000"

        ax = self.graph_ax
        fig = self.graph_fig
        ax.clear()
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 1)
        ax.axis("off")

        ax.add_patch(
            __import__("matplotlib").patches.Rectangle((0, 0.2), 100, 0.6, fill=False, linewidth=2.0, edgecolor=border_color)
        )

        x = 0.0
        if seg_contrib > 0:
            ax.add_patch(__import__("matplotlib").patches.Rectangle((x, 0.2), seg_contrib, 0.6, color=col_contrib))
            x += seg_contrib
        if seg_completed_loss > 0:
            ax.add_patch(__import__("matplotlib").patches.Rectangle((x, 0.2), seg_completed_loss, 0.6, color=col_completed_loss))
            x += seg_completed_loss
        if seg_planned_remaining > 0:
            ax.add_patch(__import__("matplotlib").patches.Rectangle((x, 0.2), seg_planned_remaining, 0.6, color=col_planned_remaining))
            x += seg_planned_remaining

        def label_if(space, center, text):
            if space >= 6:
                ax.text(center, 0.92, text, ha="center", va="bottom", fontsize=9)

        c1 = seg_contrib / 2.0
        c2 = seg_contrib + seg_completed_loss / 2.0
        c3 = seg_contrib + seg_completed_loss + seg_planned_remaining / 2.0

        label_if(seg_contrib, c1, "Contribution so far")
        label_if(seg_completed_loss, c2, "Completed weight")
        label_if(seg_planned_remaining, c3, "Planned Weight")

        def value_if(space, x0, text):
            if space >= 10:
                ax.text(x0 + space - 1.5, 0.24, text, ha="right", va="bottom", fontsize=8, color="#111")

        value_if(seg_contrib, 0.0, f"{contribution:.1f}%")
        value_if(seg_completed_loss, seg_contrib, f"{max(0.0, completed - contribution):.1f}%")
        value_if(seg_planned_remaining, seg_contrib + seg_completed_loss, f"{max(0.0, planned - completed):.1f}%")

        fig.tight_layout()
        self.graph_canvas.draw()

                         
    # Handles window closure, ensuring data is saved
    def on_close(self):
                                                                    
                                  
        if self.current_filename:
            self.save_file(silent=True)
        self.root.destroy()

                           
    # Creates a new semester file
    def new_file(self):
                                                     
        if self.current_filename:
            self.save_file(silent=True)
        
        self.gb.subjects.clear()
        self.current_filename = None
        self.refresh_subject_list()
                                                                              
        base = "Untitled Semester"
        name = base
        count = 1
        while os.path.exists(os.path.join(self.saves_path, f"{name}.json")):
            name = f"{base} ({count})"
            count += 1
        
        path = os.path.join(self.saves_path, f"{name}.json")
        self.current_filename = path
        
                                                     
        self.save_file(silent=True)
        self.file_var.set(name)
        self.refresh_file_list()

                        
    # Saves the current gradebook to JSON
    def save_file(self, silent=False) -> bool:
                                                   
                                  
                                                                                   
                         
                                                               
        if self.current_filename:
            path = self.current_filename
        else:
                                                 
                                    
                                                               
            self.toggle_rename_mode()
            messagebox.showinfo("Save As", "Please enter a name for this semester in the top bar and click the checkmark.")
            return False
        if not path:
            return False
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.gb.as_json())
            if not silent:
                                          
                self.refresh_file_list()
                if self.current_filename:
                    self.file_var.set(os.path.basename(self.current_filename).replace(".json", ""))
                                                                                       
                                                   
                pass 
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}")
            return False

    # Updates the file selection dropdown
    def refresh_file_list(self):
        json_files = glob.glob(os.path.join(self.saves_path, "*.json"))
                     
        names = [os.path.basename(f).replace(".json", "") for f in json_files]
        names.sort(key=str.lower)
        self.file_combo["values"] = names

    # Loads a file when selected from dropdown
    def on_file_selected(self, event):
        name = self.file_var.get()
        if not name: return
                   
        path = os.path.join(self.saves_path, f"{name}.json")
        if os.path.exists(path):
                                                   
                                                       
                                                                  
            self.load_custom_file(path)
                                               
            self.root.focus_set()
            if hasattr(self, 'file_combo'):
                self.file_combo.selection_clear()

    # Toggles the file renaming input field
    def toggle_rename_mode(self):
        if not self.rename_mode:
                                      
            self.rename_mode = True
            
                                                             
            current = self.file_var.get()
            if current == "New Semester":
                self.rename_var.set("")
            else:
                self.rename_var.set(current)
                
            self.file_combo.pack_forget()
            self.file_entry.pack(side="left", fill="x", expand=True)
            self.file_entry.focus_set()
                                                  
            self.file_entry.select_range(0, tk.END)
            
                                        
            self.edit_file_btn.configure(text="Save", command=self.confirm_rename)
            if USE_TTKB:
                self.edit_file_btn.configure(bootstyle=SUCCESS)
        else:
                           
            self.rename_mode = False
            self.file_entry.pack_forget()
            self.file_combo.pack(side="left", fill="x", expand=True)
            
                           
            self.edit_file_btn.configure(text="Edit", command=self.toggle_rename_mode)
            if USE_TTKB:
                self.edit_file_btn.configure(bootstyle=SECONDARY)

    # Confirms and applies file rename
    def confirm_rename(self):
        new_name = self.rename_var.get().strip()
        if not new_name:
                                             
                                                       
            self.toggle_rename_mode()
            return

        new_path = os.path.join(self.saves_path, f"{new_name}.json")
        
                         
        if os.path.exists(new_path) and (self.current_filename is None or new_path != self.current_filename):
            if not messagebox.askyesno("Overwrite", f"File '{new_name}' already exists. Overwrite?"):
                return

                                             
        if self.current_filename and os.path.exists(self.current_filename):
            try:
                os.rename(self.current_filename, new_path)
                self.current_filename = new_path
                self.file_var.set(new_name)
                self.refresh_file_list()
                
                           
                                                                   
                self.rename_mode = True 
                self.toggle_rename_mode()
                                                 
                self.root.focus_set()
                return
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename:\n{e}")
                return
        
                                                                      
        self.current_filename = new_path
                                                
        self.save_file(silent=True)
        self.file_var.set(new_name)
        self.refresh_file_list()
        
                   
        self.rename_mode = True 
        self.toggle_rename_mode()
                                         
        self.root.focus_set()

    # Deletes the current file
    def delete_current_file(self):
        if not self.current_filename or not os.path.exists(self.current_filename):
            return

        if not self.file_delete_confirm_pending:
                         
            self.file_delete_confirm_pending = True
            self.del_file_btn.configure(text="Confirm")
            self.file_delete_timer = self.root.after(2000, self.reset_file_delete_btn)
        else:
                          
            target_to_delete = self.current_filename
            self.reset_file_delete_btn()
            
            try:
                                                             
                json_files = glob.glob(os.path.join(self.saves_path, "*.json"))
                target_abs = os.path.abspath(target_to_delete)
                candidates = [f for f in json_files if os.path.abspath(f) != target_abs]
                
                                           
                candidates.sort(key=os.path.getmtime, reverse=True)
                
                if candidates:
                                                     
                    self.load_custom_file(candidates[0])
                else:
                                            
                                                                                    
                    self.current_filename = None 
                    self.new_file()                              
                
                                                   
                if os.path.exists(target_to_delete):
                    os.remove(target_to_delete)
                
                self.refresh_file_list()
                
                                                                       
                if self.current_filename:
                    name = os.path.basename(self.current_filename).replace(".json", "")
                    self.file_var.set(name)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{e}")
    
    # Resets the file delete button state
    def reset_file_delete_btn(self):
        self.file_delete_confirm_pending = False
        if self.file_delete_timer:
            self.root.after_cancel(self.file_delete_timer)
            self.file_delete_timer = None
        self.del_file_btn.configure(text="Delete")

                          
    # Opens file dialog to load a file
    def load_file(self):
                                             
        path = filedialog.askopenfilename(
            initialdir=self.saves_path,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Grade Book"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.gb.load_json(f.read())
            self.current_filename = path
            self.refresh_subject_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load:\n{e}")


                               
# Dialog for adding or editing an assessment
class AssessmentDialog:
    # Initializes the assessment dialog
    def __init__(self, master, title="Assessment", initial: Optional[Assessment] = None):
        self.result: Optional[Assessment] = None
        self.top = tk.Toplevel(master)
        self.top.title(title)
        self.top.transient(master)
        self.top.grab_set()
        self.top.resizable(False, False)

        frm = ttk.Frame(self.top, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.name_var = tk.StringVar(value=initial.name if initial else "")
        name_entry = ttk.Entry(frm, textvariable=self.name_var, width=32)
        name_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(frm, text="Type").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.kind_var = tk.StringVar(value=initial.kind if initial else "Assessment")
        kind_combo = ttk.Combobox(frm, textvariable=self.kind_var,
                                  values=["Assignment", "Exam", "Quiz", "Project", "Assessment"],
                                  state="readonly", width=29)
        kind_combo.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(frm, text="Weight (%)").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.weight_var = tk.StringVar(value=f"{initial.weight:.2f}" if initial else "")
        weight_entry = ttk.Entry(frm, textvariable=self.weight_var)
        weight_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=4)

        ttk.Label(frm, text="Mark (%)").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        self.mark_var = tk.StringVar(value=("" if (initial is None or initial.mark is None) else f"{initial.mark:.2f}"))
        mark_entry = ttk.Entry(frm, textvariable=self.mark_var)
        mark_entry.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(frm, text="(You can enter 75 or a fraction like 14/20)").grid(row=4, column=1, sticky="w", padx=4, pady=(0,8))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=6)
        ok_cmd = self.ok
        cancel_cmd = self.top.destroy

        if USE_TTKB:
            ok_btn = tb.Button(btns, text="OK", bootstyle=SUCCESS, command=ok_cmd)
            cancel_btn = tb.Button(btns, text="Cancel", bootstyle=SECONDARY, command=cancel_cmd)
        else:
            ok_btn = ttk.Button(btns, text="OK", command=ok_cmd)
            cancel_btn = ttk.Button(btns, text="Cancel", command=cancel_cmd)

        ok_btn.pack(side="left", padx=4)
        cancel_btn.pack(side="left", padx=4)

        self.top.bind("<Return>", lambda e: ok_cmd())
        self.top.bind("<Escape>", lambda e: cancel_cmd())

        name_entry.focus_set()
        
                                                
        try:
            self.top.update_idletasks()
            w = self.top.winfo_width()
            h = self.top.winfo_height()
            
                                                                                 
                                                   
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            
            x = mx + (mw // 2) - (w // 2)
            y = my + (mh // 2) - (h // 2)
            
            self.top.geometry(f"+{x}+{y}")
        except Exception:
                                           
            pass

    # Validates input and saves assessment
    def ok(self):
        name = self.name_var.get().strip()
        kind = self.kind_var.get().strip() or "Assessment"
        try:
            weight = float(self.weight_var.get().strip())
        except Exception:
            messagebox.showerror("Invalid Input", "Weight must be a number.")
            return
        if weight < 0 or weight > 1000:
            messagebox.showerror("Invalid Input", "Weight must be between 0 and 1000%.")
            return

        mark_str = self.mark_var.get().strip()
        mark = None
        if mark_str != "":
            try:
                if "/" in mark_str:
                    num, denom = mark_str.split("/")
                    num = float(num.strip())
                    denom = float(denom.strip())
                    if denom <= 0:
                        raise ValueError("Denominator must be > 0")
                    mark = (num / denom) * 100.0
                else:
                    mark = float(mark_str)
                if mark < 0 or mark > 100:
                    raise ValueError("Mark must be between 0 and 100 after conversion.")
            except Exception as e:
                messagebox.showerror("Invalid Input", f"Mark must be a number (e.g., 75) "
                                                     f"or fraction (e.g., 14/20).\nError: {e}")
                return

        if not name:
            messagebox.showerror("Invalid Input", "Please enter a name for the assessment.")
            return

        self.result = Assessment(name=name, kind=kind, weight=weight, mark=mark)
        self.top.destroy()

                               
# Dialog for selecting a save file
class FileSelectionDialog:
    # Initializes the file selection dialog
    def __init__(self, master, filenames: List[str]):
        self.selected_filename: Optional[str] = None
        self.top = tk.Toplevel(master)
        self.top.title("Select Save File")
                                                                                           
        self.top.grab_set()
        self.top.resizable(False, False)
        
                                   
        self.top.geometry("400x300")

        ttk.Label(self.top, text="Multiple save files found. Please select one:", font=("", 10)).pack(pady=10)

                           
        frame_list = ttk.Frame(self.top)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_list)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(frame_list, yscrollcommand=scrollbar.set, font=("", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        for fname in filenames:
            self.listbox.insert(tk.END, fname)
        
                                 
        if filenames:
            self.listbox.select_set(0)

        self.listbox.bind("<Double-Button-1>", lambda e: self.ok())

                 
        btns = ttk.Frame(self.top)
        btns.pack(pady=10)

        if USE_TTKB:
            ok_btn = tb.Button(btns, text="Open", bootstyle=SUCCESS, command=self.ok)
            cancel_btn = tb.Button(btns, text="New Semester", bootstyle=SECONDARY, command=self.top.destroy)
        else:
            ok_btn = ttk.Button(btns, text="Open", command=self.ok)
            cancel_btn = ttk.Button(btns, text="New Semester", command=self.top.destroy)

        ok_btn.pack(side="left", padx=5)
        cancel_btn.pack(side="left", padx=5)

    # Confirm file selection
    def ok(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        self.selected_filename = self.listbox.get(sel[0])
        self.top.destroy()
