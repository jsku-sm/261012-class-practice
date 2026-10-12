import io

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CSV 데이터 탐색", page_icon="📊", layout="wide")
st.title("📊 CSV 데이터 탐색")
st.write("CSV 파일을 업로드하고 변수를 선택해 대화형 차트를 만들어 보세요.")

with st.sidebar:
    st.header("데이터 업로드")
    uploaded = st.file_uploader("CSV 파일 선택", type=["csv"])
    encoding = st.selectbox("인코딩", ["utf-8-sig", "cp949", "euc-kr"])
    delimiter = st.selectbox("구분자", [",", ";", "\t"], format_func=lambda value: "탭" if value == "\t" else value)

if uploaded is None:
    st.info("왼쪽에서 CSV 파일을 업로드해 주세요. 첫 번째 행은 변수 이름으로 사용합니다.")
    st.stop()

try:
    df = pd.read_csv(io.BytesIO(uploaded.getvalue()), encoding=encoding, sep=delimiter)
except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as error:
    st.error(f"파일을 읽을 수 없습니다. 인코딩과 구분자를 확인해 주세요. ({error})")
    st.stop()

if df.empty:
    st.warning("업로드한 파일에 데이터 행이 없습니다.")
    st.stop()

numeric = df.select_dtypes(include="number").columns.tolist()
categorical = df.select_dtypes(exclude="number").columns.tolist()

metrics = st.columns(3)
metrics[0].metric("데이터 행", len(df))
metrics[1].metric("변수", len(df.columns))
metrics[2].metric("결측값", int(df.isna().sum().sum()))
with st.expander("데이터 미리보기", expanded=True):
    st.dataframe(df.head(100), use_container_width=True)
    st.caption("처음 100개 행을 표시합니다. 차트는 전체 데이터를 사용합니다.")
with st.expander("숫자형 변수 요약"):
    if numeric:
        st.dataframe(df[numeric].describe().T, use_container_width=True)
    else:
        st.info("숫자형 변수가 없습니다. 범주별 개수 차트를 사용할 수 있습니다.")

charts = ["범주별 개수"]
if numeric:
    charts += ["히스토그램", "박스 플롯"]
if numeric and categorical:
    charts += ["범주별 평균"]
if len(numeric) >= 2:
    charts += ["산점도", "상관관계"]

st.subheader("변수 시각화")
chart = st.selectbox("차트 종류", charts)
color = None
if categorical and chart in ["히스토그램", "박스 플롯", "산점도"]:
    color = st.selectbox("색상 구분", [None] + categorical, format_func=lambda value: "없음" if value is None else value)

if chart == "범주별 개수":
    variable = st.selectbox("변수", categorical or df.columns.tolist())
    # 문자열로 통일해 숫자와 결측값이 함께 있는 경우에도 축을 표시합니다.
    counts = df[variable].astype("string").fillna("(결측값)").value_counts().rename_axis("값").reset_index(name="개수")
    fig = px.bar(counts, x="값", y="개수", title=f"{variable}별 개수")
elif chart == "히스토그램":
    variable = st.selectbox("숫자형 변수", numeric)
    bins = st.slider("구간 수", 5, 100, 20)
    fig = px.histogram(df, x=variable, color=color, nbins=bins, barmode="overlay", opacity=0.75, title=f"{variable} 분포")
elif chart == "박스 플롯":
    variable = st.selectbox("숫자형 변수", numeric)
    fig = px.box(df, x=color, y=variable, color=color, title=f"{variable} 분포 비교")
elif chart == "범주별 평균":
    group = st.selectbox("범주형 변수", categorical)
    variable = st.selectbox("평균을 구할 숫자형 변수", numeric)
    averages = df.assign(**{group: df[group].astype("string").fillna("(결측값)")}).groupby(group, dropna=False)[variable].mean().reset_index()
    fig = px.bar(averages, x=group, y=variable, title=f"{group}별 {variable} 평균")
elif chart == "산점도":
    left, right = st.columns(2)
    x = left.selectbox("X축", numeric)
    y = right.selectbox("Y축", numeric, index=1)
    fig = px.scatter(df, x=x, y=y, color=color, title=f"{x}와 {y}의 관계")
else:
    selected = st.multiselect("비교할 숫자형 변수", numeric, default=numeric)
    if len(selected) < 2:
        st.info("숫자형 변수를 두 개 이상 선택해 주세요.")
        st.stop()
    fig = px.imshow(df[selected].corr(), text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", title="변수 간 상관관계")
    st.caption("값이 일정한 변수의 상관계수는 계산되지 않습니다. 상관관계는 인과관계를 의미하지 않습니다.")

st.plotly_chart(fig, use_container_width=True)
st.caption("마우스로 값을 확인하거나 차트를 확대할 수 있습니다. 숫자형 결측값은 계산에서 제외됩니다.")
