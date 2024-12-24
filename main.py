import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
import requests
from bs4 import BeautifulSoup
import datetime
import webbrowser  # 사이트 방문용

# ---------------------------
# 전역 변수(사용자 입력)
# ---------------------------
favorite_foods = []  # 좋아하는 음식 목록
allergies = []       # 알레르기 번호 목록 (문자열 형태)

# 알레르기 번호별 식재료 매핑
ALLERGY_DICT = {
    '1': '난류',
    '2': '우유',
    '3': '메밀',
    '4': '땅콩',
    '5': '대두',
    '6': '밀',
    '7': '고등어',
    '8': '게',
    '9': '새우',
    '10': '돼지고기',
    '11': '복숭아',
    '12': '토마토',
    '13': '아황산류',
    '14': '호두',
    '15': '닭고기',
    '16': '쇠고기',
    '17': '오징어',
    '18': '조개류(굴,전복,홍합)',
    '19': '잣'
}

# 검색 결과(음식 찾기)
searchResults = []
searchIndex = -1

def ask_user_preferences():
    """프로그램 시작 시, 좋아하는 음식 + 알레르기 번호 입력받기."""
    foods_input = simpledialog.askstring(
        "좋아하는 음식", 
        ("좋아하는 음식을 여러 개 입력하세요.\n"
         "쉼표(,)나 줄바꿈으로 구분.\n"
         "예) 귤, 마카롱, 핫초코")
    )
    if foods_input:
        lines = foods_input.replace(',', '\n').split('\n')
        global favorite_foods
        favorite_foods = [ln.strip() for ln in lines if ln.strip()]
    
    allergy_text = (
        "[알레르기 정보]\n"
        "1=난류, 2=우유, 3=메밀, 4=땅콩, 5=대두, 6=밀, 7=고등어,\n"
        "8=게, 9=새우, 10=돼지고기, 11=복숭아, 12=토마토, 13=아황산류,\n"
        "14=호두, 15=닭고기, 16=쇠고기, 17=오징어, 18=조개류, 19=잣\n\n"
        "알레르기 번호(예: 1,5,10)를 공백/쉼표로 구분."
    )
    allergies_input = simpledialog.askstring("알레르기 정보 입력", allergy_text)
    if allergies_input:
        arr = allergies_input.replace(',', ' ').split()
        global allergies
        allergies = [x.strip() for x in arr if x.strip().isdigit() and 1 <= int(x.strip()) <= 19]

def get_meal_info(date_str):
    """
    사이트의 <p> 태그에서 줄바꿈이 이미 되어있다면 그대로 가져옴.
    """
    try:
        url = "https://school.gyo6.net/gokok-hs/ad/fm/foodmenu/selectFoodMenuView.do"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        # ex) "2024.12.02" -> "20241202"
        td_id = date_str.replace('.', '')

        day_td = soup.find("td", id=td_id)
        if not day_td:
            return "급식 정보가 없습니다."

        meal_paragraphs = day_td.find_all("p")
        if not meal_paragraphs:
            return "급식 정보가 없습니다."

        # 줄바꿈을 보존하려면 get_text()에 separator="\n" 인자를 준다.
        # <p>별로 데이터를 가져와 합침
        meal_lines = []
        for p in meal_paragraphs:
            # HTML 안의 <br> 등 줄바꿈을 \n로 치환
            # strip=False로 해야 원본 줄바꿈을 그대로 가져올 가능성이 높음
            text_in_p = p.get_text("\n", strip=False)
            text_in_p = text_in_p.strip('\n')  # 앞뒤 불필요한 \n 제거
            if text_in_p:
                meal_lines.append(text_in_p)

        if not meal_lines:
            return "급식 정보가 없습니다."

        # <p> 마다 하나의 블록으로 보고, \n로 연결
        # 이렇게 하면 <p> 단위가 줄간격 역할
        meal_info = "\n".join(meal_lines)
        
        return meal_info

    except requests.exceptions.RequestException as e:
        return f"오류 발생: {e}"

