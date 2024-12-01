
#include <Arduino.h>
#include <ArduinoJson.h>

/// The size of the Tic-Tac-Toe board (3x3).
const int BOARD_SIZE = 3;

/// The Tic-Tac-Toe board represented as a 2D character array.
char board[BOARD_SIZE][BOARD_SIZE];

/// The current player ('X' or 'O').
char currentPlayer = 'X';

/// A flag indicating if the game is over.
bool gameOver = false;

/// The game mode: 0 = Player vs Player, 1 = Player vs AI, 2 = AI vs AI.
int gameMode = 0;

/**
 * @brief Initializes the game board and resets game state.
 *        All cells are set to an empty space (' '), and the current player is set to 'X'.
 *        The gameOver flag is reset to false.
 */
void initializeBoard() {
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            board[i][j] = ' '; // Set all cells to empty
        }
    }
    currentPlayer = 'X'; // Set the starting player to 'X'
    gameOver = false;    // Reset the game over flag
}

/**
 * @brief Sends a JSON message over Serial.
 * @param type The type of the message (e.g., "info", "error", "win_status").
 * @param message The content of the message to be sent.
 * 
 * This function is used for communicating game state or errors to an external interface.
 */
void sendJsonMessage(const char* type, const char* message) {
    StaticJsonDocument<200> doc;
    doc["type"] = type;
    doc["message"] = message;
    serializeJson(doc, Serial); // Serialize the JSON and send it via Serial
    Serial.println();
}

/**
 * @brief Sends the current state of the game board as a JSON message.
 */
void sendBoardState() {
    StaticJsonDocument<300> doc;
    doc["type"] = "board"; // Indicate the message contains the board state
    JsonArray boardArray = doc.createNestedArray("board");
    for (int i = 0; i < BOARD_SIZE; i++) {
        JsonArray row = boardArray.createNestedArray(); // Create an array for each row
        for (int j = 0; j < BOARD_SIZE; j++) {
            row.add(String(board[i][j])); // Add each cell value to the row
        }
    }
    serializeJson(doc, Serial); // Send the JSON-encoded board state
    Serial.println();
}

/**
 * @brief Checks if the current player has won the game.
 * @return True if the current player has achieved a winning condition, otherwise false.
 * 
 * Winning conditions include:
 * - Three matching symbols in any row
 * - Three matching symbols in any column
 * - Three matching symbols along either diagonal
 */
bool checkWin() {
    for (int i = 0; i < BOARD_SIZE; i++) {
        // Check rows and columns
        if (board[i][0] == currentPlayer && board[i][1] == currentPlayer && board[i][2] == currentPlayer) return true;
        if (board[0][i] == currentPlayer && board[1][i] == currentPlayer && board[2][i] == currentPlayer) return true;
    }
    // Check diagonals
    if (board[0][0] == currentPlayer && board[1][1] == currentPlayer && board[2][2] == currentPlayer) return true;
    if (board[0][2] == currentPlayer && board[1][1] == currentPlayer && board[2][0] == currentPlayer) return true;
    return false; // No winning condition met
}

/**
 * @brief Checks if the game has ended in a draw.
 * @return True if all cells are filled and there is no winner, otherwise false.
 * 
 * A draw occurs when all cells are occupied, and no player meets a winning condition.
 */
bool checkDraw() {
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            if (board[i][j] == ' ') return false; // At least one empty cell remains
        }
    }
    return true; // All cells are filled
}

/**
 * @brief Makes a random move for the AI player.
 * 
 * The function randomly selects an empty cell on the board and places the AI's symbol there.
 * This logic is used for basic AI functionality.
 */
void aiMoveRandom() {
    while (true) {
        int row = random(0, BOARD_SIZE);
        int col = random(0, BOARD_SIZE);
        if (board[row][col] == ' ') { // Check if the cell is empty
            board[row][col] = currentPlayer; // Place the AI's symbol
            break; // Exit the loop after a valid move
        }
    }
}

