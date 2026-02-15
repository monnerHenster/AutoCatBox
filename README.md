# AutoCatBox 加载项

### 关于

本仓库为 Home Assistant 加载项合集，面向猫砂盆/宠物相关自动化及涂鸦设备联动场景。

### 安装方法

[![添加仓库到 Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FmonnerHenster%2FAutoCatBox)

或在 **设置 → 加载项 → 加载项商店 → 仓库** 中添加：

```
https://github.com/monnerHenster/AutoCatBox
```

添加后刷新页面，即可在商店中看到本仓库的加载项并安装。

### 加载项列表

✓ [追觅涂鸦触发](dreame_tuya_trigger/)  

订阅涂鸦云消息（中国区 Pulsar），当设备上报 **code=excretion_time_day** 时自动调用 Home Assistant 中的追觅划区清扫服务，实现猫砂盆上报后自动清扫指定区域。

### 维护者提交到 GitHub（重要：仓库根目录必须直接是这些文件）

HA 只有在**仓库根目录**看到 `repository.yaml` 才会识别为有效加载项仓库。根目录必须是：

- `repository.yaml`
- `README.md`
- `dreame_tuya_trigger/`（文件夹）

**正确做法一：在 AutoCatBox 目录内初始化并推送（推荐）**

```bash
cd d:\Tools\python\RemoteServer\BGP\AutoCatBox
git init
git remote add origin https://github.com/monnerHenster/AutoCatBox.git
git add .
git commit -m "Add AutoCatBox add-on repo: 追觅涂鸦触发"
git branch -M main
git push -u origin main
```

**正确做法二：已 clone 过仓库时**

```bash
git clone https://github.com/monnerHenster/AutoCatBox.git
cd AutoCatBox
# 把本机 AutoCatBox 里的 所有文件（含 repository.yaml、README.md、dreame_tuya_trigger）复制进来，覆盖
git add .
git commit -m "Add 追觅涂鸦触发 add-on"
git push
```

**自检**：在浏览器打开 https://github.com/monnerHenster/AutoCatBox ，第一页应直接看到 `repository.yaml`、`README.md`、`dreame_tuya_trigger`，而不是再点进一个「AutoCatBox」子文件夹才看到。若是子文件夹，说明推送错了层级，需在包含 `repository.yaml` 的那一层做 `git init` 再推送。

---

[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FmonnerHenster%2FAutoCatBox
