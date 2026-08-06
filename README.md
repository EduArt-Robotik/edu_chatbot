# EDU Chatbot

Local RAG stack based on `ollama` and `chromadb` with ROS2 interface.

## Component Interaction

```mermaid
flowchart TB

%% =========================
%% Offline ingestion
%% =========================

subgraph OFFLINE["Offline: Knowledge Base Build (profile: update)"]
    DOCS["Local Knowledge Base<br/><br/>pdf, txt, md, docx<br/><br/>directory ./knowledge/documents"]
    
    INGEST["chroma-update service"]
    
    EMBED["ollama<br/>nomic-embed-text"]
    
    CHROMA["chroma<br/>Persistent Vector Store<br/><br/>- embeddings<br/>- chunks<br/>- metadata"]

    DOCS --> INGEST
    INGEST --> EMBED
    EMBED --> CHROMA
end


%% =========================
%% Runtime system
%% =========================

ROS["ROS2 Nodes"]

subgraph RUNTIME["Online: Chatbot Runtime (profile: pipeline)"]
   

    CHATBOT["edu-chatbot<br/><br/>ros2 launch edu_chatbot edu_chatbot.launch.py<br/><br/>May be split in a generic service container and a ros bridge container in the future."]

    QEMBED["ollama<br/>nomic-embed-text<br/><br/>Embed user query"]

    SEARCH["Vector Search"]

    LLM["ollama<br/><br/>gemma4 / qwen3.5"]

end


%% =========================
%% Runtime connections
%% =========================

ROS -->|"ROS2 Service Request or<br/>Input Topic"| CHATBOT

CHATBOT -->|"Input Query"| QEMBED

QEMBED -->|"Embedded Input Query"| SEARCH

CHROMA --> SEARCH

SEARCH -->|"Context"| CHATBOT

CHATBOT -->|"Prompt + Context"| LLM

LLM --> CHATBOT

CHATBOT -->|"ROS2 Service Response or<br/>Output Topic"| ROS

```

## Services

Core services:

- `ollama`: local model runtime for generation and embeddings; persistent model cache in `./ollama/models`.
- `chroma`: local vector database for document chunks and embeddings; persistent data in `./chroma/db`.

Profile-based services:

- `edu-chatbot` (profile `pipeline`): main ROS2 chatbot runtime.
- `ollama-update` (profile `update`): pulls the configured model set into Ollama.
- `chroma-update` (profile `update`): updates/rebuilds the knowledge DB.
- `open-webui` (profile `tools`): optional browser UI for manual model/prompt checks.

## Exposed Ports

- `11434:11434` -> Ollama API ([http://localhost:11434](http://localhost:11434))
- `8000:8000` -> Chroma API ([http://localhost:8000](http://localhost:8000))
- `3000:8080` -> Open WebUI ([http://localhost:3000](http://localhost:3000))

Health endpoints:

- [http://localhost:11434/api/version](http://localhost:11434/api/version) (ollama)
- [http://localhost:8000/api/v2/heartbeat](http://localhost:8000/api/v2/heartbeat) (chroma)

## Commands

Base infrastructure only:

```bash
docker compose up -d --build
```

Knowledge/model update:

```bash
docker compose --profile update up --build --abort-on-container-exit
docker compose down --remove-orphans
```

Pipeline runtime:

```bash
docker compose --profile pipeline up -d --build
docker compose stop edu-chatbot
```

Tools:

```bash
docker compose --profile tools up -d
docker compose stop open-webui
```

## Ops

```bash
docker compose ps
docker compose logs -f ollama
docker compose logs -f chroma
docker compose logs -f edu-chatbot
docker compose down --remove-orphans
```