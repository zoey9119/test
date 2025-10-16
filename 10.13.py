import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import requests
import json
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="个人信息管理系统", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "personal_management.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def init_database():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.executescript("""
    -- 个人基本信息表
    CREATE TABLE IF NOT EXISTS personal_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT,
        birth_date TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        occupation TEXT,
        education_level TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 分类表
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    );

    -- 荣誉信息表
    CREATE TABLE IF NOT EXISTS honors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        category_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        issuing_authority TEXT,
        issue_date TEXT,
        priority TEXT DEFAULT '中',
        progress INTEGER DEFAULT 100,
        attachment TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (person_id) REFERENCES personal_info(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    -- 日程信息表
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        start_time TEXT,
        end_time TEXT,
        location TEXT,
        status TEXT DEFAULT '待完成',
        priority TEXT DEFAULT '中',
        reminder TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (person_id) REFERENCES personal_info(id) ON DELETE CASCADE
    );

    -- 教育经历表
    CREATE TABLE IF NOT EXISTS education (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL,
        institution TEXT NOT NULL,
        degree TEXT,
        major TEXT,
        start_date TEXT,
        end_date TEXT,
        gpa REAL,
        achievements TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (person_id) REFERENCES personal_info(id) ON DELETE CASCADE
    );

    -- 原记录表保持不变
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER DEFAULT 1,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        notes TEXT,
        priority TEXT,
        progress INTEGER,
        created_at TEXT,
        attachment TEXT,
        FOREIGN KEY (person_id) REFERENCES personal_info(id)
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM personal_info")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO personal_info (name, gender, birth_date, email, phone, address, occupation, education_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("胡一心", "男", "2025-01-01", "54088@email.com", "666666", "上海杨浦", "雅典娜", "本科"))

        default_categories = [
            ('学术荣誉', '奖学金、学术竞赛等奖项'),
            ('工作成就', '工作相关的奖励和成就'),
            ('技能证书', '各类技能认证证书'),
            ('项目经验', '完成的重要项目'),
            ('其他荣誉', '其他类型的荣誉和成就')
        ]
        cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", default_categories)

    conn.commit()
    return conn


conn = init_database()
cursor = conn.cursor()


def get_personal_info():
    """获取个人信息"""
    return pd.read_sql_query("SELECT * FROM personal_info", conn)


def update_personal_info(info_id, update_dict):
    """更新个人信息"""
    set_clause = ", ".join([f"{key} = ?" for key in update_dict.keys()])
    values = list(update_dict.values())
    values.append(info_id)

    query = f"UPDATE personal_info SET {set_clause} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()


def insert_honor(honor_data):
    """插入荣誉信息"""
    cursor.execute("""
    INSERT INTO honors (person_id, category_id, title, description, issuing_authority, issue_date, priority, progress, attachment)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, honor_data)
    conn.commit()


def get_honors():
    """获取所有荣誉信息（带分类信息）"""
    return pd.read_sql_query("""
    SELECT h.*, c.name as category_name, p.name as person_name 
    FROM honors h 
    LEFT JOIN categories c ON h.category_id = c.id 
    LEFT JOIN personal_info p ON h.person_id = p.id
    ORDER BY h.issue_date DESC
    """, conn)


def delete_honor(honor_id):
    """删除荣誉信息"""
    cursor.execute("DELETE FROM honors WHERE id=?", (honor_id,))
    conn.commit()


def insert_schedule(schedule_data):
    """插入日程信息"""
    cursor.execute("""
    INSERT INTO schedules (person_id, title, description, start_time, end_time, location, status, priority, reminder)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, schedule_data)
    conn.commit()


def get_schedules():
    """获取所有日程信息"""
    return pd.read_sql_query("""
    SELECT s.*, p.name as person_name 
    FROM schedules s 
    LEFT JOIN personal_info p ON s.person_id = p.id
    ORDER BY s.start_time
    """, conn)


def update_schedule(schedule_id, field, value):
    """更新日程信息"""
    cursor.execute(f"UPDATE schedules SET {field}=? WHERE id=?", (value, schedule_id))
    conn.commit()


def delete_schedule(schedule_id):
    """删除日程信息"""
    cursor.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
    conn.commit()


