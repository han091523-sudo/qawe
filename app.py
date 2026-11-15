"""우리 집 휴식 취향 실험실
실행: streamlit run app.py
배포: GitHub에 두 파일 업로드 → Streamlit Community Cloud → app.py 선택.
API 키 불필요. 브라우저 세션별 독립 기록. JSON 백업으로 보관/이동 가능.
"""
import datetime as dt
import html
import json
import random
import time
import uuid
import streamlit as st

ACTIVITIES = [
    ('창밖 한 장면', '창밖에서 눈에 들어오는 색 세 가지를 천천히 찾아보세요.', '조용히', '앉아서'),
    ('한 곡만 듣기', '좋아하는 노래 한 곡을 골라 다른 일을 하지 않고 들어보세요. 음악 재생은 평소 쓰는 앱을 이용하세요.', '음악', '앉아서'),
    ('사진 한 장', '사진첩에서 다시 보고 싶은 사진 한 장을 골라 그 순간을 떠올려 보세요.', '추억', '앉아서'),
    ('멍 때리는 자리', '편한 자세로 앉아 잠깐 아무것도 하지 않아도 괜찮은 시간을 가져보세요.', '조용히', '앉아서'),
    ('종이 위 낙서', '종이에 떠오르는 선이나 모양을 자유롭게 그려보세요. 완성할 필요는 없어요.', '만들기', '앉아서'),
    ('색깔 수집', '자리에서 보이는 물건 중 오늘 마음에 드는 색을 찾아보세요.', '만들기', '앉아서'),
    ('짧은 바깥 구경', '원하고 움직임이 편한 경우에만, 안전하고 익숙한 곳을 잠깐 둘러보세요. 불편하면 앉아서 창밖 보기로 바꿔도 돼요.', '바깥', '걷기'),
    ('한 사람과 쉬는 대화', '대화하고 싶은 가족이 괜찮다면, 오늘 있었던 사소한 일 하나만 나눠보세요.', '대화', '앉아서'),
]
RATINGS = ('다시 하고 싶다', '보통이다', '나와 안 맞는다')


def validate(data):
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('백업 버전을 확인해 주세요.')
    rows = data.get('records')
    if not isinstance(rows, list) or len(rows) > 3000:
        raise ValueError('기록은 최대 3,000개입니다.')
    clean = []
    seen = set()
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError('기록 형식 오류')
        for k, limit in [('id',80),('name',20),('activity',60),('date',40),('note',300)]:
            if not isinstance(r.get(k), str) or len(r[k]) > limit:
                raise ValueError('기록 내용을 확인해 주세요.')
        if not r['id'] or r['id'] in seen or not r['name'].strip():
            raise ValueError('이름 또는 중복 기록 오류')
        if r.get('rating') not in RATINGS or type(r.get('minutes')) is not int or not 1 <= r['minutes'] <= 30:
            raise ValueError('시간 또는 평가 오류')
        dt.datetime.fromisoformat(r['date'])
        seen.add(r['id'])
        clean.append({k:r[k] for k in ('id','name','activity','date','note','rating','minutes')})
    return clean


def summary(rows):
    result = {}
    for r in rows:
        item = result.setdefault(r['activity'], [0,0,0])
        item[RATINGS.index(r['rating'])] += 1
    return sorted(result.items(), key=lambda x: (-(x[1][0]/sum(x[1])), -sum(x[1]), x[0]))


