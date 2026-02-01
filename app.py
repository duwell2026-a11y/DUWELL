import streamlit as st
import google.generativeai as genai
from ics import Calendar, Event
import json
import datetime
import re
import os

# ==========================================
# [설정] 팀장님 API 키를 여기에 넣으세요
# (친구들에게 공유할 땐 이 키를 빼고 입력받게 할 수도 있습니다)
DEFAULT_API_KEY = "내_키_여기에_붙여넣기" 
# ==========================================

# 1. 웹사이트 제목 꾸미기
st.set_page_config(page_title="DUWELL AI 비서", page_icon="📅")
st.title("🎙️ DUWELL 회의 요약 & 일정 비서")
st.write("녹음 파일을 올리시면 **일정 파일(.ics)**을 만들어 드립니다!")

# 2. 파일 업로드 버튼 만들기
uploaded_file = st.file_uploader("녹음 파일을 여기에 드래그하세요", type=["mp3", "m4a", "wav"])

# 3. 분석 시작 버튼
if uploaded_file is not None:
    if st.button("🚀 분석 및 일정 생성 시작"):
        
        # 임시 파일 저장
        with open("temp_audio.mp3", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("🎧 AI가 내용을 듣고 분석 중입니다... (잠시만 기다려주세요)")

        try:
            # AI 설정
            genai.configure(api_key=DEFAULT_API_KEY)
            model = genai.GenerativeModel("gemini-flash-latest")
            
            # 파일 업로드 및 분석
            myfile = genai.upload_file("temp_audio.mp3")
            
            prompt = """
            이 회의 녹음 파일을 분석해서 '일정'과 '할 일'을 뽑아줘.
            반드시 아래와 같은 [JSON 형식]으로만 답변해.
            [
                {
                    "name": "일정 제목",
                    "begin": "2026-02-01 14:00:00",
                    "end": "2026-02-01 15:00:00",
                    "description": "상세 내용 및 할 일"
                }
            ]
            * 날짜는 2026년 2월 기준, 시간 불명확하면 오전 9시.
            """
            
            response = model.generate_content([myfile, prompt])
            
            # JSON 정리
            txt = response.text
            if "```" in txt:
                txt = re.search(r'```(?:json)?(.*?)```', txt, re.DOTALL).group(1)
            schedule_data = json.loads(txt)

            # ICS 파일 생성
            c = Calendar()
            summary_text = ""
            for item in schedule_data:
                e = Event()
                e.name = item['name']
                e.begin = item['begin']
                e.end = item['end']
                e.description = item['description']
                c.events.add(e)
                summary_text += f"- 📌 {item['name']} ({item['begin']})\n"

            # 화면에 결과 보여주기
            st.success("✅ 분석 완료!")
            st.text_area("요약 내용", summary_text, height=150)

            # 다운로드 버튼 만들기
            ics_data = c.serialize()
            st.download_button(
                label="📥 내 캘린더에 넣기 (파일 다운로드)",
                data=ics_data,
                file_name="meeting_schedule.ics",
                mime="text/calendar"
            )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
        
        # 청소
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")