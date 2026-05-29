import random

# 產生 1~100 的隨機數字
answer = random.randint(1, 100)

print("=== 猜數字遊戲 ===")
print("請猜一個 1~100 的數字")

count = 0

while True:
    try:
        guess = int(input("請輸入數字："))
        count += 1

        if guess < answer:
            print("太小了！")
        elif guess > answer:
            print("太大了！")
        else:
            print(f"恭喜答對！答案是 {answer}")
            print(f"總共猜了 {count} 次")
            break

    except ValueError:
        print("請輸入有效的整數！")
