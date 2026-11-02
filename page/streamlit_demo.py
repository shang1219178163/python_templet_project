import streamlit as st

from base_widget import (Column, CrossAxisAlignment, MainAxisAlignment,
                         MainAxisSize, Row, Wrap)

MAIN_ALIGNS = (
    ("start", MainAxisAlignment.start),
    ("end", MainAxisAlignment.end),
    ("center", MainAxisAlignment.center),
    ("space_between", MainAxisAlignment.space_between),
    ("space_around", MainAxisAlignment.space_around),
    ("space_evenly", MainAxisAlignment.space_evenly),
)
CROSS_ALIGNS = (
    ("start", CrossAxisAlignment.start),
    ("end", CrossAxisAlignment.end),
    ("center", CrossAxisAlignment.center),
    ("stretch", CrossAxisAlignment.stretch),
    ("baseline", CrossAxisAlignment.baseline),
)

st.title("streamlit 入门演示")
st.header("streamlit 一级标题")
st.subheader("streamlit 二级标题")
st.write(""" 
“Skill”的加载执行机制取决于你具体使用的平台。目前主流实现（如 Claude Code、各类 Agent 框架）普遍遵循 “渐进式披露” 原则：启动时只加载元数据，匹配到任务时才加载完整指令，需要时再调用脚本或参考文件。
""")

st.subheader("流水按钮")
with Wrap(spacing=8, run_spacing=8):
    for index in range(9):
        if st.button(f"按钮{index + 1}", key=f"flow_btn_{index}"):
            print(f"按钮{index}")
            st.session_state["clicked_button"] = index

if "clicked_button" in st.session_state:
    st.write(f"按钮 {st.session_state['clicked_button']}")

st.header("Flex 对齐")

st.subheader("Row · MainAxisAlignment")
for name, value in MAIN_ALIGNS:
    st.caption(f"main_axis_alignment = {name}")
    with st.container(border=True):
        with Row(main_axis_alignment=value, spacing=8, key=f"row_main_{name}"):
            for index, label in enumerate(("A", "B", "C")):
                st.button(label, key=f"row_main_{name}_{index}")

st.subheader("Row · CrossAxisAlignment")
for name, value in CROSS_ALIGNS:
    st.caption(f"cross_axis_alignment = {name}")
    with st.container(border=True):
        with Row(
            cross_axis_alignment=value,
            spacing=8,
            height=140,
            key=f"row_cross_{name}",
        ):
            with st.container(border=True):
                st.button("A", key=f"row_cross_{name}_0")
            with st.container(border=True):
                st.button("B", key=f"row_cross_{name}_1")
                st.caption("更高")
            with st.container(border=True):
                st.button("C", key=f"row_cross_{name}_2")

st.subheader("Column · MainAxisAlignment")
st.caption("固定高度后才能看出 space_between / space_around / space_evenly 的留白差异。")
for group in (MAIN_ALIGNS[:3], MAIN_ALIGNS[3:]):
    cols = st.columns(3)
    for col, (name, value) in zip(cols, group):
        with col:
            st.caption(f"{name}")
            with Column(
                main_axis_alignment=value,
                spacing=8,
                height=260,
                border=True,
                key=f"col_main_{name}",
            ):
                for index, label in enumerate(("A", "B", "C")):
                    st.button(label, key=f"col_main_{name}_{index}")

st.subheader("Column · CrossAxisAlignment")
for group in (CROSS_ALIGNS[:3], CROSS_ALIGNS[3:]):
    cols = st.columns(len(group))
    for col, (name, value) in zip(cols, group):
        with col:
            st.caption(f"{name}")
            with st.container(border=True):
                with Column(
                    cross_axis_alignment=value,
                    spacing=8,
                    height=180,
                    key=f"col_cross_{name}",
                ):
                    for index, label in enumerate(("A", "B", "C")):
                        st.button(label, key=f"col_cross_{name}_{index}")

st.subheader("MainAxisSize")
st.caption("外框是父容器可用宽度。max 拉满后 space_between 会把 A / C 撑到两端；min 只包住内容，按钮挤在一起。")
for name, value in (("max", MainAxisSize.max), ("min", MainAxisSize.min)):
    st.caption(f"Row main_axis_size = {name}")
    with st.container(border=True):
        with Row(
            main_axis_alignment=MainAxisAlignment.space_between,
            main_axis_size=value,
            spacing=8,
            border=True,
            key=f"row_size_{name}",
        ):
            for index, label in enumerate(("A", "B", "C")):
                st.button(label, key=f"row_size_{name}_{index}")
