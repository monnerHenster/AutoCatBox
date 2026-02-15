# 追觅涂鸦触发 - HA Add-on

涂鸦消息订阅（中国区），当设备上报 **code=excretion_time_day** 时自动调用追觅划区清扫。

## 与 Windows 测试目录的关系

| 目录 | 用途 |
|------|------|
| **tuya_mq_consumer/** | 在 **Windows 上直接运行**：`python consumer.py`，用本机 config.py / 环境变量，可随时改代码测试。 |
| **ha_addon/dreame_tuya_trigger/** | **HA add-on**：独立一份代码，用于打包后通过 SSH 或仓库装到 HA，配置在 HA 界面里填。 |

两处逻辑一致（都是 excretion_time_day 触发追觅），互不影响。

## 安装到 HA（含西瓜定制版）

### 方式一：本地 add-on（SSH 上传）

1. 在 HA 主机上创建 add-on 目录（以 192.168.10.152 为例）：
   ```bash
   ssh root@192.168.10.152
   # 西瓜/HA OS 常见路径（按你实际调整）：
   mkdir -p /addons/dreame_tuya_trigger
   # 或若 add-on 在 /config/addons 下：
   # mkdir -p /config/addons/dreame_tuya_trigger
   ```

2. 在 **本机** 打包 add-on 并传到 HA（压缩包内直接是 dreame_tuya_trigger 目录）：
   ```bash
   cd d:\Tools\python\RemoteServer\BGP\ha_addon
   tar -cvf ../dreame_tuya_trigger.tar dreame_tuya_trigger/
   scp ../dreame_tuya_trigger.tar root@192.168.10.152:/addons/
   ```

3. 在 HA 上解压并确认结构：
   ```bash
   ssh root@192.168.10.152
   cd /addons
   tar -xvf dreame_tuya_trigger.tar
   ls dreame_tuya_trigger/   # 应有 config.yaml Dockerfile run.sh app/
   ```

4. 在 HA 界面：**设置 → 加载项 → 加载项商店**，若支持「从本地加载」则添加 `/addons`（或你实际路径）；或把 `dreame_tuya_trigger` 放到你已有的本地 add-on 仓库目录下，再在「仓库」里添加该本地路径/仓库。

5. 安装「追觅涂鸦触发」，在配置里填写：
   - **tuya_access_id** / **tuya_access_key**
   - **ha_url**：add-on 内访问 HA 一般用 `http://supervisor/core`（西瓜版若不同可改为 HA 实际地址）
   - **ha_token**：HA 长期访问令牌
   - **vacuum_entity_id** / **segments**：追觅实体与划区

### 方式二：自定义仓库

若 HA 支持从 Git/URL 安装 add-on：

1. 把 `ha_addon/dreame_tuya_trigger` 放到一个 Git 仓库的根或某目录下。
2. 在仓库根添加 `repository.yaml`（若该仓库只放这一个 add-on，很多系统允许直接指向 add-on 所在目录）。
3. 在 HA「加载项 → 仓库」里添加该仓库 URL。

## 配置说明

| 选项 | 说明 |
|------|------|
| tuya_access_id | 涂鸦云 Access ID |
| tuya_access_key | 涂鸦云 Access Secret |
| tuya_mq_env | `event-test` 或 `event` |
| ha_url | HA API 根地址，add-on 内通常为 `http://supervisor/core` |
| ha_token | HA 长期访问令牌 |
| vacuum_entity_id | 追觅吸尘器实体 ID |
| segments | 划区号列表，如 [13] |

触发条件：解密后的涂鸦消息里，**code=excretion_time_day**（在 `bizData.properties[].code` 或 `status[].code` 中出现）即调用 `dreame_vacuum.vacuum_clean_segment`。
