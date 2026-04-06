# 部署文档

## 1. 文档说明
本项目是一个基于 **FastAPI + Gradio + LangChain + FAISS** 的食谱 RAG 对话系统。本文档用来说明：
- 项目依赖哪些环境与第三方库
- 数据和配置文件应该放在哪里
- 后端和前端如何启动
- 如何验证项目是否成功运行
- 常见问题如何排查

---

## 2. 项目功能概述
本项目实现了一个食谱问答 RAG 系统，主要包含以下功能：
- 使用 Markdown 食谱文档构建知识库
- 使用 `MarkdownHeaderTextSplitter` 对文档进行结构化切分
- 使用 `HuggingFaceEmbeddings + FAISS` 构建向量索引
- 使用 `BM25 + 向量检索 + RRF` 做混合检索
- 使用大语言模型生成回答
- 使用 SQLite 保存多轮会话、短期记忆、长期记忆和反思
- 通过 FastAPI 提供后端接口，通过 Gradio 提供可视化前端

---

## 3. 运行环境
建议环境如下：
- 操作系统：Windows 10/11
- Python：3.10 或 3.11
- 包管理工具：conda 或 venv

示例：

```bash
conda create -n recipe-rag python=3.10 -y
conda activate recipe-rag
pip install -r requirements.txt
```

---

## 4. 目录说明
项目核心文件包括：
- `app/main.py`：FastAPI 后端入口，提供健康检查、聊天、会话历史和记忆等接口
- `app/core/config.py`：项目配置，集中管理数据路径、索引路径、数据库路径、模型名称和服务端口
- `app/core/dependencies.py`：服务初始化，在应用启动时统一创建知识库、会话存储、记忆、反思和对话服务实例

### 4.1 services 目录
- `app/services/kb_service.py`：知识库服务，负责串联数据加载、切分、索引构建、索引加载和检索模块
- `app/services/chat_service.py`：对话主流程服务，负责路由、查询重写、检索、记忆召回、回答生成、长期记忆抽取和反思写回
- `app/services/decision_service.py`：决策服务，根据用户问题类型、上下文和最近反思结果，决定是否改写查询以及检索条数等策略
- `app/services/memory_service.py`：记忆服务，负责构建短期记忆、召回长期记忆，并从历史对话中提取适合长期保存的信息
- `app/services/reflection_service.py`：反思服务，对当前一轮问答的检索与回答效果做简短评估，供下一轮决策参考
- `app/services/session_store.py`：会话存储服务，基于 SQLite 持久化保存会话历史、短期记忆、长期记忆和反思内容

### 4.2 rag_modules 目录
- `app/rag_modules/data_preparation.py`：数据加载与切分，读取 Markdown 食谱文件并补充分类、难度等元数据
- `app/rag_modules/index_construction.py`：向量索引构建与加载，使用 HuggingFace Embedding 和 FAISS 建立本地索引
- `app/rag_modules/retrieval_optimization.py`：检索优化模块，结合向量检索、BM25 和 RRF 重排实现混合检索
- `app/rag_modules/generation_integration.py`：生成集成模块，负责查询路由、查询改写以及最终回答生成

### 4.3 其他文件
- `gradio_app.py`：前端界面，向后端发送聊天请求并展示回答、检索调试信息、记忆和反思
---

## 5. 配置说明
项目当前默认配置写在 `config.py` 中，包括：
- `data_path`：知识库 Markdown 数据路径
- `index_save_path`：FAISS 索引保存路径
- `sqlite_path`：SQLite 数据库路径
- `embedding_model`：嵌入模型名称
- `llm_model`：大语言模型名称
- `host` 和 `port`：后端服务地址

### 当前需要注意的问题
当前代码中路径是写死在 Windows 的 `D:/all-in-rag-app/...` 下的。如果换一台电脑直接运行，通常会因为路径不存在而失败。

因此提交前建议至少做以下两种处理中的一种：

### 方案 A：直接修改 `config.py`
将下面这些路径改成你提交包中的相对路径或本机路径：
- `data_path`
- `index_save_path`
- `sqlite_path`

