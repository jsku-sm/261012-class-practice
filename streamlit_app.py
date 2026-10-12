from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CSV 시각화", page_icon="📊", layout="wide")
st.title("📊 CSV 데이터 시각화")
st.write("CSV를 업로드하고 변수를 선택해 Plotly 차트를 만들어 보세요.")

uploaded = st.sidebar.file_uploader("CSV 파일 업로드", type="csv")
encoding = st.sidebar.selectbox("파일 인코딩", ["utf-8-sig", "cp949", "euc-kr"])
separator = st.sidebar.selectbox("구분자", [",", ";", "\t"])
sample = Path(__file__).parent / "StudentsPerformance.csv"
if uploaded is None:
    if not sample.exists():
        st.info("왼쪽에서 CSV 파일을 업로드해 주세요.")
        st.stop()
    st.caption("샘플 데이터: StudentsPerformance.csv")

# 업로드한 파일이 있으면 샘플 대신 읽습니다.
try:
    df = pd.read_csv(uploaded if uploaded is not None else sample, encoding=encoding, sep=separator)
except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError, OSError) as error:
    st.error(f"CSV를 읽을 수 없습니다. 인코딩과 구분자를 확인해 주세요.\n\n{error}")
    st.stop()
if df.empty:
    st.warning("데이터가 비어 있습니다.")
    st.stop()

numeric = df.select_dtypes(include="number").columns.tolist()
categories = df.select_dtypes(exclude="number").columns.tolist()
filter_column = st.sidebar.selectbox("필터 변수", [None] + categories, format_func=lambda x: "필터 없음" if x is None else x)
if filter_column is not None:
    options = df[filter_column].dropna().unique().tolist()
    values = st.sidebar.multiselect("표시할 값", options, default=options)
    df = df[df[filter_column].isin(values)]

cols = st.columns(3)
cols[0].metric("행 수", len(df))
cols[1].metric("변수 수", len(df.columns))
cols[2].metric("결측값 수", int(df.isna().sum().sum()))
with st.expander("데이터 미리보기", expanded=True):
    st.dataframe(df.head(100), width="stretch")
    st.caption("최대 100개 행을 표시합니다. 차트는 필터링된 전체 데이터를 사용합니다.")
if df.empty:
    st.warning("필터에 해당하는 데이터가 없습니다. 표시할 값을 선택해 주세요.")
    st.stop()

types = ["범주별 개수"]
if numeric:
    types += ["히스토그램", "박스 플롯"]
    if categories:
        types += ["범주별 평균"]
if len(numeric) >= 2:
    types += ["산점도", "상관관계"]
chart = st.selectbox("차트 종류", types, index=1 if numeric else 0)
color = None
if chart in ["히스토그램", "박스 플롯", "산점도"]:
    color = st.selectbox("색상 구분 변수", [None] + categories, format_func=lambda x: "없음" if x is None else x)

if chart == "범주별 개수":
    column = st.selectbox("개수를 셀 변수", categories or df.columns.tolist())
    counts = df[column].value_counts(dropna=False).rename_axis("값").reset_index(name="개수")
    fig = px.bar(counts, x="값", y="개수", title=f"{column}별 개수")
elif chart == "히스토그램":
    column = st.selectbox("숫자형 변수", numeric)
    bins = st.slider("구간 수", 5, 100, 20)
    fig = px.histogram(df, x=column, color=color, nbins=bins, barmode="overlay", opacity=0.7, title=f"{column} 분포")
elif chart == "박스 플롯":
    column = st.selectbox("숫자형 변수", numeric)
    group = st.selectbox("그룹 변수", [None] + categories, format_func=lambda x: "없음" if x is None else x)
    fig = px.box(df, x=group, y=column, color=color, title=f"{column} 분포 비교")
elif chart == "범주별 평균":
    group = st.selectbox("범주형 변수", categories)
    column = st.selectbox("평균을 구할 변수", numeric)
    averages = df.groupby(group, dropna=False)[column].mean().reset_index()
    fig = px.bar(averages, x=group, y=column, title=f"{group}별 {column} 평균")
elif chart == "산점도":
    x = st.selectbox("X축 변수", numeric)
    y = st.selectbox("Y축 변수", numeric, index=1)
    fig = px.scatter(df, x=x, y=y, color=color, title=f"{x}와 {y}의 관계")
else:
    selected = st.multiselect("비교할 숫자형 변수", numeric, default=numeric)
    if len(selected) < 2:
        st.info("변수를 두 개 이상 선택해 주세요.")
        st.stop()
    fig = px.imshow(df[selected].corr(), text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", title="상관관계")
    st.caption("값이 일정한 변수는 상관계수가 계산되지 않습니다. 상관관계는 인과관계를 뜻하지 않습니다.")

st.plotly_chart(fig, width="stretch")
st.caption("마우스로 값을 확인하고 드래그로 확대할 수 있습니다. 숫자형 결측값은 차트와 평균 계산에서 제외됩니다.")
