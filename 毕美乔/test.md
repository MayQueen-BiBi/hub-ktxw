flowchart TD
  subgraph IN[外部输入 / 执行参数]
    P1["生产入口\nA: gansu_scripts/daily_strategy_write_mysql_new.py\n__main__: forecast_date=当日，info_date=forecast_date+1\n当前源码另硬编码 2026-07-19\n24 小时、5 段"]
    B1["交易单元回测入口\nA: gansu_scripts/daily_different_group_strategy.py\nrun_file(date, 国投, output_base)\n出清: date；结算: date-3"]
    B2["策略对比入口\nA: gansu_scripts/daily_strategy_compare.py\n__main__: info_date=当前日-1\n当前源码另硬编码 2026-07-19"]
  end

  subgraph CDEP[C 依赖：数据 / 数据库接口]
    C1["C: lambda/auto_data/engine.py\nDataEngine.get(name,date,query_datetime,...)\n按 env DataEngine 映射检查数据可用时点"]
    C2["C: lambda/database/utils.py\nPriceForecastFunc / StrategyFunc\n预测读取、策略五段数据读写、损益写入"]
    C3["配置：lambda/configs/.data_engine_gansu_env.yaml\nDataEngine -> MysqlHelper 映射\n具体数据源与凭据：待确认"]
  end

  subgraph BDEP[B 依赖：策略 / 交易对象]
    M["B: ahead_strategy/make_gansu_ahead_strategy.py\nModel.get_strategy(ga, query_datetime, pred_date)\n输出：24 个 AheadStrategy"]
    GS["B: ahead_strategy/gansu_ahead_strategies.py\n统一结算点动量 / 茴香 / 茴香-河西 / 豌豆等\n读取历史价格、实时价、日前价、日前价格预测"]
    GA["B: trading/gansu_ahead.py\nGanSuAhead / AheadStrategy\n策略曲线与 96 点中标系数计算"]
  end

  P1 -->|check_gansu_price_pred\nforecast_date 与 info_date 相差 1 天| C2
  P1 -->|构造 GanSuAhead：mode=predict；96 点占位量/价| GA
  P1 -->|Model('predict', params)| M --> GS
  GS -->|DataEngine / PriceForecastFunc 读取| C1
  GS --> C2
  M -->|24小时 × 5报价+6系数| POUT["策略生产结果\nA: run\n价格四舍五入至 10，限制 [40, GanSuConst.price_max]\n系数断言：通常上限 1.2；plus 为 1.5"]
  POUT -->|ahead_step_coef_to_mysql| C2
  POUT -->|ExcelWriter| F1["共享文件 Excel\nALGO_SHARE_DIR/甘肃/D-1策略/{info_date}机器策略.xlsx"]
  POUT -->|requests.post，post_env 非空| API["兰台日前策略 HTTP 接口\n生产 __main__ 传 product\n网络交互：未执行"]

  B2 -->|策略五段记录；默认 forecast_date=info_date-1| C2
  B2 -->|日前/实时价格；query_datetime=date+2| C1
  C1 --> CMP["daily_strategy_compare\n96 点：coef=(五段策略在日前价的交点)\nres=(coef-1)*(日前价-实时价)"]
  CMP -->|insert_strategy_profit / hourly| C2
  CMP --> F2["PNG / Excel 对比输出\nBASE_DIR 或 ALGO_SHARE_DIR 共享目录"]

  B1 -->|GanSuAhead(update=False), query_datetime=2040-01-01 01| GA
  B1 -->|策略五段记录、价格、电量、节点价| C1
  B1 --> C2
  GA --> UNIT["strategy_compare\ndeclare_quantity=理论中标系数*预测电量\nprofit=dot(日前-实时, 申报/策略电量-实际电量)/实际总量"]
  UNIT --> F3["两个 Excel\n策略对比、策略对比计算中间数据"]
