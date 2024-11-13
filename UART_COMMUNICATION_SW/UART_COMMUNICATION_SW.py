# -*- coding: utf-8 -*-

import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, scrolledtext

class UARTCommunication:
    def __init__(self):
        self.ser = None
        self.baud_rate = 9600  #Set the initial baud rate
        self.access_denied_shown = False  #Flag that displays access error only once
        self.stop_auto_receive = False  # Flag that stops the message receiving cycle

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port):
        if self.ser and self.ser.is_open:
            self.ser.close()

        try:
            self.ser = serial.Serial(port, self.baud_rate, timeout=1)
            self.access_denied_shown = False  # Clear the flag if the connection is successful
            self.stop_auto_receive = False  # Allow auto-recieve
            return f"Connected to {port} at {self.baud_rate} baud"
        except serial.SerialException as e:
            self.ser = None
            if not self.access_denied_shown:
                self.access_denied_shown = True
                return f"Error: Could not open port {port} - {e}"
            return ""
        except PermissionError as e:
            if self.ser and self.ser.is_open:
                self.ser.close()  # Closing the port in case of access error
            self.ser = None
            if not self.access_denied_shown:
                self.access_denied_shown = True
                self.stop_auto_receive = True  # Stop auto-recieve
                return f"Error: Access denied to port {port} - {e}"
            return ""

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser.baudrate = baud_rate
            self.ser.open()

    def send_message(self, message):
        if self.ser and self.ser.is_open:
            self.ser.write((message + "\n").encode())
            return f"Sent: {message}"
        return "Port not opened"

    def receive_message(self):
        if self.ser and self.ser.is_open:
            try:
                response = self.ser.readline().decode("utf-8", errors="replace").strip()
                if response:
                    return response
            except Exception as e:
                self.stop_auto_receive = True  # Stop auto-recieve on error
                return f"Error: {e}"
        return "Port not opened"

def auto_receive(uart, output_text, status_label, root):
    if uart.stop_auto_receive:
        return  #  Stop the loop if we receive an error

    response = uart.receive_message()
    if response and response != "Port not opened":
        output_text.insert(tk.END, f"Received: {response}\n")
        output_text.see(tk.END)
    root.after(100, lambda: auto_receive(uart, output_text, status_label, root))

def start_gui():
    uart = UARTCommunication()
    root = tk.Tk()
    root.title("UART Communication Interface")

    port_label = tk.Label(root, text="Select Port:")
    port_label.grid(row=0, column=0, padx=10, pady=10)

    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly")
    port_combobox.grid(row=0, column=1, padx=10, pady=10)

    baud_label = tk.Label(root, text="Baud Rate:")
    baud_label.grid(row=1, column=0, padx=10, pady=10)

    baud_var = tk.StringVar(value="9600")
    baud_combobox = ttk.Combobox(root, textvariable=baud_var, values=["4800", "9600", "19200", "57600", "115200"], state="readonly")
    baud_combobox.grid(row=1, column=1, padx=10, pady=10)

    def update_baud_rate():
        try:
            baud_rate = int(baud_var.get())
            uart.set_baud_rate(baud_rate)
            status_label.config(text=f"Baud rate set to {baud_rate}")
        except ValueError:
            status_label.config(text="Invalid baud rate selected")

    baud_combobox.bind("<<ComboboxSelected>>", lambda _: update_baud_rate())

    def open_port_callback():
        status = uart.open_port(port_var.get())
        if status:
            status_label.config(text=status)
        if "Connected" in status:
            auto_receive(uart, output_text, status_label, root)

    open_button = tk.Button(root, text="Open Port", command=open_port_callback)
    open_button.grid(row=0, column=2, padx=10, pady=10)

    message_label = tk.Label(root, text="Message:")
    message_label.grid(row=2, column=0, padx=10, pady=10)

    message_entry = tk.Entry(root)
    message_entry.grid(row=2, column=1, padx=10, pady=10)

    def send_message_callback():
        status = uart.send_message(message_entry.get())
        status_label.config(text=status)

    send_button = tk.Button(root, text="Send", command=send_message_callback)
    send_button.grid(row=2, column=2, padx=10, pady=10)

    output_text = scrolledtext.ScrolledText(root, width=50, height=10, wrap=tk.WORD)
    output_text.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

    status_label = tk.Label(root, text="Status: Not connected", fg="blue")
    status_label.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    start_gui()