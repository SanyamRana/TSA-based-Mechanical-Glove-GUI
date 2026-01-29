import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import serial
import threading
import time
import numpy as np
import csv
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ServoConfig:
    """Configuration parameters for the servo system"""
    SERIAL_PORT: str = 'COM9'
    BAUDRATE: int = 9600
    TIMEOUT: float = 1.0
    WRITE_TIMEOUT: float = 2.0
    MAX_DATA_POINTS: int = 1000
    UPDATE_INTERVAL_MS: int = 100
    PLOT_UPDATE_INTERVAL_MS: int = 50

class SerialManager:
    """Manages serial communication with error handling and reconnection"""
    
    def __init__(self, config: ServoConfig):
        self.config = config
        self.ser: Optional[serial.Serial] = None
        self.is_connected = False
        self._connect()
    
    def _connect(self) -> bool:
        """Attempt to establish serial connection"""
        try:
            self.ser = serial.Serial(
                self.config.SERIAL_PORT, 
                self.config.BAUDRATE, 
                timeout=self.config.TIMEOUT,
                write_timeout=self.config.WRITE_TIMEOUT
            )
            self.is_connected = True
            logger.info(f"Connected to {self.config.SERIAL_PORT}")
            return True
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Serial connection failed: {e}")
            return False
    
    def write(self, data: str) -> bool:
        """Write data to serial port with error handling"""
        if not self.is_connected or not self.ser:
            return False
        
        try:
            self.ser.write(data.encode())
            return True
        except Exception as e:
            logger.error(f"Serial write failed: {e}")
            self.is_connected = False
            return False
    
    def readline(self) -> Optional[str]:
        """Read line from serial port with error handling"""
        if not self.is_connected or not self.ser:
            return None
        
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            return line if line else None
        except Exception as e:
            logger.error(f"Serial read failed: {e}")
            self.is_connected = False
            return None
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()
            self.is_connected = False