def insert_education(education_data):
    """插入教育经历"""
    cursor.execute("""
    INSERT INTO education (person_id, institution, degree, major, start_date, end_date, gpa, achievements)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, education_data)
    conn.commit()


def get_education():
    """获取所有教育经历"""
    return pd.read_sql_query("""
    SELECT e.*, p.name as person_name 
    FROM education e 
    LEFT JOIN personal_info p ON e.person_id = p.id
    ORDER BY e.start_date DESC
    """, conn)


def delete_education(education_id):
    """删除教育经历"""
    cursor.execute("DELETE FROM education WHERE id=?", (education_id,))
    conn.commit()


def get_categories():
    """获取分类信息"""
    return pd.read_sql_query("SELECT * FROM categories", conn)


# === 保持原有的数据操作函数 ===
def read_data():
    return pd.read_sql_query(
        "SELECT r.*, p.name as person_name FROM records r LEFT JOIN personal_info p ON r.person_id = p.id", conn)


def insert_data(record):
    cursor.execute("""
    INSERT INTO records (person_id, title, category, notes, priority, progress, created_at, attachment)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        1,  # 默认关联到第一个个人信息
        record.get("title"), record.get("category"), record.get("notes"),
        record.get("priority"), record.get("progress"),
        record.get("created_at"), record.get("attachment")
    ))
    conn.commit()


def update_data(record_id, field, value):
    cursor.execute(f"UPDATE records SET {field}=? WHERE id=?", (value, record_id))
    conn.commit()


def delete_data(record_id):
    cursor.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()


st.sidebar.title("功能导航")
page = st.sidebar.radio("选择功能", [
    "AI助手", "数据输入", "数据查询与管理",
    "个人信息管理", "荣誉信息管理", "日程管理", "教育经历管理", "系统概览"
])

