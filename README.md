# 数据看板

你是一个vim插件开发人员, 你需要开发一个vim插件, 可以连接数据库查询数据, 并展示数据

你需要兼容 vim 和 neovim 两个版本

并且支持通过 vim-plug 安装这个插件, 尽量支持多种安装方式

## 核心特性

- **跨平台兼容**: 支持 Windows、Linux、macOS
- **静默操作**: 完全静默执行，无多余消息显示
- **自动刷新**: 支持定时刷新和文件变化检测
- **倒计时显示**: 实时显示距离下次刷新的倒计时
- **连接池管理**: 优化数据库连接性能和资源管理
- **多种安装方式**: 支持 vim-plug、Vundle、Pathogen 等


## 需求细节

### 连接数据库

可以连接数据库查询数据, 根据不同的连接url选择不同的数据库支持以下数据库

url中包含了连接数据库所包含的所有信息, 现在定义url格式如下

MySQL : mysql://username:password@host:port/database_name
PostgreSQL: postgres://username:password@host:port/database_name
SQLite: sqlite:///path/to/database_file.db
Oracle: oracle://username:password@host:port/service_name
Microsoft SQL Server: mssql://username:password@hostname:port/database_name
Redis: redis://username:password@host:port
MongoDB: mongodb://username:password@host:port/database_name
Cassandra: cassandra://username:password@host:port/keyspace_name

### 查询数据

连接数据库后, 每隔一段时查询一次数据库, 每次查询后都关闭连接, 不使用连接池功能

### 展示数据

可以根据

需要支持在终端展示
- 散点图(Scatter Plot)
- 面积图(Area Plot)
- 柱状图(Bar Plot)
- 直方图(Histogram)
- 箱线图(Box Plot)
- 热力图(Heatmap)
- 气泡图(Bubble Chart)
- 表格(Table)
- 饼图(Pie Chart)
- 折线图(Line Plot)

### 配置

需要支持配置文件, 支持配置所有的信息

以下是配置文件是一个yaml文件, 例子如下

```yaml
# 表格图表样例配置
# 功能说明：展示一个简单的数据表格，显示当前时间、随机数据和计算结果
# 适用场景：数据监控、状态展示、简单报表等

# 数据库配置
database:
  # 数据库类型，这里使用SQLite作为示例
  type: sqlite
  # 数据库连接URL，使用内存数据库，无需创建文件
  url: "sqlite:///:memory:"

# 查询配置
query:
  # SQL查询语句，生成模拟数据，无需依赖任何表
  sql: |
    SELECT 
      datetime('now', 'localtime') as current_time,     -- 当前本地时间
      abs(random() % 100) as random_number,             -- 0-99的随机数
      abs(random() % 1000) as sales_amount,             -- 模拟销售金额
      case 
        when abs(random() % 3) = 0 then 'Active'
        when abs(random() % 3) = 1 then 'Pending' 
        else 'Inactive'
      end as status,                                     -- 随机状态
      'User' || (abs(random() % 10) + 1) as username,    -- 模拟用户名
      "{{key1}}" as k1,
      "{{key2}}" as k2

  args:
    - key: key1
      default: value1
    - key: key2
      default: value2

# 显示配置
show:
  type: table                     # 图表类型：表格
  title: "系统状态监控表"         # 表格标题
  interval: 30s                   # 每30秒刷新一次数据

  # 列配置，定义每列的显示名称和格式
  column_list:
    - column: current_time        # 数据库列名
      alias: "当前时间"           # 显示名称
      width: 20                   # 列宽度（字符数）

    - column: random_number
      alias: "随机数"
      width: 10

    - column: sales_amount
      alias: "销售金额"
      width: 12

    - column: status
      alias: "状态"
      width: 10

    - column: username
      alias: "用户名"
      width: 12

    - column: key1
      alias: "k1"
      width: 10

    - column: key2
      alias: "k2"
      width: 10

  # 表格样式配置
  style:
    border: true                  # 是否显示边框
    header_style: bold blue       # 表头样式：粗体蓝色

  show_countdown: true            # 是否显示倒计时
  countdown_format: "下次更新: {time}s"  # 倒计时显示格式
```

## 命令列表

### DashboardStart

可以通过 `:DashboardStart <config file>` 来启动数据看板

打开数据看板, 后会将执行结果保存到临时文件 `/tmp/dashboard/filename.dashboard` 并且用vim打开

并且在间隔时间后会重新执行查询，同时显示倒计时功能

**特性**:
- 自动创建临时文件目录（跨平台兼容）
- 静默执行，无多余消息显示
- 支持倒计时显示，每10秒更新一次
- 自动刷新机制（定时器 + 文件变化检测）

### DashboardRestart

可以通过 `:DashboardRestart` 来重新刷新当前配置文件的执行结果

立即重新执行查询并更新显示，重置倒计时

### DashboardStop

可以通过 `:DashboardStop [config file]` 来停止数据看板

停止指定配置文件的数据看板任务，如果不指定文件则停止当前活动的看板

### DashboardList

可以通过 `:DashboardList` 来列出所有活动的数据看板

显示当前正在运行的所有看板任务及其状态信息

### DashboardStatus

可以通过 `:DashboardStatus` 来查看当前数据看板的状态

显示当前看板的详细状态信息，包括：
- 配置文件路径
- 数据库连接状态
- 下次刷新倒计时
- 查询执行历史

### Dashboard

可以通过 `:Dashboard` 来打开当前目录来选择配置, 并且在左侧显示所有配置文件

选择了一个配置文件相当于执行 `:DashboardStart`

#### 侧边栏支持

对于`:Dashboard`命令打开后需要在左侧添加一个窗口, 而不是在当前窗口打开当前目录

这个侧边栏需要展示在当前目录下所有配置文件

- 对于没打开的配置文件需要展示一个 `▸`
- 对于打开的配置文件需要展示一个 `▾`

对于打开的临时文件变更成 将执行结果保存到临时文件 `/tmp/dashboard/${file_name}.dashboard` 格式,

并且将filetype 设置为 `dashboard`

#### 侧边栏支持的操作

- 支持在侧边栏中选中一个配置文件
- `回车`打开选中的配置文件, 打开后相当于执行 `:DashboardStart` 并且需要将光标移动到到对应的`/tmp/dashboard/${file_name}.dashboard`中
- `t`停止配置文件的刷新, 并且关闭这个配置文件, 相当于执行 `:DashboardStop`
- `r`重新刷新配置文件的执行结果相当于执行 `:DashboardRestart`

## 高级特性

### 倒计时功能
- 实时显示距离下次刷新的倒计时
- 每10秒更新一次倒计时显示
- 支持暂停和恢复倒计时

### 自动刷新机制
- **定时器刷新**: 根据配置的间隔时间自动刷新
- **文件变化检测**: 监听临时文件变化，支持外部修改触发刷新
- **双重保障**: 定时器和文件监听同时工作，确保数据及时更新

### 静默操作
- 完全静默执行，无多余的状态消息
- 隐藏命令执行过程中的路径显示
- 移除所有调试和日志输出

### 跨平台兼容
- **Windows**: 支持 `%TEMP%/dashboard/` 临时目录
- **Linux/macOS**: 支持 `/tmp/dashboard/` 临时目录
- **路径处理**: 自动处理不同操作系统的路径分隔符
- **编码支持**: 正确处理中文和特殊字符

