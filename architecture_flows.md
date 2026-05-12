# Architecture Flow Diagrams

## Diagram 1: LABTAINER Flow

```mermaid
flowchart TB

    subgraph Client["User Layer"]
        B["Student Browser"]
    end

    subgraph Nginx["API Gateway & Security Layer"]
        direction TB

        N["Nginx request-based routing"]

        ROUTE["/vul-lab"]
    end

    subgraph EXEC["Management & Execution Layer / Lab Execution Module"]
        direction TB

        subgraph FE["Flask Backend"]
            direction TB

            F["Flask App"]

            CLONE["Clone and Replace Lab Parameters<br/>(ENV, randomKey, ...)"]

            USER["Create Linux User<br/>+ Reserve Dynamic Ports"]

            CMD["rebuild lab_name"]
        end

        subgraph LT["Labtainers Framework"]
            direction TB

            REBUILD["rebuild.py"]

            STOP["StopLab()<br/>docker stop/rm"]

            CHECK["CheckBuild()<br/>Check image changes"]

            BUILD["buildImage.sh<br/>Rebuild Docker images"]

            START["DoStart()<br/>Read start.config<br/>Create networks<br/>Start containers<br/>Parameterize"]
        end

        subgraph CT["Containers (Local Runtime)"]
            direction TB

            APP["Lab Service Container<br/>(WebApp or Client Shell)"]

            DB["Database Container"]

            SERVER["Server Container"]
        end
    end

    B -->|"1. Request Lab"| N

    N -->|"2. Proxy Request"| F

    F -->|"3. Clone & Inject Parameters"| CLONE

    F -->|"4. Create User & Allocate Ports"| USER

    F -->|"5. Execute rebuild lab"| CMD

    CMD -->|"6. rebuild {lab_name}"| REBUILD

    REBUILD -->|"7. Stop old containers"| STOP

    REBUILD -->|"8. Check image freshness"| CHECK

    REBUILD -->|"9. Rebuild if needed"| BUILD

    REBUILD -->|"10. Start lab containers"| START

    START -->|"11. Run locally"| APP

    START -->|"11. Run locally"| DB

    START -->|"11. Run locally"| SERVER

    B -->|"12. Access /vul-lab/... "| N

    ROUTE -->|"13. Proxy to"| APP
```

## Diagram 2: CUSTOM Flow

```mermaid
flowchart TB

    subgraph Client["User Layer"]
        B["Student Browser"]
    end

    subgraph Nginx["API Gateway & Security Layer"]
        direction TB

        N["Nginx request-based routing"]

        ROUTE["/vul-lab"]
    end

    subgraph ARCH["Management & Execution Layer"]

        direction TB

        subgraph MGMT_WRAP["Management Module"]

            direction TB

            subgraph FE["Flask Backend"]
                direction TB

                F["Flask App"]

                PORTS["Reserve Dynamic Ports<br/>(web, client, db)"]

                INJECT["Inject Parameters<br/>(ENV, RANDOM_KEY, USER_EMAIL, ...)"]

                CMD["TARGET_NODE=XX RANDOM_KEY=YY<br/>docker stack deploy"]
            end

            subgraph SM["Swarm Manager"]
                direction TB

                DEPLOY["docker stack deploy<br/>-c docker-compose.yml<br/>lab_{id}_{user}"]

                COMPOSE["Read docker-compose.yml<br/>→ Define services (web, db, client)<br/>→ Each has image, env vars, ports,<br/>placement constraints"]

                PULL["Pull images from Docker Hub<br/>(if not cached on worker)"]
            end
        end

        subgraph EXEC_WRAP["Lab Execution Module"]

            direction TB

            subgraph WN["Swarm Worker Nodes (Remote Runtime)"]
                direction TB

                RUN["Docker Swarm creates containers<br/>from pulled images"]

                ENTRY["Each container runs<br/>Dockerfile ENTRYPOINT"]

                INJECT_FLAG["Entrypoint reads RANDOM_KEY, USER_EMAIL, ENV, ...<br/>→ Hashes the FLAG<br/>→ Injects into target"]

                INJECT_DB["Database Container<br/>INSERT flag into table"]

                INJECT_FS["File Server Container<br/>Write flag to file"]

                INJECT_WEB["Web App Container<br/>Inject flag into config/env"]

                APP["Lab Service Container<br/>(WebApp or Client Shell)"]

                DB["Database Container"]

                SERVER["Server Container"]
            end
        end
    end

    B -->|"1. Request Lab"| N

    N -->|"2. Proxy Request (CUSTOM)"| F

    F -->|"3. Allocate Ports"| PORTS

    F -->|"4. Inject Parameters"| INJECT

    F -->|"5. Execute stack deploy"| CMD

    CMD -->|"6. stack deploy {name}"| DEPLOY

    DEPLOY -->|"7. Parse compose<br/>→ define topology"| COMPOSE

    COMPOSE -->|"8. Schedule services<br/>to worker nodes"| PULL

    PULL -->|"9. Pull images"| RUN

    RUN -->|"10. Create containers"| ENTRY

    ENTRY -->|"11. Execute ENTRYPOINT"| INJECT_FLAG

    INJECT_FLAG -->|"Option A"| INJECT_DB

    INJECT_FLAG -->|"Option B"| INJECT_FS

    INJECT_FLAG -->|"Option C"| INJECT_WEB

    INJECT_DB -->|"12. Flag in DB"| DB

    INJECT_FS -->|"12. Flag on disk"| SERVER

    INJECT_WEB -->|"12. Flag in config"| APP

    B -->|"13. Access /vul-lab/... "| N

    ROUTE -->|"14. Proxy to"| APP
```

## Core Differences

| Aspect | LABTAINER | CUSTOM |
|---|---|---|
| **Orchestration** | Labtainers framework (`rebuild`) | Docker Swarm (`stack deploy`) |
| **Lab folder** | Cloned per-student | Shared template folder |
| **Container host** | Same machine as Flask | Remote Swarm worker node |
| **Terminal** | TTYD inside container (direct) | SSH → docker exec |
| **User isolation** | Linux user + `sg` group switch | Docker stack naming |
| **Image lifecycle** | Managed by rebuild.py | Managed by Swarm |
