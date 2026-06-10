
import tkinter as tk
from tkinter import messagebox


class TicTacToe:

    def __init__(self, root):

        self.root = root
        self.root.title("⭕❌ 永不平手井字遊戲")
        self.root.geometry("360x420")
        self.root.resizable(False, False)

        self.current_player = "X"

        self.board = [""] * 9

        # 紀錄落子順序
        self.move_history = []

        self.buttons = []

        self.create_ui()

    def create_ui(self):

        title = tk.Label(
            self.root,
            text="⭕❌ 永不平手井字遊戲",
            font=("Microsoft JhengHei", 16, "bold")
        )

        title.pack(pady=10)

        self.status_label = tk.Label(
            self.root,
            text="輪到玩家 X",
            font=("Microsoft JhengHei", 12)
        )

        self.status_label.pack()

        board_frame = tk.Frame(self.root)
        board_frame.pack(pady=15)

        for row in range(3):

            for col in range(3):

                index = row * 3 + col

                btn = tk.Button(
                    board_frame,
                    text="",
                    width=4,
                    height=2,
                    font=("Arial", 20, "bold"),
                    command=lambda idx=index: self.make_move(idx)
                )

                btn.grid(
                    row=row,
                    column=col,
                    padx=3,
                    pady=3
                )

                self.buttons.append(btn)

        reset_btn = tk.Button(
            self.root,
            text="重新開始",
            command=self.reset_game,
            width=15
        )

        reset_btn.pack(pady=10)

    def make_move(self, index):

        if self.board[index] != "":
            return

        self.board[index] = self.current_player

        self.move_history.append(index)

        self.buttons[index].config(
            text=self.current_player
        )

        winner = self.check_winner()

        if winner:

            messagebox.showinfo(
                "遊戲結束",
                f"🎉 玩家 {winner} 獲勝！"
            )

            self.reset_game()

            return

        # 棋盤滿了但沒人贏
        if "" not in self.board:

            self.remove_oldest_piece()

        if self.current_player == "X":
            self.current_player = "O"
        else:
            self.current_player = "X"

        self.status_label.config(
            text=f"輪到玩家 {self.current_player}"
        )

    def remove_oldest_piece(self):

        if len(self.move_history) == 0:
            return

        oldest_index = self.move_history.pop(0)

        self.board[oldest_index] = ""

        self.buttons[oldest_index].config(
            text=""
        )

        self.status_label.config(
            text="棋盤已滿，自動移除最早落子的棋子"
        )

    def check_winner(self):

        wins = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],

            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],

            [0, 4, 8],
            [2, 4, 6]
        ]

        for a, b, c in wins:

            if (
                self.board[a] != ""
                and self.board[a] == self.board[b]
                and self.board[b] == self.board[c]
            ):
                return self.board[a]

        return None

    def reset_game(self):

        self.current_player = "X"

        self.board = [""] * 9

        self.move_history = []

        for btn in self.buttons:

            btn.config(text="")

        self.status_label.config(
            text="輪到玩家 X"
        )


root = tk.Tk()

game = TicTacToe(root)

root.mainloop()

