# -*- coding: utf-8 -*-

import threading
import serial
import serial.tools.list_ports
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox


class UARTCommunication:
    """
    @class UARTCommunication
    @brief Handles UART communication with the Arduino board.
    """

    def __init__(self):
        """
        @brief Initializes UART communication object.
        """
        self.ser = None

    def list_ports(self):
        """
        @brief Lists all available COM ports.
        @return List of port names.
        """
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port, baud_rate=9600):
        """
        @brief Opens a specified serial port.
        @param port The name of the port to open.
        @param baud_rate The baud rate for the connection (default: 9600).
        @return A status message indicating success or failure.
        """
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            return f"Connected to {port} at {baud_rate} baud."
        except Exception as e:
            return f"Failed to connect: {e}"

    def send_message(self, message):
        """
        @brief Sends a JSON-encoded message over the serial port.
        @param message The message to be sent as a dictionary.
        @return A status message indicating success or failure.
        """
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((json.dumps(message) + '\n').encode())
                return "Message sent."
            except Exception as e:
                return f"Failed to send message: {e}"
        return "Serial port is not open."

    def receive_message(self):
        """
        @brief Reads and parses a JSON message from the serial port.
        @return A dictionary containing the received data or an error message.
        """
        if self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode().strip()
                return json.loads(line)
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Serial port is not open."}

def update_game_board(board, buttons):
    """
    @brief Updates the GUI buttons to reflect the current board state.
    @param board The 3x3 board state as a list of lists.
    @param buttons The 3x3 grid of GUI buttons.
    """
    for i in range(3):
        for j in range(3):
            buttons[i][j].config(text=board[i][j])

def send_move(uart, row, col):
    """
    @brief Sends a move command to the Arduino.
    @param uart The UARTCommunication instance.
    @param row The row index of the move.
    @param col The column index of the move.
    """
    response = uart.send_message({"command": "MOVE", "row": row, "col": col})
    print(response)

def set_mode(uart, mode):
    """
    @brief Sends a command to set the game mode.
    @param uart The UARTCommunication instance.
    @param mode The selected game mode.
    """
    response = uart.send_message({"command": "MODE", "mode": mode})
    print(response)

def reset_game(uart):
    """
    @brief Sends a command to reset the game.
    @param uart The UARTCommunication instance.
    """
    response = uart.send_message({"command": "RESET"})
    print(response)

def auto_receive(uart, buttons, output_text, root):
    """
    @brief Continuously receives messages from the Arduino and updates the GUI.
    @param uart The UARTCommunication instance.
    @param buttons The 3x3 grid of GUI buttons.
    @param output_text The output text widget for displaying messages.
    @param root The root Tkinter window.
    """
    def task():
        while True:
            response = uart.receive_message()
            if response:
                if "type" in response and response["type"] == "board":
                    update_game_board(response["board"], buttons)
                elif "type" in response and response["type"] == "win_status":
                    messagebox.showinfo("Game Status", response["message"])
                output_text.insert(tk.END, json.dumps(response) + '\n')
                output_text.see(tk.END)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()

def start_gui():
    """
    @brief Initializes and starts the Tkinter GUI.
    """
    root = tk.Tk()
    root.title("Tic-Tac-Toe Controller")

    uart = UARTCommunication()

    # Serial Port Configuration
    port_frame = ttk.LabelFrame(root, text="Serial Port Configuration")
    port_frame.grid(row=0, column=0, padx=10, pady=10)

    port_label = ttk.Label(port_frame, text="Port:")
    port_label.grid(row=0, column=0, padx=5, pady=5)

    port_combo = ttk.Combobox(port_frame, values=uart.list_ports())
    port_combo.grid(row=0, column=1, padx=5, pady=5)

    baud_label = ttk.Label(port_frame, text="Baud Rate:")
    baud_label.grid(row=1, column=0, padx=5, pady=5)

    baud_combo = ttk.Combobox(port_frame, values=[9600, 115200])
    baud_combo.grid(row=1, column=1, padx=5, pady=5)
    baud_combo.set(9600)

    def connect():
        port = port_combo.get()
        baud = int(baud_combo.get())
        messagebox.showinfo("Connection Status", uart.open_port(port, baud))

    connect_button = ttk.Button(port_frame, text="Connect", command=connect)
    connect_button.grid(row=2, column=0, columnspan=2, pady=5)

    # Game Controls
    control_frame = ttk.LabelFrame(root, text="Game Controls")
    control_frame.grid(row=1, column=0, padx=10, pady=10)

    mode_var = tk.IntVar(value=0)
    ttk.Radiobutton(control_frame, text="Player vs Player", variable=mode_var, value=0).grid(row=0, column=0, padx=5, pady=5)
    ttk.Radiobutton(control_frame, text="Player vs AI", variable=mode_var, value=1).grid(row=0, column=1, padx=5, pady=5)
    ttk.Radiobutton(control_frame, text="AI vs AI", variable=mode_var, value=2).grid(row=0, column=2, padx=5, pady=5)

    def set_game_mode():
        set_mode(uart, mode_var.get())

    mode_button = ttk.Button(control_frame, text="Set Mode", command=set_game_mode)
    mode_button.grid(row=1, column=0, columnspan=3, pady=5)

    reset_button = ttk.Button(control_frame, text="Reset Game", command=lambda: reset_game(uart))
    reset_button.grid(row=2, column=0, columnspan=3, pady=5)

    # Game Board
    board_frame = ttk.LabelFrame(root, text="Game Board")
    board_frame.grid(row=2, column=0, padx=10, pady=10)

    buttons = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            buttons[i][j] = ttk.Button(board_frame, text=" ", width=5, command=lambda r=i, c=j: send_move(uart, r, c))
            buttons[i][j].grid(row=i, column=j, padx=5, pady=5)

    # Output Text Box
    output_text = tk.Text(root, height=10, width=50)
    output_text.grid(row=3, column=0, padx=10, pady=10)

    auto_receive(uart, buttons, output_text, root)

    root.mainloop()

if __name__ == "__main__":
    start_gui()