/**
 * @brief Handles the AI vs AI game mode, where both players are controlled by AI.
 * 
 * This function alternates between AI players making moves until there is a winner or a draw.
 * After each move, the board state is sent to the external interface.
 */
void handleAiVsAi() {
    while (!gameOver) {
        if (checkDraw()) {
            sendJsonMessage("win_status", "It's a draw!");
            gameOver = true;
            return;
        }
        aiMoveRandom(); // AI makes a random move
        if (checkWin()) {
            String message = "Player " + String(currentPlayer) + " wins!";
            sendBoardState();
            sendJsonMessage("win_status", message.c_str());
            gameOver = true;
            return;
        }
        currentPlayer = (currentPlayer == 'X') ? 'O' : 'X'; // Switch players
        sendBoardState(); // Send the board state after each move
    }
}

/**
 * @brief Attempts to make a move for the current player at the specified cell.
 * @param row The row index of the cell.
 * @param col The column index of the cell.
 * @return True if the move is valid and successfully made, otherwise false.
 * 
 * This function checks if the move is within bounds, the cell is empty, and the game is not over.
 * If valid, it updates the board and checks for a win or draw condition.
 */
bool makeMove(int row, int col) {
    if (row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE && board[row][col] == ' ' && !gameOver) {
        board[row][col] = currentPlayer; // Place the current player's symbol
        if (checkWin()) {
            String message = "Player " + String(currentPlayer) + " wins!";
            sendJsonMessage("win_status", message.c_str());
            gameOver = true;
        } else if (checkDraw()) {
            sendJsonMessage("win_status", "It's a draw!");
            gameOver = true;
        } else {
            currentPlayer = (currentPlayer == 'X') ? 'O' : 'X'; // Switch to the other player
        }
        return true;
    }
    return false; // Invalid move
}

/**
 * @brief Arduino setup function, initializes the game and sends a startup message.
 * 
 * This function runs once when the Arduino is powered on or reset.
 */
void setup() {
    Serial.begin(9600); // Initialize Serial communication
    initializeBoard();  // Initialize the game board
    sendJsonMessage("info", "TicTacToe Game Started"); // Send a startup message
}

/**
 * @brief Arduino loop function, handles game commands received over Serial.
 * 
 * This function listens for JSON-formatted commands to perform actions such as making a move,
 * resetting the game, or changing the game mode.
 */
void loop() {
    if (Serial.available() > 0) {
        StaticJsonDocument<200> doc;
        String input = Serial.readStringUntil('\n'); // Read the incoming command
        DeserializationError error = deserializeJson(doc, input);

        if (!error) { // Ensure the JSON command is valid
            const char* command = doc["command"];
            if (strcmp(command, "MOVE") == 0) { // Handle a move command
                int row = doc["row"];
                int col = doc["col"];
                if (makeMove(row, col)) {
                    sendBoardState();
                } else {
                    sendJsonMessage("error", "Invalid move.");
                }
            } else if (strcmp(command, "RESET") == 0) { // Handle game reset
                initializeBoard();
                sendJsonMessage("game_status", "Game reset.");
                sendBoardState();
            } else if (strcmp(command, "MODE") == 0) { // Handle mode change
                gameMode = doc["mode"];
                String message = "Game mode set to " + String(gameMode);
                sendJsonMessage("game_mode", message.c_str());  // Send game mode message first
                initializeBoard();
                sendJsonMessage("game_status", "Game reset.");
                sendBoardState();
            }

            // Handle AI moves if applicable
            if (gameMode == 1 && !gameOver && currentPlayer == 'O') {
                aiMoveRandom();// Make a random move for the AI
                if (checkWin()) {
                    String message = "Player " + String(currentPlayer) + " wins!";
                    sendJsonMessage("win_status", message.c_str());
                    gameOver = true;
                } else if (checkDraw()) {
                    sendJsonMessage("win_status", "It's a draw!");
                    gameOver = true;
                }
                currentPlayer = 'X'; // Switch back to Player X
                sendBoardState();
            } else if (gameMode == 2 && !gameOver) {
                handleAiVsAi(); // Handle AI vs AI
            }
        }
    }
}
