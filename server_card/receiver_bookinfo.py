import sys
import io

# ---------------------------------------------------------
# --noconsole 빌드 시 stdout/stderr가 None이 되는 현상 방지
# ---------------------------------------------------------
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import asyncio
import csv  # 파이썬 표준 내장 csv 모듈 사용
from datetime import datetime
hashlib = __import__('hashlib')
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# FastAPI 애플리케이션 및 Pydantic 데이터 모델 정의
# ---------------------------------------------------------
app = FastAPI(title="Card Payment Receiver Server")

class PaymentRequest(BaseModel):
    user_id: str = Field(..., max_length=150, description="유저 ID")
    price: int = Field(..., ge=0, description="결제 금액 (0 이상)")
    reservation_date : str = Field(..., max_length=75, description="결제 완료시간")

def generate_encrypted_approval_code(user_id: str) -> str:
    """고유 난수(UUID) + 유저 ID를 조합하여 SHA-256 암호화된 승인번호 생성"""
    raw_unique_str = f"{uuid.uuid4()}_{user_id}_{time.time()}"
    encrypted_hash = hashlib.sha256(raw_unique_str.encode('utf-8')).hexdigest()
    return f"CARD_{encrypted_hash[:16].upper()}"

# GUI 객체 접근용 전역 참조 변수
gui_app_ref = None

@app.post("/api/v1/payment")
async def process_payment(payment_data: PaymentRequest):
    log_msg = f"[카드 결제 요청] User ID: {payment_data.user_id}, 금액: {payment_data.price}원, 결재 시간: {payment_data.reservation_date}"
    
    if gui_app_ref:
        gui_app_ref.append_log(f"{log_msg}\n")

    if payment_data.price < 0:
        err_msg = "[결제 승인 거절] 유효하지 않은 금액 (0원 미만)"
        if gui_app_ref:
            gui_app_ref.append_log(f" └─> ❌ {err_msg}\n")
        raise HTTPException(status_code=400, detail="유효하지 않은 금액입니다.")

    # 암호화된 승인번호 생성
    approval_code = generate_encrypted_approval_code(payment_data.user_id)
    
    # GUI 메모리 리스트에 승인 내역 기록 (csv 저장용)
    if gui_app_ref:
        gui_app_ref.add_payment_record(
            user_id=payment_data.user_id,
            price=payment_data.price,
            reservation_date=payment_data.reservation_date,
            approval_code=approval_code
        )
        success_msg = f" └─> 승인 완료 | 승인번호: {approval_code}"
        gui_app_ref.append_log(f"{success_msg}\n\n")

    return {
        "status": "APPROVED",
        "user_id": payment_data.user_id,
        "price": payment_data.price,
        "payment_date": payment_data.reservation_date,
        "approval_code": approval_code
    }


