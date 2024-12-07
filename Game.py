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
    A class to handle UART communication with serial devices.

    Attributes
    ----------
    ser : serial.Serial
        Serial object for communication
    permission_error_shown : bool
        Flag to track if the permission error has been shown
    stop_auto_receive : bool
        Flag to stop the auto-receive loop
    """
    def __init__(self):
        """
        Initializes UARTCommunication with default settings.
        """
        self.ser = None

    def list_ports(self):
        """
        Lists available serial ports.

        Returns
        -------
        list of str
            A list of port device names.
        """
        return [port.device for port in serial.tools.list_ports.comports()]
        
    def open_port(self, port, baud_rate=9600):
        """
        Opens a serial port.

        Parameters
        ----------
        port : str
            The name of the port to open.
        baud_rate : int, optional
            The baud rate for communication (default is 9600).

        Returns
        -------
        str
            Connection status message.
        """
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            return f"Connected to {port}"
        except Exception as e:
            self.ser = None
            return f"Error: {e}"

    def send_message(self, message):
        """
        Sends a JSON-formatted message via UART.

        Parameters
        ----------
        message : dict
            The message to send.

        Returns
        -------
        str
            Message status.
        """
        if self.ser and self.ser.is_open:
            try:
                json_message = json.dumps(message)
                self.ser.write((json_message + "\n").encode())
                return f"Sent: {json_message}"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

    def receive_message(self):
        """
        Receives and parses a JSON message from UART.

        Returns
        -------
        dict or str
            Parsed JSON message if valid, or an error message.
        """
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode().strip()
                    if response:
                        json_response = json.loads(response)
                        return json_response
            except json.JSONDecodeError:
                return "Error: Invalid JSON received"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"


def update_game_board(board, buttons):
    """
    Updates the GUI game board with the current board state.

    @param board A 2D list representing the game board.
    @param buttons The GUI button widgets for each cell in the game board.
    """
    for i in range(3):
        for j in range(3):
            buttons[i][j].config(text=board[i][j])


def send_move(uart, row, col):
    """
    Sends a MOVE command with the selected row and column to the UART.

    @param uart The UARTCommunication instance for sending the command.
    @param row The row of the move.
    @param col The column of the move.
    """
    message = {"command": "MOVE", "row": row, "col": col}
    uart.send_message(message)


def set_mode(uart, mode):
    """
    Sends a MODE command to the UART to set the game mode.

    @param uart The UARTCommunication instance for sending the command.
    @param mode The game mode to set (e.g., 0 for User vs User).
    """
    message = {"command": "MODE", "mode": mode}
    uart.send_message(message)


def reset_game(uart):
    """
    Sends a RESET command to the UART to reset the game.

    @param uart The UARTCommunication instance for sending the command.
    """
    message = {"command": "RESET"}
    uart.send_message(message)


def auto_receive(uart, buttons, output_text, root):
    """
    Periodically checks for incoming messages on the UART and updates the GUI accordingly.
    """
    try:
        if uart.ser and uart.ser.is_open:
            response = uart.receive_message()
            if response and response != "Port not opened":
                if isinstance(response, dict):
                    if "board" in response:
                        update_game_board(response["board"], buttons)
                    else:
                        output_text.insert(tk.END, f"Game status: {response['message']}\n")

                    if response.get("type") == "win_status":
                        thread = threading.Thread(target=messagebox.showinfo, args=("Win Status",
                                                                                    response.get("message")))
                        thread.start()

                else:
                    output_text.insert(tk.END, f"Received: {response}\n")
                output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
    root.after(100, lambda: auto_receive(uart, buttons, output_text, root))


def start_gui():
    """
    Initializes and starts the GUI for the Tic-Tac-Toe game.
    """
    uart = UARTCommunication()

    root = tk.Tk()
    root.title("TicTacToe Game Interface")
    root.config(bg="#f0f0f0")  # Set background color

    # Font configurations
    font_style = ("Helvetica", 12)
    font_large = ("Helvetica", 16, "bold")

    port_label = tk.Label(root, text="Select Port:", font=font_style, bg="#f0f0f0")
    port_label.grid(row=0, column=0, padx=10, pady=10)
    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly", font=font_style)
    port_combobox.grid(row=0, column=1, padx=10, pady=10)

    def open_port_callback():
        """
        Opens the selected port and starts auto-receive if successful.
        """
        status = uart.open_port(port_var.get())
        status_label.config(text=status)
        if "Connected" in status:
            auto_receive(uart, buttons, output_text, root)
        else:
            output_text.insert(tk.END, f"Failed to connect: {status}\n")

    open_button = tk.Button(root, text="Open Port", command=open_port_callback, font=font_style, relief="solid", 
                            width=12, height=2, bg="#4CAF50", fg="white", bd=2, activebackground="#45a049")
    open_button.grid(row=0, column=2, padx=10, pady=10)

    buttons = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            button = tk.Button(root, text=" ", width=10, height=3, font=font_large,
                               command=lambda row=i, col=j: send_move(uart, row, col), relief="solid", 
                               bg="#e7e7e7", fg="black", activebackground="#d1d1d1")
            button.grid(row=i + 1, column=j, padx=5, pady=5)
            buttons[i][j] = button

    mode_label = tk.Label(root, text="Select Game Mode:", font=font_style, bg="#f0f0f0")
    mode_label.grid(row=4, column=0, padx=10, pady=10)
    mode_var = tk.StringVar(value="User vs User")
    mode_combobox = ttk.Combobox(root, textvariable=mode_var,
                                 values=["User vs User", "User vs AI", "AI vs AI"],
                                 state="readonly", font=font_style)
    mode_combobox.grid(row=4, column=1, padx=10, pady=10)

    def set_mode_callback():
        mode_index = mode_combobox.current()
        set_mode(uart, mode_index)
        status_label.config(text=f"Game mode set to {mode_combobox.get()}")

    mode_button = tk.Button(root, text="Set Mode", command=set_mode_callback, font=font_style, relief="solid", 
                            width=12, height=2, bg="#4CAF50", fg="white", bd=2, activebackground="#45a049")
    mode_button.grid(row=4, column=2, padx=10, pady=10)

    reset_button = tk.Button(root, text="Reset", command=lambda: reset_game(uart), font=font_style, relief="solid", 
                             width=12, height=2, bg="#f44336", fg="white", bd=2, activebackground="#e53935")
    reset_button.grid(row=5, column=1, padx=10, pady=10)

    output_text = scrolledtext.ScrolledText(root, width=50, height=10, wrap=tk.WORD, font=("Courier New", 10), 
                                            bg="#f4f4f4", fg="#333333")
    output_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

    status_label = tk.Label(root, text="Status: Not connected", fg="blue", bg="#f0f0f0", font=font_style)
    status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
