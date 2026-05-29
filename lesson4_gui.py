import tkinter as tk
from tkinter import ttk, messagebox
import random


class GuessNumberPro:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 猜數字大挑戰")
        self.root.geometry("500x420")
        self.root.configure(bg="#1E293B")
        self.root.resizable(False, False)

        self.best_score = None

        self.setup_ui()
        self.start_game()

    def setup_ui(self):

        title = tk.Label(
            self.root,
            text="🎯 猜數字大挑戰",
            font=("Microsoft JhengHei", 22, "bold"),
            bg="#1E293B",
            fg="#F8FAFC"
        )
        title.pack(pady=15)

        level_frame = tk.Frame(self.root, bg="#1E293B")
        level_frame.pack()

        tk.Label(
            level_frame,
            text="難度：",
            bg="#1E293B",
            fg="white",
            font=("Microsoft JhengHei", 11)
        ).pack(side=tk.LEFT)

        self.level = ttk.Combobox(
            level_frame,
            state="readonly",
            width=10
        )

        self.level["values"] = (
            "簡單(1-50)",
            "普通(1-100)",
            "困難(1-500)"
        )

        self.level.current(1)
        self.level.pack(side=tk.LEFT, padx=5)
        self.level.bind("<<ComboboxSelected>>",
                        lambda e: self.start_game())

        self.info_label = tk.Label(
            self.root,
            text="請輸入數字",
            font=("Microsoft JhengHei", 12),
            bg="#1E293B",
            fg="#38BDF8"
        )
        self.info_label.pack(pady=15)

        self.entry = tk.Entry(
            self.root,
            font=("Arial", 22),
            justify="center",
            width=10
        )
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", lambda e: self.check())

        self.guess_btn = tk.Button(
            self.root,
            text="猜看看",
            command=self.check,
            bg="#0EA5E9",
            fg="white",
            font=("Microsoft JhengHei", 12, "bold"),
            width=15
        )
        self.guess_btn.pack(pady=10)

        self.result_label = tk.Label(
            self.root,
            text="",
            font=("Microsoft JhengHei", 14, "bold"),
            bg="#1E293B",
            fg="#FACC15"
        )
        self.result_label.pack(pady=10)

        self.progress = ttk.Progressbar(
            self.root,
            length=300,
            maximum=10
        )
        self.progress.pack(pady=10)

        self.stats_label = tk.Label(
            self.root,
            text="",
            font=("Microsoft JhengHei", 10),
            bg="#1E293B",
            fg="#CBD5E1"
        )
        self.stats_label.pack()

        tk.Button(
            self.root,
            text="🔄 重新開始",
            command=self.start_game,
            bg="#22C55E",
            fg="white",
            font=("Microsoft JhengHei", 11),
            width=15
        ).pack(pady=15)

    def start_game(self):

        difficulty = self.level.get()

        if "50" in difficulty:
            self.max_num = 50
        elif "500" in difficulty:
            self.max_num = 500
        else:
            self.max_num = 100

        self.answer = random.randint(1, self.max_num)

        self.attempts = 0
        self.max_attempts = 10

        self.progress["value"] = 0

        self.result_label.config(text="")
        self.entry.delete(0, tk.END)

        self.info_label.config(
            text=f"請猜 1 ~ {self.max_num}"
        )

        self.update_stats()

    def update_stats(self):

        best = "-" if self.best_score is None else str(self.best_score)

        self.stats_label.config(
            text=(
                f"剩餘機會：{self.max_attempts-self.attempts}   "
                f"最佳紀錄：{best} 次"
            )
        )

    def check(self):

        try:
            guess = int(self.entry.get())

        except ValueError:
            messagebox.showwarning("錯誤", "請輸入數字")
            return

        self.attempts += 1
        self.progress["value"] = self.attempts

        if guess < self.answer:
            self.result_label.config(text="⬆ 太小了")
        elif guess > self.answer:
            self.result_label.config(text="⬇ 太大了")
        else:

            if self.best_score is None:
                self.best_score = self.attempts
            else:
                self.best_score = min(
                    self.best_score,
                    self.attempts
                )

            messagebox.showinfo(
                "恭喜",
                f"🎉 猜中了！\n\n答案：{self.answer}\n使用 {self.attempts} 次"
            )

            self.start_game()
            return

        if self.attempts >= self.max_attempts:
            messagebox.showerror(
                "遊戲結束",
                f"😢 沒有機會了\n正確答案是：{self.answer}"
            )
            self.start_game()
            return

        self.update_stats()
        self.entry.delete(0, tk.END)


root = tk.Tk()
app = GuessNumberPro(root)
root.mainloop()
