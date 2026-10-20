"""Research V2 Streamlit application: CodexDB-based SQL-only baseline.

Run from repository root:
    streamlit run CodexDB/src/codexdb/gui_v2.py
"""
import json
import os
from pathlib import Path
import sys

import openai
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from codexdb.catalog import DbCatalog
from codexdb.v2_sql_pipeline import run_sql_only

DATA_DIR = Path(__file__).resolve().parents[2] / 'tourism'
EXAMPLES_PATH = DATA_DIR / 'fewshot_examples.json'

st.set_page_config(page_title='林芝旅游 Text-to-SQL · V2', layout='wide')
st.title('林芝智慧旅游问答 · SQL 基线 V2')
st.caption('CodexDB SqlGenerator → SQL validation → CodexDB SqliteEngine → SQLite')
st.info('当前版本是 SQL-only 基线。Python Fallback 与 LLM Critic 尚未接入，结果不应视为经过语义验证。')

try:
    catalog = DbCatalog(str(DATA_DIR))
    db_id = st.sidebar.selectbox('数据库', list(catalog.db_ids()))
except (OSError, ValueError, KeyError) as exc:
    st.error('无法读取旅游数据库 Schema，请检查 CodexDB/tourism 目录。')
    st.stop()

db_path = Path(catalog.db_dir(db_id)) / f'{db_id}.sqlite'
if not db_path.is_file():
    st.error(f'找不到预期的 SQLite 数据库：{db_path}')
    st.stop()

with st.sidebar:
    st.subheader('SQL 生成配置')
    model_id = st.text_input('LLM 模型', value='gpt-4o-mini')
    style = st.selectbox('Prompt 策略', ['basic', 'schema', 'fewshot'], index=1)
    temperature = st.slider('Temperature', 0.0, 1.0, 0.0, 0.1)
    max_rows = st.number_input('最多显示行数', 1, 1000, 200)
    examples = []
    count = 0
    if style == 'fewshot':
        try:
            examples = json.loads(EXAMPLES_PATH.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            st.error('Few-shot 示例文件不存在或 JSON 格式有误。')
            st.stop()
        if not examples:
            st.error('没有可用的 Few-shot 示例。')
            st.stop()
        count = st.slider('Few-shot 示例数量', 1, len(examples), min(2, len(examples)))
        st.caption('示例仅作开发种子；正式评测须检查样本是否与测试集重叠。')

schema = catalog.sqlite_schema(db_id)
with st.expander('当前 Schema（CodexDB DbCatalog 从真实 SQLite 读取）'):
    for i, table in enumerate(schema['table_names_original']):
        columns = [col[1] for col in schema['column_names_original'] if col[0] == i]
        st.code(f'{table}({", ".join(columns)})')

question = st.text_input('请输入中文旅游问题', placeholder='林芝评分最高的五个景点有哪些？')
if st.button('生成并执行 SQL', type='primary'):
    if not question.strip():
        st.warning('请输入问题。')
        st.stop()
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        st.error('缺少 OPENAI_API_KEY 环境变量；不会尝试调用模型。')
        st.stop()
    openai.api_key = key

    try:
        with st.spinner('正在生成并执行只读 SQLite 查询...'):
            answer = run_sql_only(
                catalog, db_id, question, model_id=model_id,
                prompt_style=style, examples=examples, nr_samples=count,
                temperature=temperature, max_rows=int(max_rows),
            )
    except (ValueError, KeyError) as exc:
        st.error(f'配置或提示错误：{exc}')
        st.stop()
    except Exception:
        st.error('模型调用或处理失败，请检查本机日志及 API 配置。')
        st.stop()

    st.subheader('生成的 SQL')
    st.code(answer['sql'] or '(没有生成 SQL)', language='sql')
    if answer['ok']:
        st.subheader('查询结果')
        st.dataframe(answer['result'], use_container_width=True)
        if answer['execution'].get('truncated'):
            st.warning('查询结果已截断；仅显示前若干行。')
    else:
        st.error(
            '查询未成功：' +
            answer['execution'].get('error_type', 'UnknownError')
        )
        if answer['execution'].get('error'):
            st.caption(answer['execution']['error'])
    with st.expander('生成与执行记录'):
        st.json({
            'model_id': answer['model_id'],
            'prompt_style': answer['prompt_style'],
            'nr_samples': answer['nr_samples'],
            'elapsed_s': answer['elapsed_s'],
            'generation': answer['generation'],
            'execution': answer['execution'],
        })