if page == "AI助手":
    st.header("AI助手")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "ai_pending_data" not in st.session_state:
        st.session_state["ai_pending_data"] = None

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state["ai_pending_data"]:
        st.subheader("信息补全")
        data = st.session_state["ai_pending_data"]

        data["title"] = st.text_input("标题 *", data.get("title") or "")
        data["category"] = st.selectbox(
            "类别 *",
            ["荣誉", "教育经历", "竞赛", "证书", "账号", "其他"],
            index=["荣誉", "教育经历", "竞赛", "证书", "账号", "其他"].index(data.get("category") or "荣誉")
        )
        data["priority"] = st.selectbox(
            "优先级",
            ["低", "中", "高"],
            index=["低", "中", "高"].index(data.get("priority") or "中")
        )
        data["progress"] = st.slider("进度 (%)", 0, 100, int(data.get("progress") or 0))
        data["notes"] = st.text_area("备注", value=data.get("notes") or "")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认保存", use_container_width=True):
                data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data["attachment"] = ""
                insert_data(data)
                st.success("数据已补全")
                st.session_state["messages"].append(
                    {"role": "assistant", "content": f"已保存记录：{data['title']}"}
                )
                st.session_state["ai_pending_data"] = None
                st.rerun()
        with col2:
            if st.button("取消", use_container_width=True):
                st.session_state["ai_pending_data"] = None
                st.rerun()

    else:
        user_input = st.chat_input("请输入你的请求...")
        if user_input:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            prompt = f"""
你是一个信息管理AI助手，数据库表结构如下：
- personal_info(id, name, gender, birth_date, email, phone, address, occupation, education_level)
- records(id, person_id, title, category, notes, priority, progress, created_at, attachment)
- honors(id, person_id, category_id, title, description, issuing_authority, issue_date, priority, progress)
- schedules(id, person_id, title, description, start_time, end_time, location, status, priority, reminder)
- education(id, person_id, institution, degree, major, start_date, end_date, gpa, achievements)
- categories(id, name, description)

请根据用户输入的自然语言，判断其意图和操作的表：
- 查询个人信息（如"我的基本信息"）
- 新增荣誉（如"我获得了蓝桥杯一等奖"）
- 查询日程（如"查看我的日程"）
- 修改进度（如"把项目进度更新为50%"）

请返回一个JSON对象：
{{
  "action": "query" | "insert" | "update" | "delete",
  "table": "personal_info" | "records" | "honors" | "schedules" | "education",
  "criteria": "筛选条件或识别关键词",
  "data": {{
      // 根据操作的表不同，字段也不同
  }}
}}
用户输入：{user_input}
"""
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": "Bearer sk-809824f6fe04415fbab6982c04c3e0f3",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }

            with st.chat_message("assistant"):
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    result = response.json()

                    if "choices" not in result or not result["choices"]:
                        raise ValueError("AI响应为空")

                    model_reply = result["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(model_reply)
                    action = parsed.get("action")
                    table = parsed.get("table", "records")

                    if action == "query":
                        if table == "records":
                            df = read_data()
                        elif table == "honors":
                            df = get_honors()
                        elif table == "schedules":
                            df = get_schedules()
                        elif table == "education":
                            df = get_education()
                        elif table == "personal_info":
                            df = get_personal_info()
                        else:
                            df = read_data()

                        crit = str(parsed.get("criteria") or "").strip().lower()
                        if not crit:
                            crit = user_input.lower()


                        def match_record(row, keyword):
                            if not keyword:
                                return True
                            text_all = " ".join(str(v).lower() for v in row.values if pd.notna(v))
                            if keyword in text_all:
                                return True
                            return False


                        filtered = df[df.apply(lambda r: match_record(r, crit), axis=1)]
                        if filtered.empty:
                            st.warning(f"没有找到与『{crit}』相关的记录")
                        else:
                            st.success(f"找到 {len(filtered)} 条记录：")
                            st.dataframe(filtered, use_container_width=True)

                    elif action == "insert":
                        data = parsed.get("data", {})
                        if table == "records":
                            required = ["title", "category"]
                            if not all(data.get(k) for k in required):
                                st.warning("信息不完整，请补充。")
                                st.session_state["ai_pending_data"] = data
                                st.rerun()
                            else:
                                data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                data["attachment"] = ""
                                insert_data(data)
                                st.success(f"已添加记录：{data['title']}")
                        else:
                            st.info(f"AI建议添加到{table}表，但此功能需要手动操作")

                    elif action == "update":
                        st.info("更新操作需要手动在相应页面完成")

                    elif action == "delete":
                        st.info("删除操作需要手动在相应页面完成")
                    else:
                        st.error("无法识别AI操作")

                except json.JSONDecodeError:
                    st.error("AI返回格式错误")
                except Exception as e:
                    st.error(f"发生错误：{e}")

elif page == "数据输入":
    st.header("数据输入")
    with st.form("add_form", clear_on_submit=True):
        new_record = {}
        new_record["title"] = st.text_input("标题 *", placeholder="三好学生")
        new_record["category"] = st.selectbox("类别 *", ["荣誉", "教育经历", "竞赛", "证书", "账号", "其他"])
        new_record["notes"] = st.text_area("备注", height=100)
        new_record["priority"] = st.selectbox("优先级", ["低", "中", "高"], index=1)
        new_record["progress"] = st.slider("进度 (%)", 0, 100, 0)
        uploaded_file = st.file_uploader("上传附件", type=['txt', 'pdf', 'png', 'jpg'])
        submitted = st.form_submit_button("保存", type="primary", use_container_width=True)

    if submitted:
        new_record["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if uploaded_file:
            file_save_path = DATA_DIR / uploaded_file.name
            with open(file_save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            new_record["attachment"] = uploaded_file.name
        else:
            new_record["attachment"] = ""
        insert_data(new_record)
        st.success("已保存")

elif page == "数据查询与管理":
    st.header("数据查询与管理")
    df = read_data()
    if df.empty:
        st.info("暂无数据")
    else:
        search = st.text_input("搜索关键字", "")
        if search:
            df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]
        st.dataframe(df, use_container_width=True)
        st.subheader("编辑或删除记录")
        record_ids = df["id"].tolist()
        if record_ids:
            selected_id = st.selectbox("选择记录ID", record_ids)
            if selected_id:
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_progress = st.slider(
                        "修改进度",
                        0,
                        100,
                        int(df.loc[df['id'] == selected_id, 'progress'].values[0])
                    )
                    if st.button("更新进度", use_container_width=True):
                        update_data(selected_id, "progress", new_progress)
                        st.success("已更新")
                with col2:
                    new_priority = st.selectbox("修改优先级", ["低", "中", "高"])
                    if st.button("更新优先级", use_container_width=True):
                        update_data(selected_id, "priority", new_priority)
                        st.success("已更新")
                with col3:
                    if st.button("删除该记录", type="primary", use_container_width=True):
                        delete_data(selected_id)
                        st.warning("已删除该记录")

elif page == "个人信息管理":
    st.header("👤 个人信息管理")

    if 'personal_info' not in st.session_state:
        personal_info_df = get_personal_info()
        if not personal_info_df.empty:
            st.session_state.personal_info = personal_info_df.iloc[0].to_dict()
        else:
            st.session_state.personal_info = {
                'name': '',
                'gender': '男',
                'birth_date': '',
                'email': '',
                'phone': '',
                'address': '',
                'occupation': '',
                'education_level': '本科'
            }

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("基本信息")
        st.write(f"**姓名:** {st.session_state.personal_info['name']}")
        st.write(f"**性别:** {st.session_state.personal_info['gender']}")
        st.write(f"**出生日期:** {st.session_state.personal_info['birth_date']}")
        st.write(f"**职业:** {st.session_state.personal_info['occupation']}")

    with col2:
        st.subheader("联系信息")
        st.write(f"**邮箱:** {st.session_state.personal_info['email']}")
        st.write(f"**电话:** {st.session_state.personal_info['phone']}")
        st.write(f"**地址:** {st.session_state.personal_info['address']}")
        st.write(f"**教育程度:** {st.session_state.personal_info['education_level']}")

    with st.expander("编辑个人信息"):
        with st.form("personal_info_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("姓名", value=st.session_state.personal_info['name'])
                gender = st.selectbox("性别", ["男", "女", "其他"],
                                      index=["男", "女", "其他"].index(st.session_state.personal_info['gender']))
                birth_date = st.text_input("出生日期", value=st.session_state.personal_info['birth_date'])
                occupation = st.text_input("职业", value=st.session_state.personal_info['occupation'])

            with col2:
                email = st.text_input("邮箱", value=st.session_state.personal_info['email'])
                phone = st.text_input("电话", value=st.session_state.personal_info['phone'])
                address = st.text_area("地址", value=st.session_state.personal_info['address'])
                education_level = st.selectbox("教育程度",
                                               ["高中", "专科", "本科", "硕士", "博士", "其他"],
                                               index=["高中", "专科", "本科", "硕士", "博士", "其他"].index(
                                                   st.session_state.personal_info['education_level']))

            submitted = st.form_submit_button("更新信息")

            if submitted:
                # 构建更新字典
                update_dict = {
                    'name': name,
                    'gender': gender,
                    'birth_date': birth_date,
                    'occupation': occupation,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'education_level': education_level
                }


                personal_info_df = get_personal_info()
                if not personal_info_df.empty:
                    info_id = personal_info_df.iloc[0]['id']

                    update_personal_info(info_id, update_dict)


                    st.session_state.personal_info = update_dict
                    st.success("个人信息已更新！")

                    st.rerun()

elif page == "荣誉信息管理":
    st.header("🏆 荣誉信息管理")

    tab1, tab2 = st.tabs(["添加荣誉", "查看荣誉"])

    with tab1:
        st.subheader("添加荣誉信息")
        with st.form("honor_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("荣誉标题 *", placeholder="三好学生")
                categories = get_categories()
                category_options = [f"{row['id']}-{row['name']}" for _, row in categories.iterrows()]
                selected_category = st.selectbox("荣誉分类 *", category_options)
                issuing_authority = st.text_input("颁发机构")
                issue_date = st.text_input("颁发日期", placeholder="YYYY-MM-DD")

            with col2:
                description = st.text_area("详细描述", height=100)
                priority = st.selectbox("优先级", ["低", "中", "高"], index=1)
                progress = st.slider("进度", 0, 100, 100)

            if st.form_submit_button("添加荣誉"):
                if title:
                    category_id = int(selected_category.split('-')[0])
                    insert_honor((1, category_id, title, description, issuing_authority,
                                  issue_date, priority, progress, ""))
                    st.success("荣誉信息添加成功！")
                else:
                    st.warning("请输入荣誉标题")

    with tab2:
        st.subheader("荣誉记录")
        honors = get_honors()
        if not honors.empty:
            st.dataframe(honors, use_container_width=True)

            st.subheader("荣誉管理")
            honor_ids = honors["id"].tolist()
            if honor_ids:
                selected_honor_id = st.selectbox("选择荣誉记录ID", honor_ids)
                if selected_honor_id:
                    col1, col2 = st.columns(2)
                    with col1:
                        new_progress = st.slider(
                            "修改进度", 0, 100,
                            int(honors.loc[honors['id'] == selected_honor_id, 'progress'].values[0]),
                            key="honor_progress"
                        )
                        if st.button("更新进度", key="update_honor_progress"):
                            cursor.execute("UPDATE honors SET progress=? WHERE id=?",
                                           (new_progress, selected_honor_id))
                            conn.commit()
                            st.success("进度已更新")

                    with col2:
                        if st.button("删除该荣誉记录", type="primary"):
                            delete_honor(selected_honor_id)
                            st.warning("荣誉记录已删除")
                            st.rerun()
        else:
            st.info("暂无荣誉记录")

elif page == "日程管理":
    st.header("📅 日程管理")

    tab1, tab2 = st.tabs(["添加日程", "查看日程"])

    with tab1:
        st.subheader("添加新日程")
        with st.form("schedule_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("日程标题 *")
                start_time = st.text_input("开始时间", placeholder="YYYY-MM-DD HH:MM")
                end_time = st.text_input("结束时间", placeholder="YYYY-MM-DD HH:MM")
                location = st.text_input("地点")

            with col2:
                description = st.text_area("日程描述", height=100)
                status = st.selectbox("状态", ["待开始", "进行中", "已完成", "已取消"])
                priority = st.selectbox("优先级", ["低", "中", "高"], index=1)
                reminder = st.text_input("提醒时间", placeholder="提前15分钟")

            if st.form_submit_button("添加日程"):
                if title and start_time:
                    insert_schedule((1, title, description, start_time, end_time,
                                     location, status, priority, reminder))
                    st.success("日程添加成功！")
                else:
                    st.warning("请填写标题和开始时间")

    with tab2:
        st.subheader("日程列表")
        schedules = get_schedules()
        if not schedules.empty:

            status_filter = st.selectbox("按状态筛选", ["全部", "待开始", "进行中", "已完成", "已取消"])
            if status_filter != "全部":
                schedules = schedules[schedules['status'] == status_filter]

            st.dataframe(schedules, use_container_width=True)


            st.subheader("日程管理")
            schedule_ids = schedules["id"].tolist()
            if schedule_ids:
                selected_schedule_id = st.selectbox("选择日程ID", schedule_ids)
                if selected_schedule_id:
                    col1, col2 = st.columns(2)
                    with col1:
                        new_status = st.selectbox("修改状态",
                                                  ["待开始", "进行中", "已完成", "已取消"],
                                                  index=["待开始", "进行中", "已完成", "已取消"].index(
                                                      schedules.loc[
                                                          schedules['id'] == selected_schedule_id, 'status'].values[0]))
                        if st.button("更新状态"):
                            update_schedule(selected_schedule_id, "status", new_status)
                            st.success("状态已更新")
                            st.rerun()

                    with col2:
                        if st.button("删除该日程", type="primary"):
                            delete_schedule(selected_schedule_id)
                            st.warning("日程已删除")
                            st.rerun()
        else:
            st.info("暂无日程安排")


elif page == "教育经历管理":
    st.header("🎓 教育经历管理")

    tab1, tab2 = st.tabs(["添加教育经历", "查看教育经历"])

    with tab1:
        st.subheader("添加教育经历")
        with st.form("education_form"):
            col1, col2 = st.columns(2)
            with col1:
                institution = st.text_input("学校/机构名称 *")
                degree = st.selectbox("学位", ["高中", "专科", "学士", "硕士", "博士", "其他"])
                major = st.text_input("专业")
                start_date = st.text_input("开始日期", placeholder="YYYY-MM-DD")

            with col2:
                end_date = st.text_input("结束日期", placeholder="YYYY-MM-DD")
                gpa = st.number_input("GPA", min_value=0.0, max_value=4.0, value=3.0, step=0.1)
                achievements = st.text_area("成就/荣誉")

            if st.form_submit_button("添加教育经历"):
                if institution:
                    insert_education((1, institution, degree, major, start_date, end_date, gpa, achievements))
                    st.success("教育经历添加成功！")
                else:
                    st.warning("请输入学校/机构名称")

    with tab2:
        st.subheader("教育经历列表")
        education_list = get_education()
        if not education_list.empty:
            st.dataframe(education_list, use_container_width=True)

            st.subheader("教育经历管理")
            education_ids = education_list["id"].tolist()
            if education_ids:
                selected_edu_id = st.selectbox("选择教育经历ID", education_ids)
                if selected_edu_id:
                    if st.button("删除该教育经历", type="primary"):
                        delete_education(selected_edu_id)
                        st.warning("教育经历已删除")
                        st.rerun()
        else:
            st.info("暂无教育经历记录")

elif page == "系统概览":
    st.header("📊 系统概览")


    col1, col2, col3, col4 = st.columns(4)

    with col1:
        records_count = pd.read_sql_query("SELECT COUNT(*) as count FROM records", conn).iloc[0]['count']
        st.metric("总记录数", records_count)

    with col2:
        honors_count = pd.read_sql_query("SELECT COUNT(*) as count FROM honors", conn).iloc[0]['count']
        st.metric("荣誉数量", honors_count)

    with col3:
        schedules_count = pd.read_sql_query("SELECT COUNT(*) as count FROM schedules", conn).iloc[0]['count']
        st.metric("日程数量", schedules_count)

    with col4:
        education_count = pd.read_sql_query("SELECT COUNT(*) as count FROM education", conn).iloc[0]['count']
        st.metric("教育经历", education_count)


    st.subheader("数据分布")

    col1, col2 = st.columns(2)

    with col1:

        honors_priority = pd.read_sql_query(
            "SELECT priority, COUNT(*) as count FROM honors GROUP BY priority", conn)
        if not honors_priority.empty:
            st.write("**荣誉优先级分布**")
            fig, ax = plt.subplots()
            ax.pie(honors_priority['count'], labels=honors_priority['priority'], autopct='%1.1f%%')
            st.pyplot(fig)

    with col2:

        schedules_status = pd.read_sql_query(
            "SELECT status, COUNT(*) as count FROM schedules GROUP BY status", conn)
        if not schedules_status.empty:
            st.write("**日程状态分布**")
            fig, ax = plt.subplots()
            ax.pie(schedules_status['count'], labels=schedules_status['status'], autopct='%1.1f%%')
            st.pyplot(fig)

    st.subheader("数据库表关系")

    st.markdown("""
    **数据库表关系说明：**

    - **personal_info** (个人基本信息表) - 核心表，存储用户基本信息
    - **records** (通用记录表) - 通过 person_id 关联到 personal_info
    - **honors** (荣誉信息表) - 通过 person_id 关联到 personal_info，通过 category_id 关联到 categories
    - **schedules** (日程信息表) - 通过 person_id 关联到 personal_info
    - **education** (教育经历表) - 通过 person_id 关联到 personal_info
    - **categories** (分类表) - 为荣誉信息提供分类支持

    **关系类型：**
    - 一对一：personal_info 与用户基本身份信息
    - 一对多：personal_info 与 honors/schedules/education/records
    - 多对一：honors 与 categories
    """)

    st.subheader("最近活动")

    col1, col2 = st.columns(2)

    with col1:

        recent_records = pd.read_sql_query(
            "SELECT title, created_at FROM records ORDER BY created_at DESC LIMIT 5", conn)
        st.write("**最近记录:**")
        for _, record in recent_records.iterrows():
            st.write(f"• {record['title']} ({record['created_at'][:10]})")

    with col2:

        upcoming_schedules = pd.read_sql_query(
            "SELECT title, start_time FROM schedules WHERE start_time >= date('now') ORDER BY start_time LIMIT 5", conn)
        st.write("**即将到来的日程:**")
        for _, schedule in upcoming_schedules.iterrows():
            st.write(f"• {schedule['title']} - {schedule['start_time'][:16]}")


st.sidebar.markdown("---")
st.sidebar.subheader("系统信息")
st.sidebar.info(f"""
数据库类型: SQLite
表数量: 6
最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""")

