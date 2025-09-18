# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import random
from PIL import Image, ImageTk # PIL (Pillow) ライブラリを使用

class SeatingChartApp:
    """
    高機能な席替え抽選アプリケーション
    """
    def __init__(self, root):
        self.root = root
        self.root.title("高機能席替えアプリ Ver. 2.0")
        self.root.geometry("1280x800")
        self.root.resizable(False, False) # ウィンドウサイズ固定

        # データ保持用の変数
        self.students = []
        self.desks = {} # {seat_num: desk_widget_info}
        self.fixed_assignments = {} # {seat_num: student_name}

        # 背景画像の設定
        self.bg_image = self._load_background_image("bb.png")
        self.bg_label = tk.Label(root, image=self.bg_image)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # UIの初期化
        self._setup_ui()

    def _load_background_image(self, path):
        """背景画像を読み込み、ウィンドウサイズに合わせてリサイズする"""
        try:
            original_image = Image.open(path)
            # ウィンドウサイズに合わせてリサイズ
            resized_image = original_image.resize((1280, 800), Image.LANCZOS)
            return ImageTk.PhotoImage(resized_image)
        except Exception as e:
            messagebox.showerror("画像エラー", f"背景画像の読み込みに失敗しました: {e}\n画像なしで続行します。")
            return None

    def _setup_ui(self):
        """UIの骨格を作成する"""
        # --- メインフレーム (背景画像の上に配置) ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # --- コントロールパネル (左側) ---
        # 半透明の背景を持つCanvasを使用
        control_canvas = tk.Canvas(main_frame, bg="gray", highlightthickness=0)
        control_canvas.create_rectangle(0, 0, 250, 780, fill="#FFFFFF", stipple="gray25", outline="") # 半透明効果
        
        # ▼▼▼ ここの行を修正 ▼▼▼
        control_panel = ttk.LabelFrame(control_canvas, text="コントロールパネル", padding="10")
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        
        control_panel.place(x=0, y=0, width=250, height=780) # Canvas内に配置

        # ファイル読み込みフレーム
        file_frame = ttk.Frame(control_panel)
        file_frame.pack(fill=tk.X, pady=10)
        ttk.Button(file_frame, text="① 生徒名簿(CSV)を読込", command=self.load_students).pack(fill=tk.X, ipady=5)
        ttk.Button(file_frame, text="② 座席レイアウトを読込", command=self.load_layout).pack(fill=tk.X, pady=5, ipady=5)

        # 固定席設定フレーム
        fix_frame = ttk.LabelFrame(control_panel, text="固定席の設定", padding="10")
        fix_frame.pack(fill=tk.X, pady=15)

        ttk.Label(fix_frame, text="生徒:", font=("Meiryo UI", 10)).pack(anchor=tk.W, pady=(5,0))
        self.student_combobox = ttk.Combobox(fix_frame, state="readonly", font=("Meiryo UI", 10))
        self.student_combobox.pack(fill=tk.X)

        ttk.Label(fix_frame, text="座席番号:", font=("Meiryo UI", 10)).pack(anchor=tk.W, pady=(10,0))
        self.seat_combobox = ttk.Combobox(fix_frame, state="readonly", font=("Meiryo UI", 10))
        self.seat_combobox.pack(fill=tk.X)
        
        ttk.Button(fix_frame, text="席を固定する", command=self.fix_seat, style="TButton").pack(pady=15, ipady=5)

        # 実行フレーム
        action_frame = ttk.Frame(control_panel)
        action_frame.pack(fill=tk.X, pady=20)
        ttk.Button(action_frame, text="③ 抽選開始！", command=self.perform_random_assignment, style="Accent.TButton").pack(fill=tk.X, ipady=15)
        
        # リセット・エクスポートフレーム
        util_frame = ttk.Frame(control_panel)
        util_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Button(util_frame, text="リセット", command=self.reset, style="TButton").pack(fill=tk.X, ipady=5)
        ttk.Button(util_frame, text="結果をCSVにエクスポート", command=self.export_to_csv, style="TButton").pack(fill=tk.X, pady=5, ipady=5)
        
        # --- 座席表示エリア (右側) ---
        self.desk_area = ttk.Frame(main_frame)
        self.desk_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(270, 20), pady=20) # コントロールパネルの幅を考慮

        self.desk_canvas = tk.Frame(self.desk_area, bg="") # 机を配置するフレーム
        self.desk_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        

        # --- ステータスバー ---
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN, font=("Meiryo UI", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # --- スタイルの設定 ---
        style = ttk.Style()
        style.theme_use('clam') # モダンなテーマを使用

        # フォント設定
        default_font = ("Meiryo UI", 10)
        style.configure("TLabel", font=default_font)
        style.configure("TButton", font=default_font)
        style.configure("TEntry", font=default_font)
        style.configure("TCombobox", font=default_font)
        style.configure("TLabelFrame", font=("Meiryo UI", 11, "bold"))
        style.configure("TLabelFrame.Label", font=("Meiryo UI", 11, "bold"))


        # Accentボタン (抽選開始)
        style.configure("Accent.TButton", 
                        font=("Meiryo UI", 14, "bold"), 
                        background="#4CAF50", # 緑系
                        foreground="white",
                        relief="raised",
                        padding=10)
        style.map("Accent.TButton", 
                  background=[("active", "#66BB6A")]) # ホバー時の色

        # コントロールパネルの背景色をCanvasで実現しているため、LabelFrameの背景はデフォルトのまま

    def _create_desk_widget(self, parent, seat_num):
        """個々の机ウィジェットを作成するヘルパー関数"""
        # 角丸のCanvasで机を描画
        desk_canvas = tk.Canvas(parent, width=120, height=80, bg="#8B4513", highlightthickness=0) # 木目調の茶色
        # 長方形の角を丸くする処理 (Tkinterでは直接できないため、擬似的に)
        desk_canvas.create_oval(0, 0, 10, 10, fill="#8B4513", outline="#8B4513")
        desk_canvas.create_oval(110, 0, 120, 10, fill="#8B4513", outline="#8B4513")
        desk_canvas.create_oval(0, 70, 10, 80, fill="#8B4513", outline="#8B4513")
        desk_canvas.create_oval(110, 70, 120, 80, fill="#8B4513", outline="#8B4513")
        desk_canvas.create_rectangle(5, 0, 115, 80, fill="#8B4513", outline="")
        desk_canvas.create_rectangle(0, 5, 120, 75, fill="#8B4513", outline="")


        # 座席番号
        desk_canvas.create_text(10, 10, text=str(seat_num), anchor=tk.NW, fill="white", font=("Meiryo UI", 12, "bold"))
        
        # 名前表示用のテキスト (Canvas内に作成)
        name_text_id = desk_canvas.create_text(60, 45, text="", fill="white", font=("Meiryo UI", 16, "bold"), justify=tk.CENTER)
        
        return desk_canvas, name_text_id


    def load_students(self):
        """CSVファイルから生徒名簿を読み込む"""
        filepath = filedialog.askopenfilename(
            title="生徒名簿(CSV)ファイルを選択",
            filetypes=[("CSVファイル", "*.csv")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                next(reader, None)  # ヘッダー行を読み飛ばす
                
                self.students = [{"id": row[0], "name": row[1]} for row in reader]
            
            self.update_comboboxes()
            self.status_var.set(f"{len(self.students)}名の生徒を読み込みました。")
            messagebox.showinfo("成功", f"{len(self.students)}名の生徒情報を読み込みました。")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの読み込みに失敗しました:\n{e}")
            self.status_var.set("エラー: 生徒名簿を読み込めませんでした。")

    def load_layout(self):
        """テキストファイルから座席レイアウトを読み込み、描画する"""
        filepath = filedialog.askopenfilename(
            title="座席レイアウトファイルを選択",
            filetypes=[("テキストファイル", "*.txt")]
        )
        if not filepath:
            return

        # 既存の机をクリア
        for widget in self.desk_canvas.winfo_children():
            widget.destroy()
        self.desks = {}
        self.fixed_assignments = {} # レイアウト変更時は固定席もリセット

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                layout_lines = f.readlines()

            seat_num = 1
            for row, line in enumerate(layout_lines):
                for col, char in enumerate(line.strip()): # strip()で改行文字を除去
                    if char.upper() == 'D':
                        desk_widget, name_text_id = self._create_desk_widget(self.desk_canvas, seat_num)
                        desk_widget.grid(row=row, column=col, padx=8, pady=8) # パディングを調整
                        self.desks[seat_num] = {"widget": desk_widget, "name_text_id": name_text_id}
                        seat_num += 1
            
            self.update_comboboxes()
            self.status_var.set(f"{len(self.desks)}席のレイアウトを読み込みました。")
            messagebox.showinfo("成功", f"{len(self.desks)}席のレイアウトを読み込みました。")
        except Exception as e:
            messagebox.showerror("エラー", f"レイアウトの読み込みに失敗しました:\n{e}")
            self.status_var.set("エラー: レイアウトファイルを読み込めませんでした。")
            
    def update_comboboxes(self):
        """固定席設定用のコンボボックスを更新する"""
        # 生徒リスト
        assigned_students = list(self.fixed_assignments.values())
        unassigned_students = [s["name"] for s in self.students if s["name"] not in assigned_students]
        self.student_combobox["values"] = sorted(unassigned_students)
        
        # 座席リスト
        assigned_seats = list(self.fixed_assignments.keys())
        unassigned_seats = [num for num in self.desks.keys() if num not in assigned_seats]
        self.seat_combobox["values"] = sorted(unassigned_seats)

    def fix_seat(self):
        """選択された生徒と座席を固定する"""
        student_name = self.student_combobox.get()
        seat_num_str = self.seat_combobox.get()

        if not student_name or not seat_num_str:
            messagebox.showwarning("入力エラー", "生徒と座席番号の両方を選択してください。")
            return
        
        seat_num = int(seat_num_str)
        
        # 画面に表示 (Canvasのテキストアイテムを更新)
        desk_info = self.desks[seat_num]
        desk_info["widget"].itemconfig(desk_info["name_text_id"], text=student_name, fill="yellow") # 固定席は黄色に

        # 固定リストに追加
        self.fixed_assignments[seat_num] = student_name
        
        self.status_var.set(f"{student_name}さんを{seat_num}番の席に固定しました。")
        self.student_combobox.set('')
        self.seat_combobox.set('')
        self.update_comboboxes()

    def perform_random_assignment(self):
        """ランダムな席替えを実行する"""
        # 未割り当ての生徒と席を取得
        assigned_student_names = list(self.fixed_assignments.values())
        unassigned_students = [s["name"] for s in self.students if s["name"] not in assigned_student_names]
        
        assigned_seat_nums = list(self.fixed_assignments.keys())
        unassigned_seats = [num for num in self.desks.keys() if num not in assigned_seat_nums]

        if len(unassigned_students) != len(unassigned_seats):
            messagebox.showerror("エラー", f"生徒数({len(unassigned_students)})と空席数({len(unassigned_seats)})が一致しません。\n固定席を確認してください。")
            return
            
        if not unassigned_students and len(self.students) > 0: # 生徒がいて全員固定されている場合
            messagebox.showinfo("情報", "すべての席が割り当て済みです。")
            return
        elif not self.students: # 生徒が一人も読み込まれていない場合
             messagebox.showwarning("警告", "生徒名簿が読み込まれていません。")
             return
        elif not self.desks: # レイアウトが読み込まれていない場合
             messagebox.showwarning("警告", "座席レイアウトが読み込まれていません。")
             return

        # 抽選
        random.shuffle(unassigned_students)
        
        # 席の割り当てと表示
        for seat_num, student_name in zip(unassigned_seats, unassigned_students):
            desk_info = self.desks[seat_num]
            desk_info["widget"].itemconfig(desk_info["name_text_id"], text=student_name, fill="white") # 抽選結果は白色に
            
        self.status_var.set("抽選が完了しました！")
        messagebox.showinfo("完了", "席替えが完了しました！")

    def reset(self):
        """すべての設定と結果をリセットする"""
        if not messagebox.askyesno("確認", "すべての割り当てをリセットしますか？"):
            return
            
        self.fixed_assignments = {}
        for seat_num, desk_info in self.desks.items():
            desk_info["widget"].itemconfig(desk_info["name_text_id"], text="", fill="white") # テキストをクリア
        
        self.update_comboboxes()
        self.status_var.set("リセットしました。")

    def export_to_csv(self):
        """現在の座席表をCSVファイルにエクスポートする"""
        filepath = filedialog.asksaveasfilename(
            title="結果を保存",
            defaultextension=".csv",
            filetypes=[("CSVファイル", "*.csv")]
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["SeatNumber", "StudentID", "Name"])
                
                # 生徒の名前からIDを逆引きするための辞書を作成
                student_id_map = {s["name"]: s["id"] for s in self.students}

                # 席番号順にソートして書き出し
                for seat_num in sorted(self.desks.keys()):
                    # Canvasのテキストアイテムから名前を取得
                    name = self.desks[seat_num]["widget"].itemcget(self.desks[seat_num]["name_text_id"], "text")
                    student_id = student_id_map.get(name, "") # 名簿にない名前はIDを空にする
                    writer.writerow([seat_num, student_id, name])
            
            self.status_var.set(f"結果を{filepath}にエクスポートしました。")
            messagebox.showinfo("成功", "CSVファイルとしてエクスポートしました。")
        except Exception as e:
            messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SeatingChartApp(root)
    root.mainloop()