class DataManager:
    """Manages servo data with efficient storage and statistics"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.angle_data = deque(maxlen=max_size)
        self.feedback_data = deque(maxlen=max_size)
        self.error_data = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
        self._stats_cache = {}
        self._stats_dirty = True
    
    def add_data_point(self, commanded: float, feedback: float, timestamp: float = None):
        """Add new data point and invalidate stats cache"""
        if timestamp is None:
            timestamp = time.time()
        
        error = commanded - feedback
        
        self.angle_data.append(commanded)
        self.feedback_data.append(feedback)
        self.error_data.append(error)
        self.timestamps.append(timestamp)
        self._stats_dirty = True
    
    def get_statistics(self) -> dict:
        """Get cached statistics, recalculate if dirty"""
        if self._stats_dirty and self.error_data:
            errors = np.array(self.error_data)
            self._stats_cache = {
                'avg_error': np.mean(errors),
                'max_error': np.max(np.abs(errors)),
                'std_error': np.std(errors),
                'count': len(errors)
            }
            self._stats_dirty = False
        
        return self._stats_cache
    
    def clear(self):
        """Clear all data"""
        self.angle_data.clear()
        self.feedback_data.clear()
        self.error_data.clear()
        self.timestamps.clear()
        self._stats_cache.clear()
        self._stats_dirty = True
    
    def export_csv(self, filename: str) -> bool:
        """Export data to CSV file"""
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Sample", "Timestamp", "Commanded_Angle", "Feedback_Angle", "Error"])
                for i, (ts, cmd, fb, err) in enumerate(zip(
                    self.timestamps, self.angle_data, self.feedback_data, self.error_data
                )):
                    writer.writerow([i+1, ts, cmd, fb, err])
            return True
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False

class PlotManager:
    """Manages matplotlib plots with optimized updates"""
    
    def __init__(self, master):
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        
        self._setup_plots()
        self._plot_dirty = False
    
    def _setup_plots(self):
        """Initialize plot settings"""
        # Top plot: Commanded vs Feedback
        self.ax1.set_title("Commanded vs Feedback Angle", fontsize=12)
        self.ax1.set_xlabel("Sample")
        self.ax1.set_ylabel("Angle (°)")
        self.line_cmd, = self.ax1.plot([], [], 'b-', label='Commanded', linewidth=1)
        self.line_fb, = self.ax1.plot([], [], 'r-', label='Feedback', linewidth=1)
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)
        
        # Bottom plot: Error
        self.ax2.set_title("Error (Commanded - Feedback)", fontsize=12)
        self.ax2.set_xlabel("Sample")
        self.ax2.set_ylabel("Error (°)")
        self.line_err, = self.ax2.plot([], [], 'r-', label='Error', linewidth=1)
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    def update_plots(self, data_manager: DataManager):
        """Update plots with new data"""
        if not data_manager.angle_data:
            return
        
        x = np.arange(len(data_manager.angle_data))
        
        # Update line data
        self.line_cmd.set_data(x, data_manager.angle_data)
        self.line_fb.set_data(x, data_manager.feedback_data)
        self.line_err.set_data(x, data_manager.error_data)
        
        # Auto-scale axes
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        
        # Redraw canvas
        self.canvas.draw_idle()
    
    def clear_plots(self):
        """Clear all plot data"""
        self.line_cmd.set_data([], [])
        self.line_fb.set_data([], [])
        self.line_err.set_data([], [])
        
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        
        self.canvas.draw_idle()

class ServoControlGUI:
    """Main GUI application class"""
    
    def __init__(self):
        self.config = ServoConfig()
        self.serial_manager = SerialManager(self.config)
        self.data_manager = DataManager(self.config.MAX_DATA_POINTS)
        
        # State variables
        self.is_running = False
        self.is_clockwise = True
        self.last_commanded_angle: Optional[float] = None
        
        # Setup GUI
        self._setup_gui()
        
        # Start background threads
        self._start_threads()
    
    def _setup_gui(self):
        """Initialize the GUI components"""
        self.root = tk.Tk()
        self.root.title("Optimized Servo Motor Control")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create main frames
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Initialize plot manager
        self.plot_manager = PlotManager(plot_frame)
        
        # Setup controls
        self._setup_controls(control_frame)
        
        # Initialize display
        self._update_displays()
    
    def _setup_controls(self, parent):
        """Setup control widgets"""
        # Target angle control
        angle_frame = ttk.LabelFrame(parent, text="Target Control")
        angle_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        self.angle_var = tk.IntVar(value=90)
        self.angle_scale = ttk.Scale(
            angle_frame, from_=0, to=180, 
            variable=self.angle_var, 
            orient=tk.HORIZONTAL,
            command=self._on_angle_change
        )
        self.angle_scale.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(angle_frame, text="Target Angle (°)").pack()
        
        # Speed control
        speed_frame = ttk.LabelFrame(angle_frame, text="Speed")
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.speed_var = tk.IntVar(value=1)
        ttk.Scale(
            speed_frame, from_=1, to=5,
            variable=self.speed_var,
            orient=tk.HORIZONTAL
        ).pack(fill=tk.X)
        ttk.Label(speed_frame, text="1=Fast, 5=Slow").pack()
        
        # Status display
        status_frame = ttk.LabelFrame(parent, text="Status")
        status_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        self._setup_status_display(status_frame)
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self._setup_buttons(button_frame)
        
        # Configure column weights
        parent.columnconfigure(1, weight=1)
    
    def _setup_status_display(self, parent):
        """Setup status display widgets"""
        self.status_vars = {
            'gui_angle': tk.StringVar(value="90°"),
            'servo_angle': tk.StringVar(value="90°"),
            'current_angle': tk.StringVar(value="N/A"),
            'error': tk.StringVar(value="N/A"),
            'avg_error': tk.StringVar(value="N/A"),
            'max_error': tk.StringVar(value="N/A"),
            'direction': tk.StringVar(value="Clockwise"),
            'status': tk.StringVar(value="Stopped"),
            'connection': tk.StringVar(value="Connected" if self.serial_manager.is_connected else "Disconnected")
        }
        
        labels = [
            ("GUI Target:", 'gui_angle'),
            ("Servo Target:", 'servo_angle'),
            ("Current Angle:", 'current_angle'),
            ("Error:", 'error'),
            ("Avg Error:", 'avg_error'),
            ("Max Error:", 'max_error'),
            ("Direction:", 'direction'),
            ("Status:", 'status'),
            ("Connection:", 'connection')
        ]
        
        for i, (label_text, var_key) in enumerate(labels):
            ttk.Label(parent, text=label_text).grid(row=i, column=0, sticky='w', padx=5)
            ttk.Label(parent, textvariable=self.status_vars[var_key]).grid(row=i, column=1, sticky='w', padx=5)
    
    def _setup_buttons(self, parent):
        """Setup control buttons"""
        # Main control buttons
        self.start_btn = ttk.Button(parent, text="START", command=self._start_movement)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(parent, text="STOP", command=self._stop_movement)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Direction buttons
        direction_frame = ttk.Frame(parent)
        direction_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(direction_frame, text="Direction:").pack(side=tk.TOP)
        
        btn_frame = ttk.Frame(direction_frame)
        btn_frame.pack(side=tk.TOP)
        
        self.cw_btn = ttk.Button(btn_frame, text="Clockwise", command=self._set_clockwise)
        self.cw_btn.pack(side=tk.LEFT, padx=2)
        
        self.ccw_btn = ttk.Button(btn_frame, text="Counter-CW", command=self._set_counterclockwise)
        self.ccw_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Utility buttons
        ttk.Button(parent, text="Reset", command=self._reset_system).pack(side=tk.LEFT, padx=5)
        ttk.Button(parent, text="Save Data", command=self._save_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(parent, text="Clear Data", command=self._clear_data).pack(side=tk.LEFT, padx=5)
        
        # Initialize button states
        self._set_clockwise()
    
    def _get_actual_servo_angle(self) -> float:
        """Convert GUI angle to actual servo angle based on direction"""
        gui_angle = self.angle_var.get()
        return gui_angle if self.is_clockwise else 180 - gui_angle
    
    def _on_angle_change(self, value):
        """Handle angle slider change"""
        angle = int(float(value))
        self._update_displays()
        logger.info(f"Target set to: GUI={angle}°, Servo={self._get_actual_servo_angle()}°")
    
    def _set_clockwise(self):
        """Set clockwise direction"""
        self.is_clockwise = True
        self.cw_btn.configure(state='disabled')
        self.ccw_btn.configure(state='normal')
        self._update_displays()
        logger.info("Direction: Clockwise")
    
    def _set_counterclockwise(self):
        """Set counter-clockwise direction"""
        self.is_clockwise = False
        self.ccw_btn.configure(state='disabled')
        self.cw_btn.configure(state='normal')
        self._update_displays()
        logger.info("Direction: Counter-clockwise")
    
    def _start_movement(self):
        """Start servo movement"""
        if not self.serial_manager.is_connected:
            messagebox.showerror("Connection Error", "Serial port not connected!")
            return
        
        self.is_running = True
        self.last_commanded_angle = self._get_actual_servo_angle()
        speed = self.speed_var.get()
        
        if self.serial_manager.write(f"START,{self.last_commanded_angle},{speed}\n"):
            self.start_btn.configure(state='disabled')
            self.stop_btn.configure(state='normal')
            self._update_displays()
            logger.info(f"Started: Servo={self.last_commanded_angle}°, Speed={speed}")
        else:
            self.is_running = False
            messagebox.showerror("Communication Error", "Failed to send start command!")
    
    def _stop_movement(self):
        """Stop servo movement"""
        self.is_running = False
        
        if self.serial_manager.write("STOP\n"):
            logger.info("Movement stopped")
        
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='normal')
        self._update_displays()
    
    def _auto_stop(self):
        """Automatically stop when target is reached"""
        self.is_running = False
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='normal')
        self._update_displays()
        logger.info("Target reached - movement completed")
    
    def _reset_system(self):
        """Reset the entire system (kept as internal method for potential future use)"""
        self.is_running = False
        self.angle_var.set(90)
        self.is_clockwise = True
        
        # Clear data
        self.data_manager.clear()
        self.plot_manager.clear_plots()
        self._update_displays()
        
        # Reset GUI state
        self._set_clockwise()
        self.start_btn.configure(state='normal')
        self.last_commanded_angle=90
        self._update_displays()
        
        # Send reset command
        if self.serial_manager.write("RESET,90\n"):
            logger.info("System reset to 90°")
        
        self._update_displays()
    
    def _save_data(self):
        """Save data to CSV file"""
        if not self.data_manager.angle_data:
            messagebox.showwarning("Save Error", "No data to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Servo Data"
        )
        
        if filename and self.data_manager.export_csv(filename):
            messagebox.showinfo("Save Successful", f"Data saved to {filename}")
        elif filename:
            messagebox.showerror("Save Error", "Failed to save data!")
    
    def _clear_data(self):
        """Clear all collected data"""
        if messagebox.askyesno("Clear Data", "Are you sure you want to clear all data?"):
            self.data_manager.clear()
            self.plot_manager.clear_plots()
            self._update_displays()
            logger.info("Data cleared")
    
    def _update_displays(self):
        """Update all status displays"""
        gui_angle = self.angle_var.get()
        servo_angle = self._get_actual_servo_angle()
        
        self.status_vars['gui_angle'].set(f"{gui_angle}°")
        self.status_vars['servo_angle'].set(f"{servo_angle}°")
        self.status_vars['direction'].set("Clockwise" if self.is_clockwise else "Counter-CW")
        self.status_vars['status'].set("Running" if self.is_running else "Stopped")
        self.status_vars['connection'].set("Connected" if self.serial_manager.is_connected else "Disconnected")
        
        # Update statistics if data available
        stats = self.data_manager.get_statistics()
        if stats:
            self.status_vars['avg_error'].set(f"{stats['avg_error']:.2f}°")
            self.status_vars['max_error'].set(f"{stats['max_error']:.2f}°")
    
    def _start_threads(self):
        """Start background threads"""
        # Data collection thread
        self.data_thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        self.data_thread.start()
        
        # Plot update timer
        self.root.after(self.config.PLOT_UPDATE_INTERVAL_MS, self._update_plots_timer)
        
        # Display update timer
        self.root.after(self.config.UPDATE_INTERVAL_MS, self._update_displays_timer)
    
    def _data_collection_loop(self):
        """Background thread for data collection"""
        while True:
            if self.serial_manager.is_connected:
                line = self.serial_manager.readline()
                
                if line and line.startswith("Angle:") and self.last_commanded_angle is not None:
                    try:
                        feedback_angle = float(line.split(":")[1])
                        self.data_manager.add_data_point(self.last_commanded_angle, feedback_angle)
                        
                        # Update current angle display (thread-safe)
                        self.root.after_idle(lambda: self.status_vars['current_angle'].set(f"{feedback_angle}°"))
                        self.root.after_idle(lambda: self.status_vars['error'].set(f"{self.last_commanded_angle - feedback_angle:.2f}°"))
                        
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse angle data: {line} - {e}")
                
                elif line and line.startswith("TARGET_REACHED"):
                    self.root.after_idle(self._auto_stop)
            
            time.sleep(0.01)  # Small sleep to prevent excessive CPU usage
    
    def _update_plots_timer(self):
        """Timer callback for plot updates"""
        self.plot_manager.update_plots(self.data_manager)
        self.root.after(self.config.PLOT_UPDATE_INTERVAL_MS, self._update_plots_timer)
    
    def _update_displays_timer(self):
        """Timer callback for display updates"""
        self._update_displays()
        self.root.after(self.config.UPDATE_INTERVAL_MS, self._update_displays_timer)
    
    def _on_closing(self):
        """Handle application closing"""
        logger.info("Shutting down application...")
        self.serial_manager.close()
        self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        logger.info("Starting Servo Control GUI...")
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = ServoControlGUI()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Application Error", f"An error occurred: {e}")

if __name__ == "__main__":
    main()