def display_meal(date_str):
    """
    1) 급식을 줄 단위로 읽어 Text에 삽입
    2) 좋아하는 음식 → 볼드, 알레르기 → 붉은색
    """
    meal_data = get_meal_info(date_str)
    text_meal.delete("1.0", tk.END)

    # 라인별 처리
    lines = meal_data.split('\n')

    found_foods = set()
    found_allergies = set()

    for line in lines:
        # 태그 선택
        line_tags = []
        
        # (A) 좋아하는 음식
        fav_found = False
        for f in favorite_foods:
            if f in line:
                fav_found = True
                found_foods.add(f)
        if fav_found:
            line_tags.append("favorite")

        # (B) 알레르기
        allergy_found = False
        for num in allergies:
            if num in line:
                allergy_found = True
                found_allergies.add(num)
        if allergy_found:
            line_tags.append("allergy")

        # 넣기
        text_meal.insert("end", line.rstrip('\r') + "\n", tuple(line_tags))

    # (C) 메시지
    # 좋아하는 음식 알림
    for f in found_foods:
        messagebox.showinfo("좋아하는 음식 알림", f"{f}이(가) 나오는 날입니다!")

    # 알레르기 (한 번만)
    if found_allergies:
        sorted_nums = sorted(found_allergies, key=lambda x: int(x))
        details = []
        for num in sorted_nums:
            allergen_name = ALLERGY_DICT.get(num, "???")
            details.append(f"{num}번({allergen_name})")
        joined_str = ", ".join(details)
        messagebox.showwarning(
            "알레르기 주의",
            f"{joined_str} 이(가) 포함된 음식이 있습니다!"
        )

def on_search():
    global searchIndex, searchResults
    searchIndex = -1
    searchResults = []
    
    date_str = entry_date.get().strip()
    if not date_str:
        messagebox.showerror("오류", "날짜를 입력하세요")
        return
    display_meal(date_str)

def on_prev_day():
    global searchIndex
    if searchIndex >= 0 and searchIndex < len(searchResults):
        # 검색 모드
        if searchIndex > 0:
            searchIndex -= 1
            ds = searchResults[searchIndex]
            entry_date.delete(0, tk.END)
            entry_date.insert(0, ds)
            display_meal(ds)
        else:
            messagebox.showinfo("검색", "이전 검색 결과가 없습니다.")
    else:
        date_str = entry_date.get().strip()
        if not date_str:
            messagebox.showerror("오류", "날짜를 입력하세요")
            return
        try:
            current_date = datetime.datetime.strptime(date_str, "%Y.%m.%d")
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 잘못됨")
            return
        new_date = (current_date - datetime.timedelta(days=1)).strftime("%Y.%m.%d")
        entry_date.delete(0, tk.END)
        entry_date.insert(0, new_date)
        display_meal(new_date)

def on_next_day():
    global searchIndex
    if searchIndex >= 0 and searchIndex < len(searchResults):
        # 검색 모드
        if searchIndex < len(searchResults) - 1:
            searchIndex += 1
            ds = searchResults[searchIndex]
            entry_date.delete(0, tk.END)
            entry_date.insert(0, ds)
            display_meal(ds)
        else:
            messagebox.showinfo("검색", "다음 검색 결과가 없습니다.")
    else:
        date_str = entry_date.get().strip()
        if not date_str:
            messagebox.showerror("오류", "날짜를 입력하세요")
            return
        try:
            current_date = datetime.datetime.strptime(date_str, "%Y.%m.%d")
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 잘못됨")
            return
        new_date = (current_date + datetime.timedelta(days=1)).strftime("%Y.%m.%d")
        entry_date.delete(0, tk.END)
        entry_date.insert(0, new_date)
        display_meal(new_date)

def on_food_search():
    """현재 날짜부터 20일간만 검색."""
    global searchResults, searchIndex
    item = simpledialog.askstring("음식 검색", "찾고 싶은 음식 이름을 입력하세요:")
    if not item:
        return

    searchResults = []
    searchIndex = -1

    base_str = entry_date.get().strip()
    if not base_str:
        base_str = datetime.date.today().strftime("%Y.%m.%d")
    try:
        base_date = datetime.datetime.strptime(base_str, "%Y.%m.%d").date()
    except ValueError:
        base_date = datetime.date.today()

    end_date = base_date + datetime.timedelta(days=20)
    cur_date = base_date
    while cur_date <= end_date:
        ds = cur_date.strftime("%Y.%m.%d")
        meal_data = get_meal_info(ds)
        if item in meal_data:
            searchResults.append(ds)
        cur_date += datetime.timedelta(days=1)

    if len(searchResults) == 0:
        messagebox.showinfo("검색 결과", f"'{item}'을(를) 포함한 급식을 찾지 못했습니다.\n(20일 이내 범위)")
    else:
        messagebox.showinfo("검색 결과", f"'{item}'이(가) 포함된 날짜 {len(searchResults)}건 발견.\n가장 빠른 날짜로 이동합니다.")
        searchIndex = 0
        first_date = searchResults[0]
        entry_date.delete(0, tk.END)
        entry_date.insert(0, first_date)
        display_meal(first_date)

