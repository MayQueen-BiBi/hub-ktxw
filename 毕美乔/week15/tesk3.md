# 1 系统架构图

```mermaid
graph TD
    %% 样式定义
    classDef entry fill:#435334,color:#fff,stroke:#333;
    classDef logic fill:#9EB384,color:#000,stroke:#333;
    classDef agent fill:#CEDEBD,color:#000,stroke:#606c38,stroke-dasharray: 5 5;
    classDef tool fill:#FAF1E4,color:#000,stroke:#bc6c25;
    classDef highlight fill:#fbc02d,stroke:#f57f17,stroke-width:2px;

    %% 入口
    M([main 启动]) --> DR[deep_research 核心函数]

    subgraph Workflow [核心执行流]
        direction TB
        DR --> S1[1. 初步检索]
        S1 --> S2[2. DeepResearchAgent <br/>生成 JSON 大纲]
        
        subgraph Section_Loop [3. 逐章循环处理]
            direction TB
            L1[关键词检索 & 网页抓取] --> L2[DraftingAgent <br/>撰写章节初稿]
            L2 --> L3{ReflectionAgent <br/>内容审核}
            L3 --"不满足 (输出子问题)"--> L1
            L3 --"满足"--> L4[保存章节内容]
        end
        
        S2 --> Section_Loop
        Section_Loop --> S5[4. DeepResearchAgent <br/>整合最终报告]
    end

    %% 工具层
    subgraph Infrastructure [基础设施]
        T1[Jina Search / Reader]
    end

    %% 调用关系
    L1 -.-> T1
    S1 -.-> T1

    %% 样式应用
    class M entry;
    class DR,S1,S2,S5,L1,L4 logic;
    class L2,L3 agent;
    class T1 tool;
    class L3 highlight;   
```