def main():
    st.set_page_config(page_title='우리 집 휴식 취향 실험실', page_icon='🌿', layout='centered')
    st.markdown('''<style>
.stApp{background:#f4f6f1;color:#283f35}.block-container{max-width:850px;padding-top:2rem}
h1,h2,h3{color:#284b3c}.hero{background:#234c3c;color:#fffbed;padding:30px;border-radius:22px;margin-bottom:18px}.hero h1{color:#fffbed;font-size:2rem}.hero p{color:#dfebd8;line-height:1.8}.card{background:#fffdf5;border:1px solid #d9e2d4;border-radius:18px;padding:24px;margin:18px 0}.card h3{margin-top:0}.tag{font-size:12px;letter-spacing:2px}.stButton>button[kind="primary"]{background:#356348;border:0}
</style>''', unsafe_allow_html=True)
    ss=st.session_state
    if 'records' not in ss: ss.records=[]
    if 'experiment' not in ss: ss.experiment=None
    st.markdown('''<div class="hero"><div class="tag">A SMALL BREAK · A PERSONAL DISCOVERY</div><h1>🌿 우리 집 휴식 취향 실험실</h1><p>남들이 좋다는 휴식 말고,<br>나에게 다시 하고 싶은 휴식을 찾아봐요.</p></div>''', unsafe_allow_html=True)
    st.caption('경쟁도 연속 출석도 없어요. 마음에 안 맞는 휴식을 알아낸 것도 소중한 발견이에요.')
    with st.sidebar:
        st.header('기록 보관함')
        st.info('이 앱은 접속 세션별로 독립적이에요. 다른 휴대폰과 자동 공유되지 않으며, 새로고침·세션 종료 시 기록이 사라질 수 있어요.')
        payload=json.dumps({'version':1,'records':ss.records},ensure_ascii=False,indent=2)
        st.download_button('JSON 백업 저장',payload,'휴식취향백업.json','application/json',use_container_width=True)
        upload=st.file_uploader('백업 불러오기',type=['json'])
        confirm=st.checkbox('불러오면 현재 기록을 대체합니다.')
        if st.button('백업 적용',disabled=not upload or not confirm):
            try:
                if upload.size>2000000: raise ValueError('파일은 2MB 이하여야 해요.')
                rows=validate(json.loads(upload.getvalue().decode('utf-8-sig')))
                ss.records=rows
                st.rerun()
            except (ValueError,TypeError,KeyError,UnicodeError):
                st.error('백업 형식이 올바르지 않아요. 기존 기록은 유지했어요.')
        st.caption('자신의 기록은 본인 동의 없이 가족에게 공개하지 마세요. 상세 건강정보는 적지 않아도 돼요.')
    explore, discover, history=st.tabs(['🧪 오늘의 실험','🌱 나의 휴식 취향','📔 실험 노트'])
    with explore:
        st.subheader('오늘은 어떻게 쉬고 싶나요?')
        if ss.experiment is None:
            name=st.text_input('내 이름 또는 별명',max_chars=20,placeholder='예: 엄마, 아빠, 나')
            mins=st.select_slider('오늘 내어 볼 시간',options=[1,3,5,10,15,20,30],value=3)
            style=st.selectbox('지금 끌리는 활동', ['아무거나','조용히','음악','추억','만들기','바깥','대화'])
            seated=st.checkbox('앉아서 할 수 있는 활동만',value=True)
            candidates=[a for a in ACTIVITIES if (style=='아무거나' or a[2]==style) and (not seated or a[3]=='앉아서')]
            if not candidates:
                st.info('이 조건에 맞는 활동이 없어요. 활동 종류를 바꾸거나, 원하는 활동을 직접 적어 주세요.')
            custom=st.text_input('또는 내가 하고 싶은 휴식',max_chars=60,placeholder='선택 사항 · 예: 좋아하는 책 두 쪽 읽기')
            if st.button('오늘의 휴식 만나기',type='primary',use_container_width=True):
                if not name.strip(): st.warning('기록을 구분할 별명을 적어 주세요.')
                elif not candidates and not custom.strip(): st.warning('활동 조건을 바꾸거나 직접 적어 주세요.')
                else:
                    a=(custom.strip(),'내가 정한 방식으로 부담 없이 쉬어보세요. 불편하거나 원하지 않으면 언제든 중단해도 괜찮아요.','직접 선택','자유') if custom.strip() else random.choice(candidates)
                    ss.experiment={'name':name.strip(),'minutes':mins,'activity':a[0],'guide':a[1],'start':None}
                    st.rerun()
        else:
            e=ss.experiment
            st.markdown(f'<div class="card"><span class="tag">{e["minutes"]}분의 작은 실험</span><h3>{html.escape(e["activity"])}</h3><p>{html.escape(e["guide"])}</p></div>',unsafe_allow_html=True)
            st.caption('시간은 목표일 뿐이에요. 끝까지 채울 필요도, 잘 해낼 필요도 없어요.')
            if e['start'] is None:
                if st.button('잠깐 쉬고 올게요',type='primary',use_container_width=True):
                    e['start']=time.time();st.rerun()
            else:
                elapsed=max(0,int((time.time()-e['start'])//60))
                st.info(f'시작 후 약 {elapsed}분 · 시간은 화면을 새로 확인할 때 갱신돼요. 앱을 켜 둔 시간이지 실제 휴식 측정값은 아니에요.')
                if st.button('시간 다시 확인'):st.rerun()
            with st.form('review'):
                rating=st.radio('해 보니 어땠나요?',RATINGS,index=None)
                note=st.text_area('나에게 남기는 한 줄 · 선택',max_chars=300,placeholder='예: 음악보다 조용히 앉아 있는 게 좋았어.')
                done=st.form_submit_button('경험 기록하기',use_container_width=True)
                if done:
                    if rating is None: st.warning('어땠는지 하나 골라 주세요.')
                    elif len(ss.records)>=3000: st.warning('기록이 가득 찼어요. 백업 후 정리해 주세요.')
                    else:
                        ss.records.append({'id':uuid.uuid4().hex,'name':e['name'],'activity':e['activity'],'minutes':e['minutes'],'date':dt.datetime.now(dt.timezone.utc).isoformat(),'rating':rating,'note':note.strip()})
                        ss.experiment=None;ss.just_saved=True;st.rerun()
            if st.button('이번 활동은 건너뛰기'):
                ss.experiment=None;st.rerun()
        if ss.pop('just_saved',False):st.success('경험을 기록했어요. ‘나의 휴식 취향’에서 발견을 확인해 보세요.')
    with discover:
        st.subheader('내가 다시 고르고 싶었던 휴식')
        names=sorted({r['name'] for r in ss.records})
        if not names:st.info('아직 기록이 없어요. 짧은 활동 하나를 해 보고 느낌을 남겨 보세요.')
        else:
            person=st.selectbox('누구의 기록인가요?',names,key='discover_name')
            rows=[r for r in ss.records if r['name']==person]
            st.write(f'총 {len(rows)}번의 경험 · {len({r["activity"] for r in rows})}가지 활동')
            for activity, counts in summary(rows):
                total=sum(counts)
                st.markdown(f'**{activity}** · {total}회 경험')
                st.write(f'다시 하고 싶다 {counts[0]}회 · 보통 {counts[1]}회 · 나와 안 맞는다 {counts[2]}회')
                st.progress(counts[0]/total,text=f'다시 하고 싶다고 답한 비율 {counts[0]/total:.0%}')
                if total<3:st.caption('아직 기록이 적어요. 현재의 느낌일 뿐, 확정된 취향은 아니에요.')
            st.caption('반복 의향 비율 → 경험 수 순으로 정렬합니다. 조건과 날마다 느낌이 달라질 수 있어요. 건강 효과나 가족 간 우열을 평가하지 않습니다.')
    with history:
        st.subheader('쌓여 가는 나의 발견')
        names=sorted({r['name'] for r in ss.records})
        chosen=st.selectbox('기록 보기',['전체']+names,key='history_filter')
        rows=[r for r in ss.records if chosen=='전체' or r['name']==chosen]
        if rows:
            text='\n\n'.join(f'{r["date"]} | {r["name"]}\n{r["activity"]} · 계획 {r["minutes"]}분\n{r["rating"]}\n{r["note"]}' for r in reversed(rows))
            st.download_button('보이는 노트 TXT 저장',text,'휴식노트.txt','text/plain')
        else:st.info('아직 기록이 없어요.')
        for r in reversed(rows):
            label=f'{r["name"]} · {r["activity"]} · {r["rating"]}'
            with st.expander(label):
                st.caption(f'{r["date"][:10]} (UTC 기준) · 계획 시간 {r["minutes"]}분')
                st.write(r['note'] or '한 줄 없이 남긴 경험이에요.')
                agree=st.checkbox('이 기록을 삭제할게요',key='agree_'+r['id'])
                if st.button('기록 삭제',disabled=not agree,key='del_'+r['id']):
                    ss.records=[v for v in ss.records if v['id']!=r['id']];st.rerun()
    st.divider()
    st.caption('이 앱은 개인의 휴식 선호를 돌아보는 도구이며 진단·치료·의학적 효과를 제공하지 않습니다. 활동이 불편하면 중단하고 다른 방식을 선택하세요.')

if __name__=='__main__':
    main()