def on_enter_key(event):
    on_search()

def visit_site():
    """급식 사이트 방문 버튼 콜백."""
    webbrowser.open("https://school.gyo6.net/gokok-hs/ad/fm/foodmenu/selectFoodMenuView.do")

# ------------------------------
# tkinter GUI
# ------------------------------
root = tk.Tk()
root.title("경주여자고등학교 급식 조회")

try:
    root.iconbitmap("orange.ico")
except:
    pass

# 윈도우 정중앙 배치
root.update_idletasks()
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
ww, wh = 600, 450  # 윈도우 크기
x = (sw - ww) // 2
y = (sh - wh) // 2
root.geometry(f"{ww}x{wh}+{x}+{y}")

root.configure(bg="#FFC0CB")

# ttk 스타일
style = ttk.Style(root)
style.theme_use("clam")

style.configure("Rounded.TButton",
    padding=6,
    relief="flat",
    background="#FFC0CB",
    foreground="black"
)
style.configure("Custom.TEntry",
    fieldbackground="#FFFFFF",
    borderwidth=0,
    padding=5
)

ask_user_preferences()

main_frame = tk.Frame(root, bg="#FFC0CB")
main_frame.pack(expand=True, fill="both")

top_frame = tk.Frame(main_frame, bg="#FFC0CB")
top_frame.pack(pady=10)

btn_prev = ttk.Button(top_frame, text="<", command=on_prev_day, style="Rounded.TButton")
btn_prev.pack(side="left", padx=5)

label_info = tk.Label(
    top_frame, text="날짜(YYYY.MM.DD):",
    font=("맑은 고딕", 12), bg="#FFC0CB"
)
label_info.pack(side="left", padx=5)

entry_date = ttk.Entry(top_frame, font=("맑은 고딕", 12), width=15, style="Custom.TEntry")
entry_date.pack(side="left", padx=5)
entry_date.bind("<Return>", on_enter_key)

btn_next = ttk.Button(top_frame, text=">", command=on_next_day, style="Rounded.TButton")
btn_next.pack(side="left", padx=5)

today_str = datetime.date.today().strftime("%Y.%m.%d")
entry_date.delete(0, tk.END)
entry_date.insert(0, today_str)

bottom_frame = tk.Frame(main_frame, bg="#FFC0CB")
bottom_frame.pack(pady=10)

btn_search = ttk.Button(bottom_frame, text="조회", command=on_search, style="Rounded.TButton")
btn_search.pack(side="left", padx=10)

btn_food_search = ttk.Button(bottom_frame, text="음식 검색", command=on_food_search, style="Rounded.TButton")
btn_food_search.pack(side="left", padx=10)

text_meal = tk.Text(
    main_frame, width=70, height=12, font=("맑은 고딕", 12),
    bg="#FFDCE5", bd=0, highlightthickness=0, relief="flat"
)
text_meal.pack(pady=5, expand=True)

# 태그
text_meal.tag_configure("favorite", font=("맑은 고딕", 12, "bold"))
text_meal.tag_configure("allergy", foreground="#BB2222")

# 하단에 '급식사이트 방문' 버튼
visit_frame = tk.Frame(main_frame, bg="#FFC0CB")
visit_frame.pack(side="bottom", fill="x", pady=5)

btn_visit = ttk.Button(visit_frame, text="급식사이트 방문", command=visit_site, style="Rounded.TButton")
btn_visit.pack(side="left", padx=10)

# 오른쪽 아래 작게 '20231510이효정'
label_signature = tk.Label(
    visit_frame, text="20231510이효정",
    font=("맑은 고딕", 8), bg="#FFC0CB"
)
label_signature.pack(side="right", padx=5)

root.mainloop()
