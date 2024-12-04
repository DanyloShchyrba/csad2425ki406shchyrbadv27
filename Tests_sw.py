import unittest
from unittest.mock import MagicMock, patch
from Game import UARTCommunication, update_game_board, send_move, set_mode, reset_game, auto_receive
from tkinter import Tk
from io import StringIO
from tkinter import scrolledtext
import tkinter as tk


class TestUARTCommunication(unittest.TestCase):
    def setUp(self):
        self.uart = UARTCommunication()

    @patch('serial.Serial')
    def test_open_port_successful_connection(self, mock_serial):
        mock_serial.return_value.is_open = True
        result = self.uart.open_port('COM3')
        self.assertEqual(result, "Connected to COM3")
        self.assertTrue(self.uart.ser.is_open)

    @patch('serial.Serial')
    def test_open_port_connection_failure(self, mock_serial):
        mock_serial.side_effect = Exception("Port error")
        result = self.uart.open_port('COM3')
        self.assertIn("Error: Port error", result)
        self.assertIsNone(self.uart.ser)

    @patch('serial.Serial')
    def test_send_message_successfully(self, mock_serial):
        self.uart.ser = mock_serial()
        self.uart.ser.is_open = True
        message = {"command": "MOVE", "row": 1, "col": 2}
        result = self.uart.send_message(message)
        self.assertIn("Sent:", result)

    def test_send_message_without_open_port(self):
        result = self.uart.send_message({"command": "MOVE"})
        self.assertEqual(result, "Port not opened")

    @patch('serial.Serial')
    def test_receive_message_successfully(self, mock_serial):
        self.uart.ser = mock_serial()
        self.uart.ser.is_open = True
        self.uart.ser.in_waiting = 1
        self.uart.ser.readline.return_value = b'{"board": [["X", "", ""], ["", "O", ""], ["", "", ""]]}'
        result = self.uart.receive_message()
        self.assertEqual(result, {"board": [["X", "", ""], ["", "O", ""], ["", "", ""]]})

    @patch('serial.Serial')
    def test_receive_message_without_open_port(self, mock_serial):
        result = self.uart.receive_message()
        self.assertEqual(result, "Port not opened")

    def test_receive_message_with_invalid_json(self):
        self.uart.ser = MagicMock()
        self.uart.ser.is_open = True
        self.uart.ser.in_waiting = 1
        self.uart.ser.readline.return_value = b'Invalid JSON'
        result = self.uart.receive_message()
        self.assertIn("Error:", result)


class TestGameCommands(unittest.TestCase):
    def setUp(self):
        self.uart = UARTCommunication()  # Ensure uart is set up for each test

    def test_update_game_board(self):
        root = Tk()
        buttons = [[tk.Button(root, text=" ") for _ in range(3)] for _ in range(3)]
        board = [["X", "O", "X"], ["O", "X", "O"], ["X", "O", "X"]]
        update_game_board(board, buttons)
        for i in range(3):
            for j in range(3):
                self.assertEqual(buttons[i][j]["text"], board[i][j])
        root.destroy()

    @patch.object(UARTCommunication, 'send_message')
    def test_send_move(self, mock_send_message):
        send_move(self.uart, 1, 1)
        mock_send_message.assert_called_with({"command": "MOVE", "row": 1, "col": 1})

    @patch.object(UARTCommunication, 'send_message')
    def test_set_mode(self, mock_send_message):
        set_mode(self.uart, 1)
        mock_send_message.assert_called_with({"command": "MODE", "mode": 1})

    @patch.object(UARTCommunication, 'send_message')
    def test_reset_game(self, mock_send_message):
        reset_game(self.uart)
        mock_send_message.assert_called_with({"command": "RESET"})

    @patch('serial.Serial')
    def test_auto_receive_no_data(self, mock_serial):
        mock_serial.return_value = MagicMock(is_open=True, in_waiting=2)
        self.uart.ser = mock_serial()
        root = Tk()
        buttons = [[tk.Button(root, text=" ") for _ in range(3)] for _ in range(3)]
        output_text = scrolledtext.ScrolledText(root, width=50, height=10)

        # Simulate no data received
        mock_serial().readline.return_value = b''
        auto_receive(self.uart, buttons, output_text, root) 

        # Check if no board update happens
        for i in range(3):
            for j in range(3):
                self.assertEqual(buttons[i][j]["text"], " ")

        root.destroy()

    def test_uart_initialization(self):
        uart = UARTCommunication()
        self.assertIsNone(uart.ser)

    @patch('serial.Serial')
    def test_auto_receive_valid_response(self, mock_serial):
        mock_serial.return_value = MagicMock(is_open=True, in_waiting=1)
        mock_serial().readline.return_value = b'{"board": [["X", "O", "X"], ["O", "X", "O"], ["X", "O", "X"]]}'
        self.uart.ser = mock_serial()
        root = Tk()
        buttons = [[tk.Button(root, text=" ") for _ in range(3)] for _ in range(3)]
        output_text = scrolledtext.ScrolledText(root, width=50, height=10)

        # Simulate receiving a valid game board response
        auto_receive(self.uart, buttons, output_text, root)

        # Check if the board was updated correctly
        for i in range(3):
            for j in range(3):
                self.assertEqual(buttons[i][j]["text"], ["X", "O", "X", "O", "X", "O", "X", "O", "X"][i * 3 + j])
        root.destroy()

    @patch('serial.Serial')
    def test_auto_receive_invalid_json(self, mock_serial):
        mock_serial.return_value = MagicMock(is_open=True, in_waiting=1)
        mock_serial().readline.return_value = b'{"board": [["X", "O", "X"], ["O", "X", "O"]]}'
        self.uart.ser = mock_serial()
        root = Tk()
        buttons = [[tk.Button(root, text=" ") for _ in range(3)] for _ in range(3)]
        output_text = scrolledtext.ScrolledText(root, width=50, height=10)

        # Simulate receiving an invalid game board response
        auto_receive(self.uart, buttons, output_text, root)

        # Check if error message is displayed
        self.assertIn("Error:", output_text.get("1.0", tk.END))
        root.destroy()

if __name__ == '__main__':
    unittest.main()