# ---------------------------------------------------------
# 실행 디렉터리 경로 반환 함수 (PyInstaller exe 대응)
# ---------------------------------------------------------
def get_executable_dir():
    """exe 파일 빌드 환경과 일반 python 스크립트 실행 환경 모두에서 실제 실행 위치 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 .exe 실행 환경
        return os.path.dirname(sys.executable)
    else:
        # 일반 .py 스크립트 실행 환경
        return os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------
# Tkinter GUI Dialog 및 Uvicorn 서버 스레드 제어
# ---------------------------------------------------------
class PaymentReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("카드 결제 수신 서버 Dialog (FastAPI)")
        self.root.geometry("680x420")
        self.root.minsize(580, 350)

        self.server_thread = None
        self.uvicorn_server = None
        self.loop = None
        self.is_running = False

        # 자동 저장 타이머 핸들 및 시간 설정 변수
        self.auto_save_timer_id = None
        self.auto_save_hours = 0

        # 승인된 결제 데이터를 담아둘 메모리 리스트
        self.payment_records = []
        # 가장 최근에 저장된 내역 스냅샷 (중복 저장 방지용)
        self.last_saved_records = []

        # 1. 상단 포트, 상태 표시 및 자동 저장 타이머 영역
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(top_frame, text="포트 번호:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_entry = tk.Entry(top_frame, width=6)
        self.port_entry.insert(0, "8000")
        self.port_entry.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = tk.Label(top_frame, text="서버 상태: 정지됨", fg="red")
        self.status_label.pack(side=tk.LEFT, padx=(0, 15))

        # --- 자동 저장 타이머 콤보박스 ---
        tk.Label(top_frame, text="자동 저장:").pack(side=tk.LEFT, padx=(0, 5))
        self.timer_combobox = ttk.Combobox(
            top_frame,
            values=["0시간", "1시간", "2시간", "3시간", "12시간", "24시간"],
            width=8,
            state="readonly"
        )
        self.timer_combobox.current(0)  # 기본값 "0시간"
        self.timer_combobox.pack(side=tk.LEFT)
        self.timer_combobox.bind("<<ComboboxSelected>>", self.on_timer_changed)

        # 2. 로그 출력 스크롤 텍스트 영역
        log_frame = tk.Frame(root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_display = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_display.pack(fill=tk.BOTH, expand=True)
        self.log_display.configure(state="disabled")

        # 3. 하단 컨트롤 버튼 영역
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)

        self.start_button = tk.Button(
            btn_frame, text="Server Start", command=self.start_server, height=1
        )
        self.start_button.grid(row=0, column=0, padx=2, sticky="ew")

        self.stop_button = tk.Button(
            btn_frame,
            text="Server Stop",
            command=self.stop_server,
            state=tk.DISABLED,
            height=1,
        )
        self.stop_button.grid(row=0, column=1, padx=2, sticky="ew")

        self.clear_button = tk.Button(
            btn_frame, text="Clear Log", command=self.clear_log, height=1
        )
        self.clear_button.grid(row=0, column=2, padx=2, sticky="ew")

        self.export_button = tk.Button(
            btn_frame,
            text="Export CSV",
            command=self.export_to_csv,
            fg="blue",
            height=1,
        )
        self.export_button.grid(row=0, column=3, padx=2, sticky="ew")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_payment_record(self, user_id: str, price: int, reservation_date: str, approval_code: str):
        """승인된 결제 정보를 메모리 리스트에 수집"""
        self.payment_records.append({
            "유저": user_id,
            "금액": price,
            "승인시각": reservation_date,
            "승인번호": approval_code
        })

    # ---------------------------------------------------------
    # 자동 CSV 저장 및 타이머 제어
    # ---------------------------------------------------------
    def on_timer_changed(self, event=None):
        """콤보박스 변경 이벤트 처리"""
        selected_text = self.timer_combobox.get()
        hours = int(selected_text.replace("시간", ""))
        self.auto_save_hours = hours

        # 기존 작동 중인 타이머 취소
        if self.auto_save_timer_id:
            self.root.after_cancel(self.auto_save_timer_id)
            self.auto_save_timer_id = None

        if hours > 0:
            self.append_log(f"[시스템] 자동 CSV 저장 타이머 설정됨: {hours}시간 주기\n\n")
            self.schedule_auto_save()
        else:
            self.append_log("[시스템] 자동 CSV 저장 타이머 중지됨 (0시간)\n\n")

    def schedule_auto_save(self):
        """선택한 시간(ms) 이후에 auto_save_csv 함수를 호출하도록 예약"""
        if self.auto_save_hours > 0:
            interval_ms = self.auto_save_hours * 3600 * 1000  # 시간 -> 밀리초 변환
            self.auto_save_timer_id = self.root.after(interval_ms, self.auto_save_csv)

    def auto_save_csv(self):
        """타이머 동작 시 자동 실행되는 CSV 저장 로직"""
        # 저장할 내역이 없는 경우
        if not self.payment_records:
            self.append_log("[자동 저장] 저장할 결제 내역이 없어 자동 저장을 건너뜁니다.\n\n")
            self.schedule_auto_save()
            return

        # 최근에 저장한 내역과 변경사항이 없는 경우 (중복 저장 방지)
        if self.payment_records == self.last_saved_records:
            self.append_log("[자동 저장] 이전 저장 이후 추가된 결제 내역이 없어 저장을 건너뜁니다.\n\n")
            self.schedule_auto_save()
            return

        try:
            now = datetime.now()
            # 1. 실제 exe 실행 파일 위치 추출 (AppData Temp 방지)
            base_dir = get_executable_dir()
            
            # 2. 오늘 날짜 폴더 생성 (YYYY-MM-DD)
            today_folder_name = now.strftime("%Y-%m-%d")
            target_dir = os.path.join(base_dir, today_folder_name)
            os.makedirs(target_dir, exist_ok=True)

            # 3. CSV 파일명 (HH-MM-SS.csv)
            file_name = now.strftime("%H-%M-%S.csv")
            full_path = os.path.join(target_dir, file_name)

            # 4. 파일 저장
            with open(full_path, mode="w", newline="", encoding="utf-8-sig") as f:
                fieldnames = ["유저", "금액", "승인시각", "승인번호"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.payment_records)

            # 5. 최근 저장 내역 상태 갱신 (얕은 복사로 스냅샷 저장)
            self.last_saved_records = list(self.payment_records)

            self.append_log(f"[자동 저장 완료] CSV 파일이 저장되었습니다:\n └─> {full_path}\n\n")

        except Exception as e:
            self.append_log(f"[자동 저장 오류] 파일 저장 중 오류 발생: {e}\n\n")

        # 저장 완료 후 다음 주기 타이머 예약
        self.schedule_auto_save()

    def export_to_csv(self):
        """기존 수동 Export CSV 버튼"""
        if not self.payment_records:
            messagebox.showwarning("알림", "저장할 결제 내역이 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="결제 내역 CSV 저장"
        )

        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    fieldnames = ["유저", "금액", "승인시각", "승인번호"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.payment_records)

                # 수동 저장 시에도 최근 저장 상태 업데이트
                self.last_saved_records = list(self.payment_records)

                messagebox.showinfo("성공", f"CSV 파일 저장 완료:\n{file_path}")
                self.append_log(f"[시스템] CSV 내역 수동 저장 완료: {file_path}\n\n")
            except Exception as e:
                messagebox.showerror("저장 오류", f"CSV 저장 중 오류 발생:\n{e}")

    def append_log(self, message: str):
        """Thread-safe UI 로그 출력"""
        def _update():
            self.log_display.configure(state='normal')
            self.log_display.insert(tk.END, message)
            self.log_display.see(tk.END)
            self.log_display.configure(state='disabled')
        self.root.after(0, _update)

    def clear_log(self):
        self.log_display.configure(state='normal')
        self.log_display.delete('1.0', tk.END)
        self.log_display.configure(state='disabled')

    def _run_uvicorn_server(self, port: int):
        """백그라운드 스레드 전용 asyncio 루프 생성 및 Uvicorn 구동"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=port,
                log_config=None,
                loop="asyncio"
            )
            self.uvicorn_server = uvicorn.Server(config)
            self.loop.run_until_complete(self.uvicorn_server.serve())
        except Exception as e:
            self.append_log(f"[서버 오류 발생] {e}\n")

    def start_server(self):
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("오류", "유효한 포트 번호를 입력하세요.")
            return

        self.server_thread = threading.Thread(
            target=self._run_uvicorn_server, 
            args=(port,), 
            daemon=True
        )
        self.server_thread.start()

        self.is_running = True
        self.status_label.config(text=f"서버 상태: 실행 중 ({port}번 포트)", fg="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.DISABLED)
        self.append_log(f"[시스템] 카드 결제 수신 서버 시작 완료 (0.0.0.0:{port})\n\n")

    def stop_server(self):
        if self.uvicorn_server and self.is_running:
            self.uvicorn_server.should_exit = True
            self.is_running = False

        self.status_label.config(text="서버 상태: 정지됨", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)
        self.append_log("[시스템] 카드 결제 수신 서버 정지됨\n\n")

    def on_closing(self):
        if self.auto_save_timer_id:
            self.root.after_cancel(self.auto_save_timer_id)
        if self.is_running:
            self.stop_server()
        self.root.destroy()

# ---------------------------------------------------------
# 진입점
# ---------------------------------------------------------
def main():
    global gui_app_ref
    root = tk.Tk()
    app_gui = PaymentReceiverGUI(root)
    gui_app_ref = app_gui
    root.mainloop()

if __name__ == "__main__":
    main()