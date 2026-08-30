## 今日完成：

- ##### 全局异常处理配置

  - 因为昨天和ds与glm的对话，我决定深化一下我的工程化能力。jwt和pydantic的config非空校验已经能被我自然融入MVP，抬高MVP质量，后续我想把更多细节锻炼为我的下意识操作，继续抬高MVP质量。

  - 所以今天，我选择封装异常处理，让每个路由不再手动HTTPSException。

    - 将异常处理器放置于单独模块exceptions.py，轻量，方便调用。

    - 创建AppError类，继承Exception类，设置status_code与default_detail默认值（500），同时super()_____init____(self.detail)从父类继承detail

    - 将400，403，404等常见异常创建为类，继承AppError

    - 写返回JSON的异步函数

    - 写注册函数，包含add_exception_handler(错误类，返回值)注册异常处理器和unhandled_handler()未处理异常兜底处理器

    - 在main调用注册函数实现全局注册。

    - 将各个异常处理更换为自定义错误类型。500则使用昨天学的logger计入日志

- ##### ruff + pre-commit配套代码质量门禁打造

  - 据我常用的hermes与dsh所言，ruff工具在uv sync时就已经配置在dev依赖中，只是我一直未使用。今天搭配pre-commit可以实现git-commit时自动审查代码。

    - 写.pre-commit-config.yaml的yaml文件

    - pre-commit install将hook注册进.git。由于hook会在git-commit前自动运行，所以必须注册进去。

      - 首次使用远程hook时，需要配置对应网络环境，例如连接github需要使用代理。第一次拉取成功后，本地保有缓存，下次本地可以直接使用。

    - pre-commit run --all-files实现全文件格式与规范审查。中途出现的failed可能只是提示开发者需要再次git add文件

    - 再跑一遍pre-commit run --all-files，测试全pass，放行。交由CI再次审查

      - 当ruff版本锁死 + 本地强制运行时，由于本地与CI规则相同，不会出现两套规则，CI假绿的情况出现概率更小。





## 笔者有感：

        感觉经过今天的学习，我的工程化能力又深化了一些。先前第一个项目的jwt + pydantic校验config的“加分项”已经成为基础，今天以后，这些工程化代码要加上注册全局Exception处理器了，逐渐把这些事情转化为我做项目的细节，能够提高我项目MVP的质量。后续还有调logging库记录日志，以及ruff + pre-commit代码格式审查，redis做ip限流等等。总之以后的标准会越来越高。

        还有，我发现uv真的好用，我现在都不想管travel的依赖情况了，太乱了。

        我或许可以把这些能力整理成工程化能力checklist。哎，时间还长，我有足够的时间深化项目。



### 2026.8.29
