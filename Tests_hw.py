# -*- coding: utf-8 -*-

import unittest
import serial
import json
import time
import logging

# Logging setup
logging.basicConfig(filename="test_results.log", level=logging.DEBUG, format="%(asctime)s - %(message)s")

class TicTacToeArduinoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ser = serial.Serial(cls.SERIAL_PORT, cls.BAUD_RATE, timeout=1)
        time.sleep(2)  # Allow time for the Arduino to reset

    @classmethod
    def tearDownClass(cls):
        cls.ser.close()

    def send_game_command(self, command_dict):
        self.ser.write((json.dumps(command_dict) + '\n').encode())
        time.sleep(0.5)  # Small delay to allow Arduino to process

    def receive_game_response(self):
        if self.ser.in_waiting > 0:
            line = self.ser.readline()
            try:
                decoded_line = line.decode("utf-8").strip()
                return json.loads(decoded_line)
            except UnicodeDecodeError:
                return None

        return None

    def test_initialize_board(self):
        self.send_game_command({"command": "RESET"})
        response1 = self.receive_game_response()
        response2 = self.receive_game_response()
        self.assertIsNotNone(response2)

        if response2["type"] == "game_status":
            self.assertEqual(response2["message"], "Game reset.")
            response2 = self.receive_game_response()

        self.assertEqual(response2["type"], "board")
        board_state = response2.get("board", [])
        for row in board_state:
            for cell in row:
                self.assertEqual(cell, " ")
        logging.info("test_initialize_board passed.")

    def test_make_invalid_move(self):
        self.send_game_command({"command": "RESET"})
        self.receive_game_response()
        self.receive_game_response()

        self.send_game_command({"command": "MOVE", "row": 0, "col": 0})
        self.receive_game_response()

        self.send_game_command({"command": "MOVE", "row": 0, "col": 0})
        response = self.receive_game_response()
        self.assertIsNotNone(response)
        if response["type"] == "error":
            self.assertEqual(response["message"], "Invalid move.")
        else:
            self.assertEqual(response["type"], "board")
        logging.info("test_make_invalid_move passed.")

    def test_game_mode_switch(self):
        self.send_game_command({"command": "MODE", "mode": 1})
        responses = {"game_mode": False, "game_status": False, "board": False}

        for _ in range(5):
            response = self.receive_game_response()
            if response:
                response_type = response["type"]
                if response_type == "game_mode":
                    responses["game_mode"] = True
                    self.assertIn("Game mode set to 1", response["message"])
                elif response_type == "game_status":
                    responses["game_status"] = True
                    self.assertEqual(response["message"], "Game reset.")

                if all(responses.values()):
                    break

        self.send_game_command({"command": "MODE", "mode": 2})
        responses = {"game_mode": False, "game_status": False, "board": False}

        for _ in range(5):
            response = self.receive_game_response()
            if response:
                response_type = response["type"]
                if response_type == "game_mode":
                    responses["game_mode"] = True
                    self.assertIn("Game mode set to 2", response["message"])
                elif response_type == "game_status":
                    responses["game_status"] = True
                    self.assertEqual(response["message"], "Game reset.")
                elif response_type == "board":
                    responses["board"] = True
                    board_state = response["board"]
                    for row in board_state:
                        for cell in row:
                            self.assertEqual(cell, " ")
                if all(responses.values()):
                    break
        logging.info("test_game_mode_switch passed.")

    def test_handle_ai_vs_ai(self):
        self.send_game_command({"command": "MODE", "mode": 2})
        self.receive_game_response()
        self.receive_game_response()

        while True:
            response = self.receive_game_response()
            if response and response["type"] == "win_status":
                self.assertIn(response["message"], ["Player X wins!", "Player O wins!", "It's a draw!"])
                break
        logging.info("test_handle_ai_vs_ai passed.")


if __name__ == '__main__':
    import argparse
    import sys

    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Run TicTacToe Arduino tests.")
    parser.add_argument('serial_port', type=str, help='Serial port for Arduino connection (e.g., COM6)')
    parser.add_argument('baud_rate', type=int, help='Baud rate for Arduino connection (e.g., 9600)')
    args = parser.parse_args()

    # Set parameters for the test class
    TicTacToeArduinoTests.SERIAL_PORT = args.serial_port
    TicTacToeArduinoTests.BAUD_RATE = args.baud_rate

    # Run the tests
    sys.argv = sys.argv[:1]  # Clear additional args for unittest
    unittest.main(argv=sys.argv)