例如可改成：
- `./app/data/C8/cook`
- `./vector_index`
- `./app.db`

### 方案 B：使用 `.env` 文件
项目配置类支持从 `.env` 文件加载配置，因此可以在项目根目录创建 `.env` 文件，并提供对应配置。

示例：

```env
DEEPSEEK_API_KEY=你的API密钥
DATA_PATH=./app/data/C8/cook
INDEX_SAVE_PATH=./vector_index
SQLITE_PATH=./app.db
HOST=0.0.0.0
PORT=8000
```

说明：
- `DEEPSEEK_API_KEY` 是必须的，否则大模型初始化会失败。
- 若使用 `.env`，建议仍检查路径是否与项目目录一致。

---

## 6. 数据准备
后端启动时会自动初始化知识库，其流程为：
1. 从 `data_path` 递归读取所有 Markdown 文件
2. 对每个文档补充分类、菜名、难度等元数据
3. 使用 Markdown 标题进行结构化切分
4. 如果本地已有 FAISS 索引，则直接加载
5. 若本地没有索引，则重新构建并保存

因此，运行前应确保：
- `data_path` 路径存在
- 目录内包含 `.md` 食谱文件
- 程序对索引目录和 SQLite 路径有读写权限

---

## 7. 后端启动
进入项目根目录后，启动 FastAPI 后端：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

如果你希望局域网内访问，也可以改为：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端启动成功后，可以访问：
- 健康检查：`http://127.0.0.1:8000/health`
- 知识库统计：`http://127.0.0.1:8000/kb/stats`

---

## 8. 前端启动
本项目前端使用 Gradio，并默认请求本地后端接口 `http://127.0.0.1:8000`。

启动方式：

```bash
python gradio_app.py
```

默认会在浏览器中打开：
- `http://127.0.0.1:7860`

使用时需保证：
- FastAPI 后端已经先启动
- `gradio_app.py` 中的 `BACKEND` 地址与后端地址一致

---

## 9. 接口说明
后端主要接口如下：

### 9.1 健康检查
```http
GET /health
```
返回：
```json
{"status": "ok"}
```

### 9.2 知识库统计
```http
GET /kb/stats
```
返回知识库中文档数量、分类统计、难度统计等信息。

### 9.3 聊天接口
```http
POST /chat
```
请求示例：
```json
{
  "session_id": "test-session",
  "message": "推荐一个简单的早餐",
  "stream": false
}
```

### 9.4 会话历史
```http
GET /sessions/{session_id}/history
```

### 9.5 会话记忆
```http
GET /sessions/{session_id}/memory
```

---

## 10. 验证是否部署成功
可以按如下顺序验证：

1. 启动后端，访问 `/health`，确认返回 `{"status": "ok"}`
2. 访问 `/kb/stats`，确认知识库统计正常返回
3. 启动 Gradio 前端
4. 在聊天框输入问题，例如：
   - `推荐一个简单的素菜`
   - `西红柿炒蛋怎么做`
5. 检查页面中是否能显示：
   - 回答内容
   - 检索调试信息
   - 会话记忆与反思信息

---

## 11. 常见问题

### 11.1 API Key 未配置
报错表现：
- 后端启动时报错，提示缺少 `DEEPSEEK_API_KEY`

解决方法：
- 在系统环境变量中设置 `DEEPSEEK_API_KEY`
- 或在项目根目录 `.env` 文件中写入该变量

### 11.2 路径不存在
报错表现：
- 数据目录找不到
- SQLite 文件无法创建
- FAISS 索引目录无法加载或保存

解决方法：
- 检查 `data_path`、`index_save_path`、`sqlite_path`
- 建议改为相对路径，避免绑定个人电脑磁盘位置

### 11.3 前端无法连接后端
报错表现：
- Gradio 页面提交后无响应
- 请求报连接错误

解决方法：
- 确认 FastAPI 已先启动
- 确认 `gradio_app.py` 中的 `BACKEND` 地址与后端实际地址一致

### 11.4 首次启动较慢
原因：
- 首次运行时需要加载嵌入模型，并可能重新构建 FAISS 索引

这是正常现象，后续如果索引已保存，则再次启动会更快。
