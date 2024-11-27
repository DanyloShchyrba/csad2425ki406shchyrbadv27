import unittest
from unittest.mock import MagicMock, patch
from GUI import UARTCommunication, send_move, set_mode, reset_game
import logging

logging.basicConfig(filename="test_results.log", level=logging.INFO, format="%(asctime)s - %(message)s")

class TestUARTCommunication(unittest.TestCase):
    def setUp(self):
        self.uart = UARTCommunication()

    @patch('serial.Serial')
    def test_open_port_successful_connection(self, mock_serial):
        mock_serial.return_value.is_open = True
        result = self.uart.open_port('COM3')
        self.assertEqual(result, "Connected to COM3")
        self.assertTrue(self.uart.ser.is_open)
        logging.info("test_open_port_successful_connection passed.")

    @patch('serial.Serial')
    def test_open_port_connection_failure(self, mock_serial):
        mock_serial.side_effect = Exception("Port error")
        result = self.uart.open_port('COM3')
        self.assertIn("Error: Port error", result)
        self.assertIsNone(self.uart.ser)
        logging.info("test_open_port_connection_failure passed.")

    @patch('serial.Serial')
    def test_send_message_successfully(self, mock_serial):
        self.uart.ser = mock_serial()
        self.uart.ser.is_open = True
        message = {"command": "MOVE", "row": 1, "col": 2}
        result = self.uart.send_message(message)
        self.assertIn("Sent:", result)
        logging.info("test_send_message_successfully passed.")

    def test_send_message_without_open_port(self):
        result = self.uart.send_message({"command": "MOVE"})
        self.assertEqual(result, "Port not opened")
        logging.info("test_send_message_without_open_port passed.")

    @patch('serial.Serial')
    def test_receive_message_successfully(self, mock_serial):
        self.uart.ser = mock_serial()
        self.uart.ser.is_open = True
        self.uart.ser.in_waiting = 1
        self.uart.ser.readline.return_value = b'{"board": [["X", "", ""], ["", "O", ""], ["", "", ""]]}'
        result = self.uart.receive_message()
        self.assertEqual(result, {"board": [["X", "", ""], ["", "O", ""], ["", "", ""]]})
        logging.info("test_receive_message_successfully passed.")

    @patch('serial.Serial')
    def test_receive_message_without_open_port(self, mock_serial):
        result = self.uart.receive_message()
        self.assertEqual(result, "Port not opened")
        logging.info("test_receive_message_without_open_port passed.")

    def test_receive_message_with_invalid_json(self):
        self.uart.ser = MagicMock()
        self.uart.ser.is_open = True
        self.uart.ser.in_waiting = 1
        self.uart.ser.readline.return_value = b'Invalid JSON'
        result = self.uart.receive_message()
        self.assertIn("Error:", result)
        logging.info("test_receive_message_with_invalid_json passed.")


class TestGameCommands(unittest.TestCase):
    def setUp(self):
        self.uart = MagicMock()

    def test_send_move_command(self):
        send_move(self.uart, 1, 1)
        self.uart.send_message.assert_called_once_with({"command": "MOVE", "row": 1, "col": 1})
        logging.info("test_send_move_command passed.")

    def test_set_game_mode(self):
        set_mode(self.uart, 1)
        self.uart.send_message.assert_called_once_with({"command": "MODE", "mode": 1})
        logging.info("test_set_game_mode passed.")

    def test_reset_game_command(self):
        reset_game(self.uart)
        self.uart.send_message.assert_called_once_with({"command": "RESET"})
        logging.info("test_reset_game_command passed.")


if __name__ == '__main__':
    unittest.main()
    logging.info("All tests in tests.py executed successfully.")
    print("All tests in tests.py passed successfully!")
