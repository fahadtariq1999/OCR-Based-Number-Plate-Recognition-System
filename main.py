import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import cv2
import os
import easyocr
# from ultralytics import YOLO # Keep this if you have it set up
from datetime import datetime
import shutil # For cleaning up cropped images

from ultralytics import YOLO
# --- Configuration ---
MODEL_PATH = 'yolov8_model/best.pt'  
CROPPED_DIR = 'cropped_objects_toll_system'
VEHICLES_DB_FILE = 'vehicles_db.csv'  # Columns: plate, owner, type, balance
TOLL_LOG_FILE = 'toll_log.csv'    # Columns: timestamp, plate, amount, status, image_ref
DEFAULT_TOLL_AMOUNT = 10.00

# --- Initialize OCR and Object Detection ---
# Ensure 'best.pt' is in the same directory or provide the full path
# For demonstration, if YOLO causes issues without GPU or setup, we can mock it.
try:
    model = YOLO(MODEL_PATH)
    yolo_available = True
    print("YOLO model loaded successfully.")
except Exception as e:
    print(f"Error loading YOLO model: {e}. YOLO features will be disabled.")
    yolo_available = False
    model = None # Placeholder

try:
    reader = easyocr.Reader(['en'])
    ocr_available = True
    print("EasyOCR reader initialized.")
except Exception as e:
    print(f"Error initializing EasyOCR: {e}. OCR features will be disabled.")
    ocr_available = False
    reader = None # Placeholder

class TollManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Toll Management System")
        self.root.geometry("900x700")

        # Initialize data storage if files don't exist
        self._init_csv_files()

        self.vehicles_data = self._load_data(VEHICLES_DB_FILE)
        self.toll_log_data = self._load_data(TOLL_LOG_FILE)

        # Styling
        style = ttk.Style()
        style.theme_use('clam') # or 'alt', 'default', 'classic'
        style.configure("TNotebook.Tab", font=('Helvetica', 12, 'bold'))
        style.configure("TButton", font=('Helvetica', 10), padding=5)
        style.configure("TLabel", font=('Helvetica', 10))
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

        # --- Main UI Structure ---
        self.notebook = ttk.Notebook(root)

        # Tab 1: Process Toll
        self.tab_process_toll = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_process_toll, text='Process Toll Booth Image')
        self._create_process_toll_tab()

        # Tab 2: Vehicle Management
        self.tab_vehicle_management = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_vehicle_management, text='Vehicle Management')
        self._create_vehicle_management_tab()

        # Tab 3: Toll Log
        self.tab_toll_log = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_toll_log, text='View Toll Log')
        self._create_toll_log_tab()

        self.notebook.pack(expand=True, fill='both')

        # Periodically clean up old cropped images
        self._cleanup_cropped_dir()


    def _init_csv_files(self):
        if not os.path.exists(VEHICLES_DB_FILE):
            with open(VEHICLES_DB_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['plate', 'owner', 'type', 'balance'])
                # Add a sample vehicle for testing
                writer.writerow(['MH20EE7777', 'Test User', 'Car', '50.00'])
        if not os.path.exists(TOLL_LOG_FILE):
            with open(TOLL_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'plate', 'amount', 'status', 'image_ref'])

    def _load_data(self, filename):
        data = []
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except FileNotFoundError:
            messagebox.showerror("Error", f"{filename} not found. Please ensure it exists.")
        return data

    def _save_data(self, filename, data, fieldnames):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save data to {filename}: {e}")

    def _cleanup_cropped_dir(self):
        if os.path.exists(CROPPED_DIR):
            try:
                shutil.rmtree(CROPPED_DIR) # Removes the directory and all its contents
                print(f"Cleaned up {CROPPED_DIR}")
            except Exception as e:
                print(f"Error cleaning up {CROPPED_DIR}: {e}")
        os.makedirs(CROPPED_DIR, exist_ok=True)


    # --- TAB 1: Process Toll ---
    def _create_process_toll_tab(self):
        frame = self.tab_process_toll

        # Top frame for image selection and processing
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=tk.X, pady=10)

        ttk.Button(top_frame, text="Select Image & Process", command=self.select_and_process_image).pack(side=tk.LEFT, padx=5)
        self.image_path_label = ttk.Label(top_frame, text="No image selected")
        self.image_path_label.pack(side=tk.LEFT, padx=5)

        # Frame for displaying detected plates and actions
        results_frame = ttk.LabelFrame(frame, text="Detected Plates & Toll Processing", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        cols = ('plate_number', 'status', 'vehicle_owner', 'current_balance', 'action')
        self.detected_plates_tree = ttk.Treeview(results_frame, columns=cols, show='headings', height=10)
        for col in cols:
            self.detected_plates_tree.heading(col, text=col.replace('_', ' ').title())
            self.detected_plates_tree.column(col, width=120, anchor=tk.W)
        self.detected_plates_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.detected_plates_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.detected_plates_tree.configure(yscrollcommand=vsb.set)

        # Placeholder for image display (optional, can be complex)
        # self.image_display_label = ttk.Label(results_frame, text="Image will appear here")
        # self.image_display_label.pack(pady=10)

        self.status_bar = ttk.Label(frame, text="Status: Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def select_and_process_image(self):
        if not yolo_available or not ocr_available:
            messagebox.showerror("Dependency Error", "YOLO model or EasyOCR is not available. Cannot process image.")
            return

        filepath = filedialog.askopenfilename(
            title="Select Image",
            filetypes=(("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*"))
        )
        if not filepath:
            return

        self.image_path_label.config(text=os.path.basename(filepath))
        self.status_bar.config(text="Status: Processing image...")
        self.root.update_idletasks() # Force GUI update

        try:
            image = cv2.imread(filepath)
            if image is None:
                messagebox.showerror("Error", "Could not read image file.")
                self.status_bar.config(text="Status: Error reading image.")
                return

            # Clear previous results
            for item in self.detected_plates_tree.get_children():
                self.detected_plates_tree.delete(item)
            self._cleanup_cropped_dir() # Clean before new processing

            results = model(image) # YOLO detection
            # The structure of 'results' might vary slightly based on ultralytics version
            # Assuming results[0].boxes gives access to bounding boxes

            detected_texts = []
            if results and results[0].boxes is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy() # Get boxes in xyxy format
                confidences = results[0].boxes.conf.cpu().numpy() # Get confidences
                class_ids = results[0].boxes.cls.cpu().numpy() # Get class IDs

                for i, (box, conf, cls_id) in enumerate(zip(boxes, confidences, class_ids)):
                    # Assuming class 0 is 'license_plate' or similar in your 'best.pt'
                    # You might need to adjust this if your model has multiple classes
                    # For now, let's assume all detected objects are plates if you only trained for plates
                    x_min, y_min, x_max, y_max = map(int, box)
                    cropped_object = image[y_min:y_max, x_min:x_max]
                    
                    # Sanity check for cropped image size
                    if cropped_object.size == 0:
                        print(f"Warning: Cropped object {i} is empty. Skipping.")
                        continue

                    cropped_image_path = os.path.join(CROPPED_DIR, f"cropped_{os.path.basename(filepath)}_{i}.jpg")
                    cv2.imwrite(cropped_image_path, cropped_object)
                    
                    ocr_result = reader.readtext(cropped_image_path, detail=0, paragraph=False) # Simpler output
                    
                    # Combine OCR results, filter for alphanumeric, and make uppercase
                    # Basic filtering for common OCR errors could be added here
                    plate_text = "".join(filter(str.isalnum, "".join(ocr_result))).upper()
                    
                    if plate_text: # Only process if OCR found something
                        detected_texts.append({'raw_plate': plate_text, 'image_ref': cropped_image_path})
            else:
                self.status_bar.config(text="Status: No objects detected by YOLO.")
                return # No detections

            if not detected_texts:
                self.status_bar.config(text="Status: No license plates read by OCR.")
                messagebox.showinfo("OCR Result", "No license plates could be read from the detected objects.")
                return

            # Process detected plates for toll
            for det_plate_info in detected_texts:
                plate = det_plate_info['raw_plate']
                image_ref = det_plate_info['image_ref']
                self._process_toll_for_plate(plate, image_ref)

            self.status_bar.config(text=f"Status: Processing complete. {len(detected_texts)} potential plates found.")
            self._refresh_toll_log_tab() # Update log tab as well

        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred: {e}")
            self.status_bar.config(text=f"Status: Error - {e}")
            import traceback
            traceback.print_exc()


    def _process_toll_for_plate(self, plate_number, image_ref):
        vehicle = self._find_vehicle(plate_number)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "Unknown"
        owner = "N/A"
        balance_val = "N/A"

        if vehicle:
            owner = vehicle['owner']
            try:
                current_balance = float(vehicle['balance'])
                balance_val = f"{current_balance:.2f}"
                if current_balance >= DEFAULT_TOLL_AMOUNT:
                    vehicle['balance'] = str(current_balance - DEFAULT_TOLL_AMOUNT)
                    status = "Auto-Paid"
                    self._log_toll_transaction(timestamp, plate_number, DEFAULT_TOLL_AMOUNT, status, image_ref)
                    self._save_data(VEHICLES_DB_FILE, self.vehicles_data, ['plate', 'owner', 'type', 'balance'])
                    self._refresh_vehicle_management_tab() # Update vehicle data display
                    balance_val = f"{float(vehicle['balance']):.2f} (Paid)"
                else:
                    status = "Unpaid - Low Balance"
                    self._log_toll_transaction(timestamp, plate_number, DEFAULT_TOLL_AMOUNT, status, image_ref)
            except ValueError:
                status = "Error - Invalid Balance"
                balance_val = vehicle['balance'] + " (Error)"
                self._log_toll_transaction(timestamp, plate_number, DEFAULT_TOLL_AMOUNT, status, image_ref)
        else:
            status = "Unpaid - Unregistered"
            self._log_toll_transaction(timestamp, plate_number, DEFAULT_TOLL_AMOUNT, status, image_ref)

        # Add to the detected plates treeview
        self.detected_plates_tree.insert('', tk.END, values=(plate_number, status, owner, balance_val, "Details"))
        # Could add a button or double-click event here to show image_ref or more details

    def _find_vehicle(self, plate_number):
        for v in self.vehicles_data:
            if v['plate'] == plate_number:
                return v
        return None

    def _log_toll_transaction(self, timestamp, plate, amount, status, image_ref):
        new_log_entry = {
            'timestamp': timestamp,
            'plate': plate,
            'amount': f"{amount:.2f}",
            'status': status,
            'image_ref': os.path.basename(image_ref) # Store only filename
        }
        self.toll_log_data.append(new_log_entry)
        self._save_data(TOLL_LOG_FILE, self.toll_log_data, ['timestamp', 'plate', 'amount', 'status', 'image_ref'])


    # --- TAB 2: Vehicle Management ---
    def _create_vehicle_management_tab(self):
        frame = self.tab_vehicle_management

        # Display vehicles
        list_frame = ttk.LabelFrame(frame, text="Registered Vehicles", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ('plate', 'owner', 'type', 'balance')
        self.vehicles_tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        for col in cols:
            self.vehicles_tree.heading(col, text=col.title())
            self.vehicles_tree.column(col, width=150, anchor=tk.W)
        self.vehicles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vsb_vehicles = ttk.Scrollbar(list_frame, orient="vertical", command=self.vehicles_tree.yview)
        vsb_vehicles.pack(side=tk.RIGHT, fill=tk.Y)
        self.vehicles_tree.configure(yscrollcommand=vsb_vehicles.set)
        
        self._refresh_vehicle_management_tab()

        # Add/Edit vehicle form
        form_frame = ttk.LabelFrame(frame, text="Add/Edit Vehicle", padding=10)
        form_frame.pack(fill=tk.X, pady=10)

        ttk.Label(form_frame, text="Plate Number:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.plate_entry = ttk.Entry(form_frame, width=30)
        self.plate_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Owner Name:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.owner_entry = ttk.Entry(form_frame, width=30)
        self.owner_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Vehicle Type:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.type_entry = ttk.Entry(form_frame, width=30) # Could be a Combobox
        self.type_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Initial Balance:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.balance_entry = ttk.Entry(form_frame, width=30)
        self.balance_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Button(form_frame, text="Add Vehicle", command=self.add_vehicle).grid(row=4, column=0, padx=5, pady=10)
        ttk.Button(form_frame, text="Update Selected", command=self.update_vehicle).grid(row=4, column=1, padx=5, pady=10, sticky=tk.W)
        ttk.Button(form_frame, text="Delete Selected", command=self.delete_vehicle).grid(row=4, column=2, padx=5, pady=10, sticky=tk.W)
        ttk.Button(form_frame, text="Load Selected", command=self.load_selected_vehicle_to_form).grid(row=0, column=2, rowspan=2, padx=5, pady=5, sticky=tk.EW)


    def _refresh_vehicle_management_tab(self):
        # Clear existing items
        for item in self.vehicles_tree.get_children():
            self.vehicles_tree.delete(item)
        # Add new items
        for vehicle in self.vehicles_data:
            try:
                balance_val = f"{float(vehicle.get('balance', 0.0)):.2f}"
            except ValueError:
                balance_val = vehicle.get('balance', 'N/A') # Show raw if not float
            self.vehicles_tree.insert('', tk.END, values=(
                vehicle.get('plate', ''),
                vehicle.get('owner', ''),
                vehicle.get('type', ''),
                balance_val
            ))
    
    def load_selected_vehicle_to_form(self):
        selected_item = self.vehicles_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a vehicle from the list to load.")
            return
        
        item_values = self.vehicles_tree.item(selected_item, 'values')
        self.plate_entry.delete(0, tk.END)
        self.plate_entry.insert(0, item_values[0])
        self.owner_entry.delete(0, tk.END)
        self.owner_entry.insert(0, item_values[1])
        self.type_entry.delete(0, tk.END)
        self.type_entry.insert(0, item_values[2])
        self.balance_entry.delete(0, tk.END)
        self.balance_entry.insert(0, item_values[3])


    def add_vehicle(self):
        plate = self.plate_entry.get().strip().upper()
        owner = self.owner_entry.get().strip()
        v_type = self.type_entry.get().strip()
        balance_str = self.balance_entry.get().strip()

        if not all([plate, owner, v_type, balance_str]):
            messagebox.showerror("Input Error", "All fields are required.")
            return
        try:
            balance = float(balance_str)
            if balance < 0:
                messagebox.showerror("Input Error", "Balance cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Balance must be a valid number.")
            return

        if self._find_vehicle(plate):
            messagebox.showerror("Error", f"Vehicle with plate {plate} already exists.")
            return

        new_vehicle = {'plate': plate, 'owner': owner, 'type': v_type, 'balance': f"{balance:.2f}"}
        self.vehicles_data.append(new_vehicle)
        self._save_data(VEHICLES_DB_FILE, self.vehicles_data, ['plate', 'owner', 'type', 'balance'])
        self._refresh_vehicle_management_tab()
        messagebox.showinfo("Success", f"Vehicle {plate} added.")
        # Clear entries
        self.plate_entry.delete(0, tk.END)
        self.owner_entry.delete(0, tk.END)
        self.type_entry.delete(0, tk.END)
        self.balance_entry.delete(0, tk.END)

    def update_vehicle(self):
        selected_item = self.vehicles_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a vehicle from the list to update.")
            return

        plate = self.plate_entry.get().strip().upper()
        owner = self.owner_entry.get().strip()
        v_type = self.type_entry.get().strip()
        balance_str = self.balance_entry.get().strip()

        if not all([plate, owner, v_type, balance_str]):
            messagebox.showerror("Input Error", "All fields are required for update.")
            return
        try:
            balance = float(balance_str)
            if balance < 0:
                messagebox.showerror("Input Error", "Balance cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Balance must be a valid number for update.")
            return

        # Find the vehicle in self.vehicles_data using the original plate from Treeview if plate is being changed
        original_plate = self.vehicles_tree.item(selected_item, 'values')[0]
        vehicle_to_update = self._find_vehicle(original_plate)

        if not vehicle_to_update:
             messagebox.showerror("Error", f"Vehicle {original_plate} not found in data. This shouldn't happen.")
             return

        # If plate number is changed, check if the new plate number already exists (and is not the current one)
        if plate != original_plate and self._find_vehicle(plate):
            messagebox.showerror("Error", f"Another vehicle with plate {plate} already exists.")
            return

        vehicle_to_update['plate'] = plate
        vehicle_to_update['owner'] = owner
        vehicle_to_update['type'] = v_type
        vehicle_to_update['balance'] = f"{balance:.2f}"

        self._save_data(VEHICLES_DB_FILE, self.vehicles_data, ['plate', 'owner', 'type', 'balance'])
        self._refresh_vehicle_management_tab()
        messagebox.showinfo("Success", f"Vehicle {plate} updated.")
    
    def delete_vehicle(self):
        selected_item = self.vehicles_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a vehicle from the list to delete.")
            return

        plate_to_delete = self.vehicles_tree.item(selected_item, 'values')[0]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete vehicle {plate_to_delete}?"):
            self.vehicles_data = [v for v in self.vehicles_data if v['plate'] != plate_to_delete]
            self._save_data(VEHICLES_DB_FILE, self.vehicles_data, ['plate', 'owner', 'type', 'balance'])
            self._refresh_vehicle_management_tab()
            messagebox.showinfo("Success", f"Vehicle {plate_to_delete} deleted.")


    # --- TAB 3: Toll Log ---
    def _create_toll_log_tab(self):
        frame = self.tab_toll_log
        
        log_frame = ttk.LabelFrame(frame, text="Toll Transaction Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ('timestamp', 'plate', 'amount', 'status', 'image_ref')
        self.toll_log_tree = ttk.Treeview(log_frame, columns=cols, show='headings', height=15)
        for col in cols:
            self.toll_log_tree.heading(col, text=col.replace('_',' ').title())
            self.toll_log_tree.column(col, width=120, anchor=tk.W)
        self.toll_log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb_log = ttk.Scrollbar(log_frame, orient="vertical", command=self.toll_log_tree.yview)
        vsb_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.toll_log_tree.configure(yscrollcommand=vsb_log.set)
        
        self._refresh_toll_log_tab()

        ttk.Button(frame, text="Refresh Log", command=self._refresh_toll_log_tab).pack(pady=10)
        # Future: Add filtering options here

    def _refresh_toll_log_tab(self):
        # Clear existing items
        for item in self.toll_log_tree.get_children():
            self.toll_log_tree.delete(item)
        # Reload data from file in case it was modified externally or by other parts of app
        self.toll_log_data = self._load_data(TOLL_LOG_FILE)
        # Add new items
        for log_entry in self.toll_log_data:
            self.toll_log_tree.insert('', tk.END, values=(
                log_entry.get('timestamp', ''),
                log_entry.get('plate', ''),
                log_entry.get('amount', ''),
                log_entry.get('status', ''),
                log_entry.get('image_ref', '')
            ))

if __name__ == "__main__":
    if not yolo_available and not ocr_available:
        print("CRITICAL ERROR: Neither YOLO nor EasyOCR could be initialized.")
        print("The application might not function correctly or at all.")
        # Optionally, exit or show a critical error GUI message here
        # For now, we'll let it run to show the GUI structure.

    root = tk.Tk()
    app = TollManagementApp(root)
    root.mainloop()